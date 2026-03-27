#!/bin/bash
set -e

# Activate the conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate pychron_env

# Execute the passed command
exec "$@"