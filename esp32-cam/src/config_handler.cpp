#include "config_handler.h"
#include "sd_handler.h"

Config globalConfig;

bool loadConfig() {
    String json = readFile(SD_MMC, "/config.json");
    if (json.length() == 0) {
        Serial.println("No config file found, using defaults");
        globalConfig.resolution = 6; // VGA
        globalConfig.rotation = 0;
        globalConfig.flip = false;
        globalConfig.mirror = false;
        globalConfig.flash_enabled = false;
        globalConfig.motion_enabled = false;
        globalConfig.motion_threshold = 15;
        strcpy(globalConfig.hostname, "esp32-cam");
        strcpy(globalConfig.wifi_ssid, "");
        strcpy(globalConfig.wifi_pass, "");
        return saveConfig();
    }

    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, json);

    if (error) {
        Serial.print("deserializeJson() failed: ");
        Serial.println(error.c_str());
        return false;
    }

    globalConfig.resolution = doc["resolution"] | 6;
    globalConfig.rotation = doc["rotation"] | 0;
    globalConfig.flip = doc["flip"] | false;
    globalConfig.mirror = doc["mirror"] | false;
    globalConfig.flash_enabled = doc["flash_enabled"] | false;
    globalConfig.motion_enabled = doc["motion_enabled"] | false;
    globalConfig.motion_threshold = doc["motion_threshold"] | 15;
    strlcpy(globalConfig.hostname, doc["hostname"] | "esp32-cam", sizeof(globalConfig.hostname));
    strlcpy(globalConfig.wifi_ssid, doc["wifi_ssid"] | "", sizeof(globalConfig.wifi_ssid));
    strlcpy(globalConfig.wifi_pass, doc["wifi_pass"] | "", sizeof(globalConfig.wifi_pass));

    return true;
}

bool saveConfig() {
    JsonDocument doc;
    doc["resolution"] = globalConfig.resolution;
    doc["rotation"] = globalConfig.rotation;
    doc["flip"] = globalConfig.flip;
    doc["mirror"] = globalConfig.mirror;
    doc["flash_enabled"] = globalConfig.flash_enabled;
    doc["motion_enabled"] = globalConfig.motion_enabled;
    doc["motion_threshold"] = globalConfig.motion_threshold;
    doc["hostname"] = globalConfig.hostname;
    doc["wifi_ssid"] = globalConfig.wifi_ssid;
    doc["wifi_pass"] = globalConfig.wifi_pass;

    String json;
    serializeJson(doc, json);
    return writeFile(SD_MMC, "/config.json", json.c_str());
}

void printConfig() {
    Serial.println("Current Configuration:");
    Serial.printf("Resolution: %d\n", globalConfig.resolution);
    Serial.printf("Rotation: %d\n", globalConfig.rotation);
    Serial.printf("Flip: %s\n", globalConfig.flip ? "true" : "false");
    Serial.printf("Mirror: %s\n", globalConfig.mirror ? "true" : "false");
    Serial.printf("Flash: %s\n", globalConfig.flash_enabled ? "true" : "false");
    Serial.printf("Motion Enabled: %s\n", globalConfig.motion_enabled ? "true" : "false");
    Serial.printf("Motion Threshold: %d\n", globalConfig.motion_threshold);
    Serial.printf("Hostname: %s\n", globalConfig.hostname);
    Serial.printf("WiFi SSID: %s\n", globalConfig.wifi_ssid);
}
