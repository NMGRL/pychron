FROM condaforge/miniforge3:latest

LABEL maintainer="Pychron Docker Builder"
LABEL description="Docker environment for AGESLDEO/pychron"

# 1. Build Stage 

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies for gui and audio
RUN apt-get update && apt-get install -y \
    git build-essential libgl1 libegl1 libxrandr2 libxss1 libxcursor1 \
    libxcomposite1 libasound2t64 libxi6 libxtst6 libxkbcommon-x11-0 \
    nano alsa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# 2. Run Stage 

# Create conda environment 
# Install older versions of traits as a workaround for Color import errors
RUN mamba create -n pychron_env python=3.9 \
    numpy \
    cython \
    "traits=6.3.2" \
    "traitsui<8.0.0" \
    "pyface<8.0.0" \
    envisage \
    apptools \
    pyqt \
    -c conda-forge -y && \
    mamba clean -afy

# Install Pip dependencies with uv
SHELL ["conda", "run", "-n", "pychron_env", "/bin/bash", "-c"]

# Install chaco/enable explicitly for ARM64/Apple Silicon build issues
# Install requirements
RUN echo "Installing dependencies..." && \
    uv pip install chaco enable --python $CONDA_PREFIX && \
    if [ -f "docs/requirements.txt" ]; then \
        uv pip install -r docs/requirements.txt --python $CONDA_PREFIX; \
    fi && \
    if [ -f "app_utils/requirements/pip_requirements.txt" ]; then \
        uv pip install -r app_utils/requirements/pip_requirements.txt --python $CONDA_PREFIX; \
    fi

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV PYCHRON_USE_LOGIN=0
ENV QT_X11_NO_MITSHM=1
ENV CONDA_DEFAULT_ENV=pychron_env

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "launchers/launcher.py"]