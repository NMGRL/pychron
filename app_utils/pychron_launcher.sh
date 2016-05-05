#!/bin/bash

ROOT=~/.pychron/updates/pychron

echo Using $ROOT as "ROOT" directory

ENTRY_POINT=$ROOT/launchers/pyexperiment_debug.py

export PYTHONPATH=$ROOT

GITHUB_USER=
GITHUB_PASSWORD=
GITHUB_ORGANIZATION=

MassSpecDBVersion=16

python $ENTRY_POINT
