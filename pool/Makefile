NAME := pool_domotic
VERSION := 0.9.3

COMMON_SOURCE_DIR := ../common
FILES_TO_COPY := domo_wifi.py save_config.py domo_utils.py oled_ssd1306.py esp32_led.py web_files_management.py crtl_relay.py web_log.py ssd1306.py microdot.py microdot_helpers.py microdot_websocket.py
FILES_TO_UPLOAD := config_var.py main.py web_command.py web_config.py

PORT ?= /dev/ttyACM0
AMPY ?= ampy

UPDATEBIN := update.bin

BACKUP_DIR = backup

.PHONY: all
all: $(UPDATEBIN)
upload: clean $(UPDATEBIN) copy

$(UPDATEBIN):
	@echo "Creating a temp_$(NAME) dir and copy files in"
	# Create a temporary directory to stage the files
	@mkdir -p temp_$(NAME)
	@cp -avf $(addprefix $(COMMON_SOURCE_DIR)/, $(FILES_TO_COPY)) temp_$(NAME)/
	@cp -avf $(FILES_TO_UPLOAD) temp_$(NAME)/
	@echo $(VERSION) > temp_$(NAME)/VERSION
	@(cd temp_$(NAME)/ && sha256sum * > sha256sum)
	@python3.13 ./pack.py
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
	@echo "[1/3] Listing all files on the device..."
	@ampy --port $(PORT) ls
	@echo "[2/3] Creating local backup directory: '$(BACKUP_DIR)'"
	@mkdir -p $(BACKUP_DIR)
	@echo "[3/3] Copying files to '$(BACKUP_DIR)'..."
	@for file in $$(ampy --port $(PORT) ls); do \
		local_dest="$(BACKUP_DIR)$${file}"; \
		echo "  -> Copying $$file to $$local_dest"; \
		mkdir -p "$$(dirname "$$local_dest")"; \
		ampy --port $(PORT) get $$file "$$local_dest"; \
	done
	@echo "--- Backup complete! ---"

delete:
	@echo "--- WARNING: This will delete ALL files and directories from $(PORT) ---"
	@read -p "Press [Enter] to confirm, or [Ctrl+C] to abort..."
	@echo "[1/2] Deleting all files..."
	@for item in $$(ampy --port $(PORT) ls); do \
		echo "  -> Deleting file: $$item"; \
		ampy --port $(PORT) rm $$item > /dev/null 2>&1 || true; \
	done
	@echo "[2/2] Deleting all directories..."
	@for item in $$(ampy --port $(PORT) ls | tac); do \
		echo "  -> Deleting directory: $$item"; \
		ampy --port $(PORT) rmdir $$item > /dev/null 2>&1 || true; \
	done
	@echo "--- Delete complete! ---"

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  clean   	Clean all previous build."
	@echo "  $(UPDATEBIN)n 	Create the $(UPDATEBIN) file."
	@echo "  upload    	Uploads all files to the device $(PORT)."
	@echo "  delete    	Delete all files and directory on the device $(PORT)."
	@echo "  ls     	Show all files on device $(PORT)."
	@echo "  help      	Shows this help message."
