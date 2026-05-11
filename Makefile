# Default to :0 if DISPLAY isn't set as workaround for macos
DISPLAY ?= :0

.PHONY: up clean shell

up:
	@echo "Checking for X11 display..."
	@if [ -z "$(DISPLAY)" ]; then \
		echo "Error: DISPLAY variable is empty."; \
		echo "If on mac, make sure XQuartz is running and run 'export DISPLAY=:0'"; \
		exit 1; \
	fi
	@echo "Configuring permissions for $(DISPLAY)..."
	-xhost +local:docker
	@echo "Starting Pychron..."
	DISPLAY=$(DISPLAY) docker-compose up

clean:
	docker-compose down
	-xhost -local:docker

shell:
	docker-compose run --rm pychron /bin/bash