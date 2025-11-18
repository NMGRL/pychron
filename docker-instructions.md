## Instructions

### Dependencies
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

1. Install [Homebrew](https://brew.sh/)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

1. Install XQuartz
```bash
brew install --cask xquartz
```

XQuartz Settings > Security and check "Allow connections from network clients"
Quit and restart XQuartz

## Run Pychron
1. Run startup script

```bash
chmod +x run.sh
# run script
./run.sh
```

A login popup should appear.

If the startup script returns a build error, rebuild the docker image and rerun the startup script
```bash
# Rebuild image
docker-compose up --build
# rerun script
./run.sh
```

