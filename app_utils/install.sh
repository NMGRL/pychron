#!/bin/sh

#CONFIGURATION
#--------------------------------------------------
APP_PREFIX=experiment
CONDA_ENV=pychron_env
APP_NAME=experiment
VERSION=2.0.5
PYCHRONDATA_PREFIX=~/Pychrondata
URL=https://github.com/NMGRL/pychron.git
ANACONDA_PREFIX=
#--------------------------------------------------

#make root
if [ -d $PYCHRONDATA_PREFIX ]
then
    echo $PYCHRONDATA_PREFIX already exists
else
    mkdir $PYCHRONDATA_PREFIX
    mkdir $PYCHRONDATA_PREFIX/.hidden
    mkdir $PYCHRONDATA_PREFIX/.hidden/updates
    mkdir $PYCHRONDATA_PREFIX/setupfiles

    #write boiler plate xml file
    cat <<EOT >> $PYCHRONDATA_PREFIX/setupfiles/initialization.xml
<root>
  <globals>
  </globals>
  <plugins>
    <general>
      <plugin enabled="true">Database</plugin>
      <plugin enabled="false">Geo</plugin>
      <plugin enabled="false">Experiment</plugin>
      <plugin enabled="true">Processing</plugin>
      <plugin enabled="true">PyScript</plugin>
      <plugin enabled="true">ArArConstants</plugin>
      <plugin enabled="true">Entry</plugin>
      <plugin enabled="false">SystemMonitor</plugin>
    </general>
    <hardware>
    </hardware>
    <data>
    </data>
    <social>
      <plugin enabled="false">Email</plugin>
      <plugin enabled="false">Twitter</plugin>
    </social>
  </plugins>
</root>
EOT

    git clone $URL $PYCHRONDATA_PREFIX/.hidden/updates/pychron
fi

#install dependencies
$ANACONDA_PREFIX/anaconda/bin/conda create --yes -n $CONDA_ENV python
source $ANACONDA_PREFIX/anaconda/bin/activate $CONDA_ENV

$ANACONDA_PREFIX/anaconda/envs/$CONDA_ENV/bin/conda install --yes --file ./${APP_PREFIX}_conda_requirements.txt
$ANACONDA_PREFIX/anaconda/envs/$CONDA_ENV/bin/pip install -r ./${APP_PREFIX}_pip_requirements.txt

#build application
cd ${PYCHRONDATA_PREFIX}/.hidden/updates/pychron
$ANACONDA_PREFIX/anaconda/envs/$CONDA_ENV/bin/python app_utils/app_maker.py -A$APP_NAME -v$VERSION

#move application to Pychrondata
mv ./launchers/py${APP_NAME}_${VERSION}.app ${PYCHRONDATA_PREFIX}/py${APP_NAME}_${VERSION}.app