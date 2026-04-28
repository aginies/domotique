#include "web_server.h"
#include "esp_camera.h"
#include "camera_handler.h"
#include "config_handler.h"
#include "sd_handler.h"
#include <time.h>
#include "Arduino.h"

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t camera_httpd = NULL;

static esp_err_t index_handler(httpd_req_t *req){
    httpd_resp_set_type(req, "text/html");
    String html = "<html><head><title>ESP32-CAM</title><meta name='viewport' content='width=device-width, initial-scale=1'>";
    html += "<style>body{font-family:Arial;text-align:center;} .btn{padding:10px;margin:5px;cursor:pointer;background:#eee;border:1px solid #ccc;border-radius:4px;min-width:120px;}</style></head><body>";
    html += "<h1>ESP32-CAM Control</h1>";
    
    if (!cameraOK) {
        html += "<h2 style='color:red;'>CAMERA HARDWARE ERROR (Check Ribbon)</h2>";
    }

    html += "<img id='stream' src='/stream' style='width:100%; max-width:640px; border:1px solid #000;'><br><br>";
    html += "<div>";
    html += "Resolution: <select id='resSelect' onchange=\"fetch('/control?var=resolution&val='+this.value).then(() => setTimeout(() => location.reload(), 500))\">";
    
    int resValues[] = {10, 9, 8, 7, 6, 5, 4};
    const char* resNames[] = {"UXGA (1600x1200)", "SXGA (1280x1024)", "XGA (1024x768)", "SVGA (800x600)", "VGA (640x480)", "CIF (400x296)", "QVGA (320x240)"};
    
    for (int i = 0; i < 7; i++) {
        html += "<option value='";
        html += String(resValues[i]);
        html += "'";
        if (globalConfig.resolution == resValues[i]) html += " selected";
        html += ">";
        html += resNames[i];
        html += "</option>";
    }
    html += "</select><br><br>";
    
    html += "<button class='btn' onclick=\"fetch('/control?var=flip&val=toggle').then(() => location.reload())\">Toggle Flip</button>";
    html += "<button class='btn' onclick=\"fetch('/control?var=mirror&val=toggle').then(() => location.reload())\">Toggle Mirror</button><br>";
    html += "<button class='btn' onclick=\"fetch('/control?var=flash&val=toggle')\">Toggle Flash</button>";
    html += "<button class='btn' onclick=\"fetch('/control?var=motion&val=toggle').then(() => location.reload())\">Motion: ";
    html += globalConfig.motion_enabled ? "ON" : "OFF";
    html += "</button><br>";
    html += "Motion Sensitivity: <input type='range' min='1' max='50' value='";
    html += String(globalConfig.motion_threshold);
    html += "' onchange=\"fetch('/control?var=threshold&val='+this.value)\"><br>";
    html += "<button class='btn' onclick=\"fetch('/capture').then(r => alert('Photo saved to SD Card'))\">Take Photo</button>";
    html += "</div>";
    html += "<div style='margin-top:20px; padding:10px; background:#f9f9f9; font-size: 0.9em;'>";
    html += "<b>Direct Links:</b><br>";
    html += "Live Stream: <a href='/stream' id='sl'></a><br>";
    html += "Snapshot: <a href='/capture' id='cl'></a>";
    html += "</div>";
    html += "<script>";
    html += "var url = window.location.origin;";
    html += "document.getElementById('stream').src = url + '/stream';";
    html += "document.getElementById('sl').href = url + '/stream';";
    html += "document.getElementById('sl').innerText = url + '/stream';";
    html += "document.getElementById('cl').href = url + '/capture';";
    html += "document.getElementById('cl').innerText = url + '/capture';";
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
    
    // Save to SD Card
    time_t now = time(nullptr);
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    char path[64];
    strftime(path, sizeof(path), "/photo_%Y%m%d_%H%M%S.jpg", &timeinfo);
    
    File file = SD_MMC.open(path, FILE_WRITE);
    if (file) {
        file.write(fb->buf, fb->len);
        file.close();
        Serial.printf("Capture: Saved to %s\n", path);
    } else {
        Serial.println("Capture: Failed to save to SD card");
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
        globalConfig.resolution = val_int;
        changed = true;
        Serial.printf("Web Interface: Resolution changed to %d\n", val_int);
    } else if(!strcmp(var, "flip")) {
        globalConfig.flip = (strcmp(val, "toggle") == 0) ? !globalConfig.flip : val_int;
        changed = true;
        Serial.printf("Web Interface: Flip changed to %s\n", globalConfig.flip ? "ON" : "OFF");
    } else if(!strcmp(var, "mirror")) {
        globalConfig.mirror = (strcmp(val, "toggle") == 0) ? !globalConfig.mirror : val_int;
        changed = true;
        Serial.printf("Web Interface: Mirror changed to %s\n", globalConfig.mirror ? "ON" : "OFF");
    } else if(!strcmp(var, "flash")) {
        bool newState = (strcmp(val, "toggle") == 0) ? !globalConfig.flash_enabled : val_int;
        setFlash(newState);
        Serial.printf("Web Interface: Flash changed to %s\n", newState ? "ON" : "OFF");
    } else if(!strcmp(var, "motion")) {
        globalConfig.motion_enabled = (strcmp(val, "toggle") == 0) ? !globalConfig.motion_enabled : val_int;
        changed = true;
        Serial.printf("Web Interface: Motion changed to %s\n", globalConfig.motion_enabled ? "ON" : "OFF");
    } else if(!strcmp(var, "threshold")) {
        globalConfig.motion_threshold = val_int;
        changed = true;
        Serial.printf("Web Interface: Motion Threshold changed to %d\n", val_int);
    }

    if (changed) {
        updateCameraSettings();
        saveConfig();
    }

    return httpd_resp_send(req, NULL, 0);
}

void startWebServer(){
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.stack_size = 8192; // Increase stack for camera operations
    config.max_open_sockets = 5;

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
