#ifndef MOTION_DETECTOR_H
#define MOTION_DETECTOR_H

#include "esp_camera.h"

bool detectMotion(camera_fb_t * fb);

#endif
