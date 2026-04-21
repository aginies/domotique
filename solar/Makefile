NAME := solar_domotic
VERSION := 0.1.0

COMMON_SOURCE_DIR := ../common
FILES_TO_COPY := domo_wifi.py save_config.py domo_microdot.py domo_utils.py oled_ssd1306.py esp32_led.py web_files_management.py web_log.py web_upload.py ssd1306.py microdot.py microdot_helpers.py microdot_websocket.py domo_socket_server.py paths.py domo_dns.py
FILES_TO_UPLOAD := config_var.py main.py web_command.py web_config.py solar_monitor.py mqtt_client.py web_command.html web_config.html wifi_setup.py fake_shelly.py

PORT ?= /dev/ttyACM0
AMPY ?= ampy

UPDATEBIN := update.bin

BACKUP_DIR = backup

.PHONY: all
all: $(UPDATEBIN)
upload: clean $(UPDATEBIN) copy

$(UPDATEBIN):
	@echo "Creating a temp_$(NAME) dir and copy files in"
	@mkdir -p temp_$(NAME)
	@cp -avf $(addprefix $(COMMON_SOURCE_DIR)/, $(FILES_TO_COPY)) temp_$(NAME)/
	@cp -avf $(FILES_TO_UPLOAD) temp_$(NAME)/
	@echo $(VERSION) > temp_$(NAME)/VERSION
	@(cd temp_$(NAME)/ && sha256sum * > sha256sum)
	@python3 ./pack.py
	@echo "update.bin created successfully."

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@rm -rf temp_$(NAME) $(UPDATEBIN) unpacked_files unpacked
	@echo "Cleanup complete."

copy:
	@echo "Starting upload to $(PORT)"
	@find temp_$(NAME) -type f | while read -r file; do \
		echo "    - Copying $$file to /"; \
		$(AMPY) --port $(PORT) put "$$file" || exit 1; \
	done
	@echo "Upload complete."

ls:
	@echo "Show files on $(PORT)"
	$(AMPY) --port $(PORT) ls

backup:
	@echo "--- Starting backup from device $(PORT) ---"
	@ampy --port $(PORT) ls
	@mkdir -p $(BACKUP_DIR)
	@for file in $$(ampy --port $(PORT) ls); do \
		local_dest="$(BACKUP_DIR)$${file}"; \
		echo "  -> Copying $$file to $$local_dest"; \
		mkdir -p "$$(dirname "$$local_dest")"; \
		ampy --port $(PORT) get $$file "$$local_dest"; \
	done
	@echo "--- Backup complete! ---"

delete:
	@echo "--- WARNING: This will delete ALL files from $(PORT) ---"
	@read -p "Press [Enter] to confirm, or [Ctrl+C] to abort..."
	@for item in $$(ampy --port $(PORT) ls); do \
		echo "  -> Deleting: $$item"; \
		ampy --port $(PORT) rm $$item > /dev/null 2>&1 || true; \
	done
	@for item in $$(ampy --port $(PORT) ls | tac); do \
		ampy --port $(PORT) rmdir $$item > /dev/null 2>&1 || true; \
	done
	@echo "--- Delete complete! ---"

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  clean      Clean previous build."
	@echo "  $(UPDATEBIN)  Create the $(UPDATEBIN) file."
	@echo "  upload     Upload all files to the device $(PORT)."
	@echo "  delete     Delete all files on the device $(PORT)."
	@echo "  ls         Show all files on device $(PORT)."
	@echo "  help       Show this help message."
	@echo ""
	@echo "Note: umqtt must be installed on the device if MQTT is enabled:"
	@echo "  import mip; mip.install('umqtt.simple')"
