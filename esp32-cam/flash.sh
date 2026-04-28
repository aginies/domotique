#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Starting Build Process ---"
pio run

echo ""
echo "--- Starting Upload Process ---"
# Check if a port is provided as an argument, otherwise use default auto-detection
if [ -n "$1" ]; then
    pio run -t upload --upload-port "$1"
else
    pio run -t upload
fi

echo ""
echo "--- Opening Serial Monitor (115200 baud) ---"
echo "Press Ctrl+C to exit the monitor"
if [ -n "$1" ]; then
    pio device monitor -b 115200 --port "$1"
else
    pio device monitor -b 115200
fi
