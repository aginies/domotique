#include "motion_detector.h"
#include "config_handler.h"
#include <Arduino.h>

static const int HISTORY_SIZE = 5;
static size_t frame_history[HISTORY_SIZE] = {0};
static int hist_idx = 0;
static int warmup_count = 0;

bool detectMotion(camera_fb_t * fb) {
    if (!globalConfig.motion_enabled) return false;
    if (fb == NULL) return false;

    size_t current_size = fb->len;

    // Warmup phase: fill history buffer without triggering motion
    if (warmup_count < HISTORY_SIZE) {
        frame_history[warmup_count] = current_size;
        warmup_count++;
        return false;
    }

    // Calculate rolling average of the last HISTORY_SIZE frames
    unsigned long sum = 0;
    for (int i = 0; i < HISTORY_SIZE; i++) {
        sum += frame_history[i];
    }
    int avg = (int)(sum / HISTORY_SIZE);

    // Absolute delta from the rolling average
    int delta = abs((int)current_size - avg);

    // Threshold: per mille of average + absolute minimum
    int threshold = (avg * globalConfig.motion_threshold) / 1000;
    if (threshold < 50) threshold = 50;

    Serial.printf("Motion check: delta=%d, threshold=%d, avg=%d, current=%u\n", delta, threshold, avg, current_size);

    if (delta > threshold) {
        warmup_count = 0;  // Reset baseline for new scene
        return true;
    }

    // Update rolling history: remove oldest, add current
    sum -= frame_history[hist_idx];
    frame_history[hist_idx] = current_size;
    hist_idx = (hist_idx + 1) % HISTORY_SIZE;

    return false;
}
