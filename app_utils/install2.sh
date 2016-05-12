#!/usr/bin/env bash
# This script is used to install pychron
# First in downloads and installs miniconda
# miniconda is used to manage the python dependencies
# conda is used to create a new environment
# conda and pip are used to install the dependencies
# a Pychron support directory is created and some boilerplate support files are written
# the pychron source code is downloaded from the available releases stored at github
#    (i.e the source is not a git clone just a static directory)
# if update_flag is set then clone the repository into .pychron/updates/
# the source code is stored in the Pychron support directory
# a launcher script is created and copied to the desktop

# =========== User Questions ==============
default=NMGRL
echo -n "Github organization [$default] >> "
read go
[ -z "$go" ] && go=$default

default=nmgrluser
echo -n "Github user name [$default] >> "
read gu
[ -z "$gu" ] && gu=$default

echo -n "Github password for ${gu} >> "
read gp

default=16
echo -n "MassSpec Database Version [$default] >> "
read dbv
[ -z "$dbv" ] && dbv=$default

echo export GITHUB_ORGANIZATION=${go} >> ${LAUNCHER_SCRIPT_PATH}
echo export GITHUB_USER=${gu} >> ${LAUNCHER_SCRIPT_PATH}
echo export GITHUB_PASSWORD=${gp} >> ${LAUNCHER_SCRIPT_PATH}
echo export MassSpecDBVersion=$dbv >> ${LAUNCHER_SCRIPT_PATH}

# =========== Configuration ===============
WORKING_DIR=~/pychron_install_wd

MINICONDA_URL=https://repo.continuum.io/miniconda/Miniconda-latest-MacOSX-x86_64.sh
MINICONDA_INSTALLER_SCRIPT=miniconda_installer.sh
MINICONDA_PREFIX=$HOME/miniconda2

CONDA_ENV=pychron
DOWNLOAD_URL=https://github.com/NMGRL/pychron/archive/v3.tar.gz

PYCHRONDATA_PREFIX=~/Pychron
ENTHOUGHT_DIR=$HOME/.enthought
PREFERENCES_ROOT=pychron.view.application.root

USE_UPDATE=1

LAUNCHER_SCRIPT_PATH=pychron_launcher.sh
APPLICATION=pyview_debug
PYCHRON_GIT_SOURCE_URL=https://github.com/NMGRL/pychron.git

PYCHRON_PATH=${PYCHRONDATA_PREFIX}/src

CONDA_REQ="statsmodels
scikit-learn
PyYAML
traits
traitsui
chaco
enable
pyface
envisage
sqlalchemy
Reportlab
lxml
xlrd
xlwt
pip
PySide
matplotlib
PyMySQL
requests
keyring
pil
paramiko"

PIP_REQ="uncertainties
pint
GitPython
peakutils"

# =========== Payload text ===============
INITIALIZATION="<root>\n
  <globals>\n
  </globals>\n
  <plugins>\n
    <general>\n
      <plugin enabled='true'>ArArConstants</plugin>\n
      <plugin enabled='true'>DVC</plugin>\n
      <plugin enabled='true'>GitHub</plugin>\n
      <plugin enabled='true'>Pipeline</plugin>\n
      <plugin enabled='true'>Update</plugin>\n
    </general>\n
    <hardware>\n
    </hardware>\n
    <data>\n
    </data>\n
    <social>\n
      <plugin enabled='false'>Email</plugin>\n
      <plugin enabled='false'>Twitter</plugin>\n
    </social>\n
  </plugins>\n
</root>\n
"

DVC_PREFS="[pychron.dvc]\n
organization=NMGRLData\n
meta_repo_name=MetaData\n
"

PREFERENCES="[pychron.genera]\n
[pychron.dvc]\n
organization=NMGRLData\n
meta_repo_name=MetaData\n
"

STARTUP_TESTS="- plugin: ArArConstantsPlugin\n
  tests:\n
- plugin: DVC\n
  tests:\n
    - test_database\n
    - test_dvc_fetch_meta\n
- plugin: GitHub\n
  tests:\n
    - test_api\n
"
# =========== Setup Working dir ===========
cd

if ! [ -e ${WORKING_DIR} ]
 then
  echo Making working directory
  mkdir ${WORKING_DIR}
fi
cd ${WORKING_DIR}

# =========== Conda =======================
# check for conda
if type ${MINICONDA_PREFIX}/bin/conda >/dev/null
then
    # update conda
    echo conda already installed
    ${MINICONDA_PREFIX}/bin/conda update --yes conda
    echo Conda Updated
else
    echo conda doesnt exist
    # install conda

     # download miniconda installer script
     if ! [ -e ./${MINICONDA_INSTALLER_SCRIPT} ]
     then
         echo Downloading conda
        curl -L ${MINICONDA_URL} -o ${MINICONDA_INSTALLER_SCRIPT}
     fi

     chmod +x ./${MINICONDA_INSTALLER_SCRIPT}

     echo Installing conda. This may take a few minutes. Please be patient
     ./${MINICONDA_INSTALLER_SCRIPT} -b

     echo Conda Installed
     ${MINICONDA_PREFIX}/bin/conda update --yes conda
     echo Conda Updated
fi

${MINICONDA_PREFIX}/bin/conda create --yes -n${CONDA_ENV} pip

# install requirements
${MINICONDA_PREFIX}/envs/${CONDA_ENV}/bin/conda install -n${CONDA_ENV} --yes ${CONDA_REQ}
${MINICONDA_PREFIX}/envs/${CONDA_ENV}/bin/pip install ${PIP_REQ}

# =========== Support files ================
# make root
if [ -d ${PYCHRONDATA_PREFIX} ]
then
    echo ${PYCHRONDATA_PREFIX} already exists
else
    echo Making root directory ${PYCHRONDATA_PREFIX}
    mkdir ${PYCHRONDATA_PREFIX}
    mkdir ${PYCHRONDATA_PREFIX}/setupfiles
    mkdir ${PYCHRONDATA_PREFIX}/preferences

    printf ${DVC_PREFS} > ${PYCHRONDATA_PREFIX}/preferences/dvc.ini
    printf ${INITIALIZATION} > ${PYCHRONDATA_PREFIX}/setupfiles/initialization.xml
fi

# ========= Enthought directory ============
if [ -d ${ENTHOUGHT_DIR} ]
then
    echo ${ENTHOUGHT_DIR} already exists
else
    echo Making root directory ${ENTHOUGHT_DIR}
    mkdir ${ENTHOUGHT_DIR}
fi

printf ${PREFERENCES} > ${ENTHOUGHT_DIR}/${PREFERENCES_ROOT}/preferences.ini

# ============== Install Pychron source ==============
if [[ ${USE_UPDATE} == "1" ]]
then
    if [ -d ~/.pychron/ ]
        then
            if [ ! -d ~/.pychron/updates ]
            then
               mkdir ~/.pychron/updates
            fi
        else
            mkdir ~/.pychron/
            mkdir ~/.pychron/updates
        fi
    git clone ${PYCHRON_GIT_SOURCE_URL} ~/.pychron/updates
    PYCHRON_PATH=~/.pychron/updates
else
    # =========== Unpack Release ===============
    cd ${PYCHRONDATA_PREFIX}
    mkdir ./src
    curl -L ${DOWNLOAD_URL} -o pychron_src.tar.gz
    tar -xf ./pychron_src.tar.gz -C ./src --strip-components=1
fi

# ========== Launcher Script ===============
touch ${LAUNCHER_SCRIPT_PATH}

echo ROOT=${PYCHRON_PATH} > ${LAUNCHER_SCRIPT_PATH}

echo ENTRY_POINT=\$ROOT/launchers/${APPLICATION}.py >> ${LAUNCHER_SCRIPT_PATH}
echo export PYTHONPATH=\$ROOT >> ${LAUNCHER_SCRIPT_PATH}

echo ${MINICONDA_PREFIX}/envs/${CONDA_ENV}/bin/python \$ENTRY_POINT >> ${LAUNCHER_SCRIPT_PATH}

chmod +x ${LAUNCHER_SCRIPT_PATH}
cp ${LAUNCHER_SCRIPT_PATH} ~/Desktop/
# ============= EOF =============================================
