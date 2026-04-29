#include "web_server.h"
#include "esp_camera.h"
#include "camera_handler.h"
#include "config_handler.h"
#include "sd_handler.h"
#include <WebSocketsServer.h>
#include <time.h>
#include "Arduino.h"

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// HTTP server
httpd_handle_t camera_httpd = NULL;

// WebSocket server
#define WEBSOCKET_PORT 81
WebSocketsServer webSocket(WEBSOCKET_PORT);

// Forward declarations
static esp_err_t index_handler(httpd_req_t *req);

static void getResName(int res, char *buf, size_t len) {
    switch(res) {
        case 10: snprintf(buf, len, "UXGA"); break;
        case 9:  snprintf(buf, len, "SXGA"); break;
        case 8:  snprintf(buf, len, "XGA"); break;
        case 7:  snprintf(buf, len, "SVGA"); break;
        case 6:  snprintf(buf, len, "VGA"); break;
        case 5:  snprintf(buf, len, "CIF"); break;
        case 4:  snprintf(buf, len, "QVGA"); break;
        default:  snprintf(buf, len, "Unknown"); break;
    }
}

void webSocketLoop() {
    webSocket.loop();
}

void broadcastConfig() {
    if (!camera_httpd) return;

    char buf[256];
    char resName[16];
    getResName(globalConfig.resolution, resName, sizeof(resName));

    snprintf(buf, sizeof(buf),
        "{\"resolution\":%d,\"rotation\":%d,\"flip\":%d,\"mirror\":%d,\"flash\":%d,\"motion\":%d,\"threshold\":%d,\"resName\":\"%s\"}",
        globalConfig.resolution, globalConfig.rotation,
        globalConfig.flip ? 1 : 0,
        globalConfig.mirror ? 1 : 0,
        globalConfig.flash_enabled ? 1 : 0,
        globalConfig.motion_enabled ? 1 : 0,
        globalConfig.motion_threshold,
        resName
    );

    webSocket.broadcastTXT(buf, strlen(buf));
}

static void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            Serial.printf("[WS] Client %d disconnected\n", num);
            break;

        case WStype_CONNECTED: {
            Serial.printf("[WS] Client %d connected\n", num);
            broadcastConfig();
            break;
        }

        case WStype_TEXT: {
            JsonDocument doc;
            DeserializationError err = deserializeJson(doc, payload);

            if (err) {
                Serial.printf("[WS] JSON parse failed: %s\n", err.c_str());
                break;
            }

            const char *cmd = doc["cmd"];
            if (!cmd) break;

            bool changed = false;

            if (strcmp(cmd, "resolution") == 0) {
                int val = doc["val"] | globalConfig.resolution;
                globalConfig.resolution = constrain(val, 0, 15);
                changed = true;
                Serial.printf("[WS] Resolution -> %d\n", globalConfig.resolution);
            }
            else if (strcmp(cmd, "flip") == 0) {
                if (doc["toggle"] | false) {
                    globalConfig.flip = !globalConfig.flip;
                } else {
                    globalConfig.flip = doc["val"] | globalConfig.flip;
                }
                changed = true;
                Serial.printf("[WS] Flip -> %d\n", globalConfig.flip);
            }
            else if (strcmp(cmd, "mirror") == 0) {
                if (doc["toggle"] | false) {
                    globalConfig.mirror = !globalConfig.mirror;
                } else {
                    globalConfig.mirror = doc["val"] | globalConfig.mirror;
                }
                changed = true;
                Serial.printf("[WS] Mirror -> %d\n", globalConfig.mirror);
            }
            else if (strcmp(cmd, "flash") == 0) {
                bool newState;
                if (doc["toggle"] | false) {
                    newState = !globalConfig.flash_enabled;
                } else {
                    newState = doc["val"] | globalConfig.flash_enabled;
                }
                setFlash(newState);
                globalConfig.flash_enabled = newState;
                changed = true;
                Serial.printf("[WS] Flash -> %d\n", newState);
            }
            else if (strcmp(cmd, "motion") == 0) {
                if (doc["toggle"] | false) {
                    globalConfig.motion_enabled = !globalConfig.motion_enabled;
                } else {
                    globalConfig.motion_enabled = doc["val"] | globalConfig.motion_enabled;
                }
                changed = true;
                Serial.printf("[WS] Motion -> %d\n", globalConfig.motion_enabled);
            }
            else if (strcmp(cmd, "threshold") == 0) {
                int val = doc["val"] | globalConfig.motion_threshold;
                globalConfig.motion_threshold = constrain(val, 1, 50);
                changed = true;
                Serial.printf("[WS] Threshold -> %d\n", globalConfig.motion_threshold);
            }
            else if (strcmp(cmd, "ping") == 0) {
                webSocket.sendTXT(num, "{\"type\":\"pong\"}");
                break;
            }

            if (changed) {
                updateCameraSettings();
                saveConfig();
                broadcastConfig();
            }
            break;
        }

        default:
            break;
    }
}

static esp_err_t index_handler(httpd_req_t *req){
    httpd_resp_set_type(req, "text/html");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store, no-cache, must-revalidate");
    httpd_resp_set_hdr(req, "Pragma", "no-cache");
    String html = "<!DOCTYPE html><html><head><title>ESP32-CAM</title><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='cache-control' content='no-cache'><meta http-equiv='expires' content='0'><meta http-equiv='pragma' content='no-cache'>";
    html += "<style>body{font-family:Arial;text-align:center;margin:10px;background:#1a1a2e;color:#eee}.btn{padding:8px 16px;margin:4px;cursor:pointer;background:#e94560;border:none;border-radius:4px;color:#fff;font-size:14px;min-width:100px}.btn:hover{background:#c73e54}.btn.active{background:#0f3460}.btn-toggle{background:#533483}.btn-toggle.active{background:#e94560}.status{margin:6px;font-size:13px;color:#aaa}</style></head><body>";
    html += "<h1>ESP32-CAM</h1>";

    if (!cameraOK) {
        html += "<h2 style='color:#e94560'>CAMERA ERROR</h2>";
    }

    html += "<img id='stream' src='/stream' style='width:100%;max-width:640px;border:2px solid #16213e;border-radius:8px;'><div class='status' id='wsStatus'>Connecting...</div><br>";
    html += "<div style='margin:15px 0;'>";
    html += "<button class='btn' onclick='setRes(10)'>UXGA</button>";
    html += "<button class='btn' onclick='setRes(9)'>SXGA</button>";
    html += "<button class='btn' onclick='setRes(8)'>XGA</button>";
    html += "<button class='btn' onclick='setRes(7)'>SVGA</button>";
    html += "<button class='btn' onclick='setRes(6)'>VGA</button>";
    html += "<button class='btn' onclick='setRes(5)'>CIF</button>";
    html += "<button class='btn' onclick='setRes(4)'>QVGA</button>";
    html += "<br><br>";
    html += "<button class='btn btn-toggle' id='flipBtn'>Flip</button>";
    html += "<button class='btn btn-toggle' id='mirrorBtn'>Mirror</button><br>";
    html += "<button class='btn btn-toggle' id='flashBtn'>Flash</button>";
    html += "<button class='btn btn-toggle' id='motionBtn'>Motion</button><br>";
    html += "Sensitivity: <input id='threshRange' type='range' min='1' max='50' value='15' style='width:200px;vertical-align:middle'>";
    html += "<span id='threshVal' class='status'>15</span><br>";
    html += "<button class='btn' onclick='doCapture()'>Take Photo</button>";
    html += "</div>";
    html += "<div style='margin-top:10px;font-size:12px;color:#666'>";
    html += "Stream: <a href='/stream' style='color:#e94560'>/stream</a> | ";
    html += "Snap: <a href='/capture' style='color:#e94560'>/capture</a>";
    html += "</div>";

    html += "<script>";
    html += "var ws;";
    html += "function logStatus(msg) { document.getElementById('wsStatus').innerText = msg; }";
    html += "function updateUI(c) {";
    html += "  updateBtn('flipBtn', c.flip);";
    html += "  updateBtn('mirrorBtn', c.mirror);";
    html += "  updateBtn('flashBtn', c.flash);";
    html += "  updateBtn('motionBtn', c.motion);";
    html += "  document.getElementById('threshRange').value = c.threshold;";
    html += "  document.getElementById('threshVal').innerText = c.threshold;";
    html += "}";
    html += "function updateBtn(id, val) { var b=document.getElementById(id); b.classList.toggle('active',!!val); }";
    html += "function sendWS(cmd, val) {";
    html += "  var msg={cmd:cmd};";
    html += "  if(val!==undefined&&typeof val==='object') { for(var k in val) msg[k]=val[k]; } else { msg.val=val; }";
    html += "  if(ws&&ws.readyState===1) ws.send(JSON.stringify(msg));";
    html += "}";
    html += "function setRes(v) { sendWS('resolution', v); }";
    html += "function toggleFlip() { sendWS('flip', {toggle:true}); }";
    html += "function toggleMirror() { sendWS('mirror', {toggle:true}); }";
    html += "function toggleFlash() { sendWS('flash', {toggle:true}); }";
    html += "function toggleMotion() { sendWS('motion', {toggle:true}); }";
    html += "function doCapture() { fetch('/capture').then(()=>{}); }";
    html += "function connectWS() {";
    html += "  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';";
    html += "  ws = new WebSocket(proto + '//' + location.host + ':' + " + String(WEBSOCKET_PORT) + ");";
    html += "  ws.onopen = function(){ logStatus('Connected'); console.log('WS opened'); };";
    html += "  ws.onclose = function(){ logStatus('Disconnected'); setTimeout(connectWS, 3000); };";
    html += "  ws.onerror = function(){ logStatus('WS Error'); ws.close(); };";
    html += "  ws.onmessage = function(e) {";
    html += "    var c = JSON.parse(e.data);";
    html += "    if(c.type === 'pong') { logStatus('Connected'); return; }";
    html += "    updateConfig(c); console.log('WS recv:', c);";
    html += "  };";
    html += "}";
    html += "function updateConfig(c) {";
    html += "  updateUI(c);";
    html += "}";
    html += "document.getElementById('flipBtn').onclick=function(){toggleFlip();};";
    html += "document.getElementById('mirrorBtn').onclick=function(){toggleMirror();};";
    html += "document.getElementById('flashBtn').onclick=function(){toggleFlash();};";
    html += "document.getElementById('motionBtn').onclick=function(){toggleMotion();};";
    html += "document.getElementById('threshRange').oninput=function(){document.getElementById('threshVal').innerText=this.value;setTimeout(function(){sendWS('threshold',parseInt(document.getElementById('threshRange').value))},300);};";
    html += "connectWS();";
    html += "</script></body></html>";
    return httpd_resp_send(req, html.c_str(), html.length());
}

static esp_err_t stream_handler(httpd_req_t *req){
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len = 0;
    uint8_t * _jpg_buf = NULL;
    char * part_buf[64];

    if (!cameraOK) {
        return httpd_resp_send_404(req);
    }

    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if(res != ESP_OK) return res;

    Serial.println("Stream: Started");

    while(true){
        fb = esp_camera_fb_get();
        if (!fb) {
            res = ESP_FAIL;
        } else {
            if(fb->format != PIXFORMAT_JPEG){
                bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
                esp_camera_fb_return(fb);
                fb = NULL;
                if(!jpeg_converted) res = ESP_FAIL;
            } else {
                _jpg_buf_len = fb->len;
                _jpg_buf = fb->buf;
            }
        }
        if(res == ESP_OK){
            size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, _jpg_buf_len);
            res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
        }
        if(res == ESP_OK){
            res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
        }
        if(res == ESP_OK){
            res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
        }
        if(fb){
            esp_camera_fb_return(fb);
            fb = NULL;
            _jpg_buf = NULL;
        } else if(_jpg_buf){
            free(_jpg_buf);
            _jpg_buf = NULL;
        }
        if(res != ESP_OK) break;
    }
    Serial.println("Stream: Stopped");
    return res;
}

static esp_err_t capture_handler(httpd_req_t *req){
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;

    Serial.println("Capture: Taking snapshot...");
    fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Capture: Camera capture failed");
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
    res = httpd_resp_send(req, (const char *)fb->buf, fb->len);

    if (SD_MMC.cardType() == CARD_NONE) {
        Serial.println("Capture: No SD card available");
    } else {
        time_t now = time(nullptr);
        struct tm timeinfo;
        memset(&timeinfo, 0, sizeof(timeinfo));
        localtime_r(&now, &timeinfo);
        char path[64];
        memset(path, 0, sizeof(path));
        if (strftime(path, sizeof(path), "/photo_%Y%m%d_%H%M%S.jpg", &timeinfo) == 0) {
            Serial.println("Capture: strftime failed");
        } else {
            File file = SD_MMC.open(path, FILE_WRITE);
            if (file) {
                file.write(fb->buf, fb->len);
                file.close();
                Serial.printf("Capture: Saved to %s\n", path);
            } else {
                Serial.println("Capture: Failed to save to SD card");
            }
        }
    }

    esp_camera_fb_return(fb);
    Serial.printf("Capture: Sent %u bytes\n", fb->len);
    return res;
}

static esp_err_t control_handler(httpd_req_t *req){
    char*  buf;
    size_t buf_len;
    char var[32] = {0,};
    char val[32] = {0,};

    buf_len = httpd_req_get_url_query_len(req) + 1;
    if (buf_len > 1) {
        buf = (char*)malloc(buf_len);
        if (httpd_req_get_url_query_str(req, buf, buf_len) == ESP_OK) {
            if (httpd_query_key_value(buf, "var", var, sizeof(var)) == ESP_OK &&
                httpd_query_key_value(buf, "val", val, sizeof(val)) == ESP_OK) {
            } else {
                free(buf);
                httpd_resp_send_404(req);
                return ESP_FAIL;
            }
        } else {
            free(buf);
            httpd_resp_send_404(req);
            return ESP_FAIL;
        }
        free(buf);
    } else {
        httpd_resp_send_404(req);
        return ESP_FAIL;
    }

    int val_int = atoi(val);
    bool changed = false;

    if(!strcmp(var, "resolution")) {
        globalConfig.resolution = constrain(val_int, 0, 15);
        changed = true;
        if (globalConfig.resolution != val_int) {
            Serial.printf("Web Interface: Resolution clamped to %d (was %d)\n", globalConfig.resolution, val_int);
        }
        Serial.printf("Web Interface: Resolution changed to %d\n", globalConfig.resolution);
    } else if(!strcmp(var, "flip")) {
        globalConfig.flip = (strcmp(val, "toggle") == 0) ? !globalConfig.flip : (val_int ? true : false);
        changed = true;
        Serial.printf("Web Interface: Flip changed to %s\n", globalConfig.flip ? "ON" : "OFF");
    } else if(!strcmp(var, "mirror")) {
        globalConfig.mirror = (strcmp(val, "toggle") == 0) ? !globalConfig.mirror : (val_int ? true : false);
        changed = true;
        Serial.printf("Web Interface: Mirror changed to %s\n", globalConfig.mirror ? "ON" : "OFF");
    } else if(!strcmp(var, "flash")) {
        bool newState = (strcmp(val, "toggle") == 0) ? !globalConfig.flash_enabled : (val_int ? true : false);
        setFlash(newState);
        globalConfig.flash_enabled = newState;
        changed = true;
        Serial.printf("Web Interface: Flash changed to %s\n", newState ? "ON" : "OFF");
    } else if(!strcmp(var, "motion")) {
        globalConfig.motion_enabled = (strcmp(val, "toggle") == 0) ? !globalConfig.motion_enabled : (val_int ? true : false);
        changed = true;
        Serial.printf("Web Interface: Motion changed to %s\n", globalConfig.motion_enabled ? "ON" : "OFF");
    } else if(!strcmp(var, "threshold")) {
        globalConfig.motion_threshold = constrain(val_int, 1, 50);
        changed = true;
        Serial.printf("Web Interface: Motion Threshold changed to %d\n", globalConfig.motion_threshold);
    }

    if (changed) {
        updateCameraSettings();
        saveConfig();
        broadcastConfig();
    }

    return httpd_resp_send(req, NULL, 0);
}

void startWebServer(){
    // ---- WebSocket server ----
    webSocket.onEvent(webSocketEvent);
    webSocket.begin();
    Serial.printf("WebSocket server on port %d\n", WEBSOCKET_PORT);

    // ---- HTTP server ----
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.stack_size = 8192;
    config.max_open_sockets = 6;

    httpd_uri_t index_uri = { .uri = "/", .method = HTTP_GET, .handler = index_handler, .user_ctx = NULL };
    httpd_uri_t stream_uri = { .uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = NULL };
    httpd_uri_t control_uri = { .uri = "/control", .method = HTTP_GET, .handler = control_handler, .user_ctx = NULL };
    httpd_uri_t capture_uri = { .uri = "/capture", .method = HTTP_GET, .handler = capture_handler, .user_ctx = NULL };

    Serial.println("Starting Web Server on port 80...");
    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &index_uri);
        httpd_register_uri_handler(camera_httpd, &control_uri);
        httpd_register_uri_handler(camera_httpd, &capture_uri);
        httpd_register_uri_handler(camera_httpd, &stream_uri);
        Serial.println("Web Server started successfully!");
    } else {
        Serial.println("Failed to start Web Server!");
    }
}
