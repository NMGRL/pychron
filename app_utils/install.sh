#!/bin/sh

#CONFIGURATION
#--------------------------------------------------
APP_PREFIX=./experiment
CONDA_ENV=pychron_env2
APP_NAME=experiment
VERSION=3.0.1
PYCHRONDATA_PREFIX=~/Pychrondata_install_dev2
URL=https://github.com/NMGRL/pychron.git
#--------------------------------------------------

#make root
if [ -d $PYCHRONDATA_PREFIX ]
then
    echo $PYCHRONDATA_PREFIX already exists
else
    mkdir $PYCHRONDATA_PREFIX
    mkdir $PYCHRONDATA_PREFIX/.hidden
    mkdir $PYCHRONDATA_PREFIX/.hidden/updates
    git clone $URL $PYCHRONDATA_PREFIX/.hidden/updates/pychron
fi

#install dependencies
/anaconda/bin/conda create --yes -n $CONDA_ENV python
source /anaconda/bin/activate $CONDA_ENV
/anaconda/bin/conda install --yes --file ./${APP_PREFIX}_conda_requirements.txt
pip install -r ./${APP_PREFIX}_pip_requirements.txt

#build application
cd ${PYCHRONDATA_PREFIX}/.hidden/updates/pychron
python app_utils/app_maker.py -A$APP_NAME -v$VERSION

#move application to Pychrondata
mv ./launchers/py${APP_NAME}_${VERSION}.app ${PYCHRONDATA_PREFIX}/py${APP_NAME}_${VERSION}.app