#ifndef CONFIG_HANDLER_H
#define CONFIG_HANDLER_H

#include <ArduinoJson.h>
#include <Arduino.h>

struct Config {
    int resolution; // 0-14 (FRAMESIZE_UXGA, etc.)
    int rotation;   // 0, 90, 180, 270
    bool flip;
    bool mirror;
    bool flash_enabled;
    bool motion_enabled;
    int motion_threshold;
    char hostname[32];
    char wifi_ssid[32];
    char wifi_pass[64];
};

extern Config globalConfig;

bool loadConfig();
bool saveConfig();
void printConfig();

#endif
