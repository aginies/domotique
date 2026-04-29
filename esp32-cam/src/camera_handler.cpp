#include "camera_handler.h"
#include <Arduino.h>

bool cameraOK = false;

bool initCamera() {
    cameraOK = false;
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000; // Reverted to 20MHz
    config.pixel_format = PIXFORMAT_JPEG;

    // Re-enable PSRAM for multiple buffers (allows motion detection + web stream)
    if (psramFound()) {
        config.frame_size = (framesize_t)globalConfig.resolution;
        config.jpeg_quality = 10;
        config.fb_count = 2;
        config.fb_location = CAMERA_FB_IN_PSRAM;
    } else {
        config.frame_size = FRAMESIZE_VGA;
        config.jpeg_quality = 12;
        config.fb_count = 1;
        config.fb_location = CAMERA_FB_IN_DRAM;
    }

    // Give hardware time to settle
    delay(500);

    // Camera init (ESP core handles SCCB bus recovery internally)
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x", err);
        return false;
    }

    sensor_t * s = esp_camera_sensor_get();
    if (s->id.PID == OV3660_PID) {
        s->set_vflip(s, 1); // flip it back
        s->set_brightness(s, 1); // up the brightness a bit
        s->set_saturation(s, -2); // lower the saturation
    }
    
    // Set initial settings from config
    updateCameraSettings();

    // Flash LED pin
    pinMode(FLASH_GPIO_NUM, OUTPUT);
    digitalWrite(FLASH_GPIO_NUM, LOW);

    cameraOK = true;
    return true;
}

bool updateCameraSettings() {
    sensor_t * s = esp_camera_sensor_get();
    if (s == NULL) return false;

    s->set_framesize(s, (framesize_t)globalConfig.resolution);
    s->set_vflip(s, globalConfig.flip ? 1 : 0);
    s->set_hmirror(s, globalConfig.mirror ? 1 : 0);
    
    // For 180 degree rotation, we can use both vflip and hmirror
    if (globalConfig.rotation == 180) {
        s->set_vflip(s, !globalConfig.flip ? 1 : 0);
        s->set_hmirror(s, !globalConfig.mirror ? 1 : 0);
    }
    // Note: 90/270 degree hardware rotation is not supported by standard esp_camera API for OV2640.
    // It would require software processing which is slow.

    return true;
}

void setFlash(bool state) {
    globalConfig.flash_enabled = state;
    digitalWrite(FLASH_GPIO_NUM, state ? HIGH : LOW);
}
