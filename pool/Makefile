NAME := pool_domotic
VERSION := 0.9.0

COMMON_SOURCE_DIR := ../common
FILES_TO_COPY := domo_wifi.py save_config.py domo_utils.py oled_ssd1306.py esp32_led.py web_files_management.py crtl_relay.py web_log.py

UPDATEBIN := update.bin

.PHONY: all
all: $(UPDATEBIN)

$(UPDATEBIN):
	@echo "Creating a tarball named $(TARBALL)..."
	# Create a temporary directory to stage the files
	@mkdir -p temp_$(NAME)
	@cp $(addprefix $(COMMON_SOURCE_DIR)/, $(FILES_TO_COPY)) temp_$(NAME)/
	@cp -avf *.py temp_$(NAME)/
	@echo $(VERSION) > temp_$(NAME)/VERSION
	@rm -vf temp_$(NAME)/*pack.py
	@(cd temp_$(NAME)/ && sha256sum * > sha256sum)
	@python3.13 ./pack.py
	@echo "update.bin created successfully."

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@rm -rf temp_$(NAME) $(UPDATEBIN) unpacked_files unpacked
	@echo "Cleanup complete."
