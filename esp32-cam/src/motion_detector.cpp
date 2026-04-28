#include "motion_detector.h"
#include "config_handler.h"
#include <Arduino.h>

static size_t last_size = 0;

bool detectMotion(camera_fb_t * fb) {
    if (!globalConfig.motion_enabled) return false;
    if (fb == NULL) return false;

    size_t current_size = fb->len;
    bool motion = false;

    if (last_size > 0) {
        int diff = abs((int)current_size - (int)last_size);
        int threshold_val = (last_size * globalConfig.motion_threshold / 100);
        
        // Only log if there is a significant change, but below threshold, to avoid flooding
        if (diff > (threshold_val / 2)) {
            Serial.printf("Motion Debug: Diff=%d, Threshold=%d, Size=%u\n", diff, threshold_val, current_size);
        }

        if (diff > threshold_val) {
            motion = true;
        }
    }

    last_size = current_size;
    return motion;
}
