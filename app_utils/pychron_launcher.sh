#!/bin/bash

ROOT=~/Programming/pychron
if [ ! -d $ROOT ]; then
    ROOT=~/Programming/git/pychron
    if [ ! -d $ROOT ]; then
      ROOT=~/Programming/github/pychron/
      if [ ! -d $ROOT ]; then
        ROOT=~/Programming/github/pychron_dev
      fi
    fi
fi

echo Using $ROOT as "ROOT" directory

ENTRY_POINT=$ROOT/launchers/pyexperiment_debug.py

export PYTHONPATH=$ROOT

python $ENTRY_POINT
