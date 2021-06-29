#!/bin/bash
xhost + 127.0.0.1
docker container prune -f
docker run -e DISPLAY=host.docker.internal:0 pychron3
