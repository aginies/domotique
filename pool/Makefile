NAME := pool_domotic
VERSION := 0.9.0

COMMON_SOURCE_DIR := ../common
FILES_TO_COPY := domo_wifi.py save_config.py domo_utils.py oled_ssd1306.py esp32_led.py web_files_management.py

TARBALL := $(NAME)-$(VERSION).tar.gz

.PHONY: all
all: $(TARBALL)

$(TARBALL):
	@echo "Creating a tarball named $(TARBALL)..."
	# Create a temporary directory to stage the files
	@mkdir -p temp_$(NAME)
	@cp $(addprefix $(COMMON_SOURCE_DIR)/, $(FILES_TO_COPY)) temp_$(NAME)/
	cp -avf *.py temp_$(NAME)/
	@tar -czf $(TARBALL) temp_$(NAME)/
	@echo "Tarball created successfully."

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@rm -rf temp_$(NAME) $(TARBALL)
	@echo "Cleanup complete."
