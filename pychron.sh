#!/bin/bash
xhost + 127.0.0.1
docker container prune -f
docker run -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=host.docker.internal:0 pychron3
