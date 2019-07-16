#!/bin/bash
export GITHUB_ORGANIZATION=NMGRL
export GITHUB_USER=nmgrluser
export GITHUB_PASSWORD=
export MassSpecDBVersion=16
export CONDA_ENV=pychron3
export CONDA_DISTRO=/Users/ross/anaconda3
export PYCHRON_APPNAME=Pychron
export APPLICATION_ID=1
export QT_API=pyqt

ROOT=$/Users/ross/.pychron.1/pychron
export PYTHONPATH=$ROOT

/Users/ross/anaconda3/envs/pychron3/bin/pythonw $ROOT/launchers/launcher.py
