#!/bin/bash
set -e

OS="$(uname -s)"

if [ "$OS" = "Darwin" ]; then
    if ! pgrep -x "X11.bin" > /dev/null; then
        echo "Starting XQuartz..."
        open -a XQuartz
        sleep 3
    fi

    [ -z "$DISPLAY" ] && export DISPLAY=:0
    
    # add localhost to xquartz
    xhost + 127.0.0.1 > /dev/null
    
    # Use special DNS for mac
    export DOCKER_DISPLAY="host.docker.internal:0"
else
    [ -z "$DISPLAY" ] && export DISPLAY=:0
    xhost +local:docker
    export DOCKER_DISPLAY=$DISPLAY
fi

echo "Starting Pychron on $OS..."
export DISPLAY_VAR=$DOCKER_DISPLAY

docker-compose up --build