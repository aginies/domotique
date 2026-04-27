# lilygo_solar/Makefile
PORT ?= /dev/ttyACM0
BAUD ?= 115200
AMPY ?= ampy

FILES := config_var.py main.py mqtt_receiver.py wifi.py st7789.py

.PHONY: upload ls delete reset monitor help

upload:
	@echo "Uploading minimal files to $(PORT)..."
	@for file in $(FILES); do \
		echo "    - $$file"; \
		$(AMPY) --port $(PORT) put "$$file" || exit 1; \
	done
	@echo "Upload complete."

ls:
	@$(AMPY) --port $(PORT) ls

delete:
	@echo "Deleting all files from $(PORT)..."
	@for item in $$(ampy --port $(PORT) ls); do \
		echo "    - Deleting: $$item"; \
		ampy --port $(PORT) rm $$item > /dev/null 2>&1 || true; \
	done

reset:
	@echo "Resetting $(PORT)..."
	@$(AMPY) --port $(PORT) reset

monitor:
	@echo "Starting monitor on $(PORT) at $(BAUD) bps..."
	@echo "Press Ctrl+A then K to quit screen."
	@screen $(PORT) $(BAUD)

help:
	@echo "lilygo_solar Minimal Makefile"
	@echo "  make upload   Upload core files"
	@echo "  make ls       List files on device"
	@echo "  make delete   Clean device"
	@echo "  make reset    Reset device"
	@echo "  make monitor  Open serial monitor (screen)"
