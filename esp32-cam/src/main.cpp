#include <Arduino.h>
#include <WiFiManager.h>
#include <time.h>
#include "soc/soc.h"           // Added for brownout
#include "soc/rtc_cntl_reg.h"  // Added for brownout
#include "sd_handler.h"
#include "config_handler.h"
#include "camera_handler.h"
#include "web_server.h"
#include "motion_detector.h"

void setupNTP() {
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    setenv("TZ", "CET-1CEST,M3.5.0,M10.5.0/3", 1); // Central Europe Time
    tzset();
    
    Serial.print("Waiting for NTP time sync: ");
    time_t now = time(nullptr);
    int retry = 0;
    while (now < 8 * 3600 * 2 && retry < 10) {
        delay(500);
        Serial.print(".");
        now = time(nullptr);
        retry++;
    }
    Serial.println("");
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    Serial.print("Current time: ");
    Serial.print(asctime(&timeinfo));
}

void setup() {
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout detector
    Serial.begin(115200);
    delay(1000); // Wait for Serial to initialize
    Serial.println("\n\n====================================");
    Serial.println("ESP32-CAM Starting up...");
    Serial.println("====================================\n");
    Serial.setDebugOutput(true);

    // 1. Initialize SD Card
    if (!initSDCard()) {
        Serial.println("SD Card initialization failed!");
    }

    // 2. Load Configuration from SD
    loadConfig();
    printConfig();

    // 3. Setup WiFi
    WiFiManager wm;
    // wm.resetSettings(); // Uncomment to reset WiFi settings
    
    bool connected = false;
    if (strlen(globalConfig.wifi_ssid) > 0) {
        Serial.printf("Connecting to WiFi from config: %s\n", globalConfig.wifi_ssid);
        WiFi.begin(globalConfig.wifi_ssid, globalConfig.wifi_pass);
        // Wait for connection
        int retry = 0;
        while (WiFi.status() != WL_CONNECTED && retry < 20) {
            delay(500);
            Serial.print(".");
            retry++;
        }
        if (WiFi.status() == WL_CONNECTED) {
            connected = true;
            Serial.println("\nSuccessfully connected with config credentials!");
        } else {
            Serial.println("\nFailed to connect with config credentials, starting WiFiManager...");
        }
    }

    if (!connected) {
        Serial.println("Starting WiFiManager (Check for AP: " + String(globalConfig.hostname) + ")");
        if (!wm.autoConnect(globalConfig.hostname)) {
            Serial.println("WiFiManager: Failed to connect and hit timeout");
            ESP.restart();
        }
        Serial.println("WiFiManager: Connection successful!");
    }
    
    Serial.print("WiFi Connected! IP Address: ");
    Serial.println(WiFi.localIP());

    // 4. Setup NTP
    setupNTP();

    // 5. Initialize Camera
    bool cameraOK = initCamera();
    if (!cameraOK) {
        Serial.println("Camera initialization failed! System will stay up for debugging.");
    }

    // 6. Start Web Server (Always start so we can see the UI)
    startWebServer();

    Serial.print("Setup complete. Use 'http://");
    Serial.print(WiFi.localIP());
    Serial.println("' to connect");
}

void loop() {
    if (cameraOK && globalConfig.motion_enabled) {
        camera_fb_t * fb = esp_camera_fb_get();
        if (fb) {
            if (detectMotion(fb)) {
                Serial.println("Motion detected! Attempting to save...");
                
                // Save image to SD
                time_t now = time(nullptr);
                struct tm timeinfo;
                localtime_r(&now, &timeinfo);
                char path[64];
                strftime(path, sizeof(path), "/motion_%Y%m%d_%H%M%S.jpg", &timeinfo);
                
                if (SD_MMC.cardType() == CARD_NONE) {
                    Serial.println("Error: No SD Card detected, cannot save motion image.");
                } else {
                    File file = SD_MMC.open(path, FILE_WRITE);
                    if (file) {
                        file.write(fb->buf, fb->len);
                        file.close();
                        Serial.printf("Saved motion image to %s\n", path);
                    } else {
                        Serial.printf("Failed to open %s for writing\n", path);
                    }
                }
            }
            esp_camera_fb_return(fb);
        } else {
            // This happens if the web stream is using the only available buffer
            // Serial.println("Motion: Could not get frame (busy?)"); 
        }
        delay(500); 
    } else {
        delay(1000);
    }
}
