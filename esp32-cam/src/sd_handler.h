#ifndef SD_HANDLER_H
#define SD_HANDLER_H

#include "FS.h"
#include "SD_MMC.h"

bool initSDCard();
bool writeFile(fs::FS &fs, const char * path, const char * message);
String readFile(fs::FS &fs, const char * path);

#endif
