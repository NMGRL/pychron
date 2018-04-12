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

# =========== Front Matter ==============

cat << "EOF"
  _______     _______ _    _ _____   ____  _   _
 |  __ \ \   / / ____| |  | |  __ \ / __ \| \ | |
 | |__) \ \_/ / |    | |__| | |__) | |  | |  \| |
 |  ___/ \   /| |    |  __  |  _  /| |  | | . ` |
 | |      | | | |____| |  | | | \ \| |__| | |\  |
 |_|      |_|  \_____|_|  |_|_|  \_\\____/|_| \_|


Developer: Jake Ross (NMT)
Date: 10-02-2016
---*---*---*---*---*---*---*---*---*---*---*---*
Welcome to the Pychron Installer.

Hit "Enter" to continue

---*---*---*---*---*---*---*---*---*---*---*---*
EOF

read wait

cat << "EOF"
You will be asked to provide a series of configuration values. Each value has as default value, indicated in square
brackets e.g., [default]

To except the default value hit "Enter" when prompted


!!!WARNING!!!
This installer is beta and not guaranteed to work. USE WITH CAUTION

Hit "Enter" to continue
EOF
read wait

if type git >/dev/null
then
    echo 'Git is already installed'
else
    echo "Git is required"
    exit
fi

if type gcc >/dev/null
then
    echo 'XCode Commandline tools are already installed'
else
    echo "XCode Commandline tools are required"
    xcode-select --install
fi
# =========== User Questions ==============
echo "In order to submit issues to the Pychron developers you need to have a Github account"

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

default=NMGRL
echo -n "Pychron Fork [$default] >> "
read pychron_fork
[ -z "$pychron_fork" ] && pychron_fork=$default

default=release/py3/v18.2
echo -n "Pychron Version [$default] >> "
read branch
[ -z "$branch" ] && branch=$default

default=pyqt
echo -n "Qt Bindings [$default] >> "
read qt_bindings
[ -z "$qt_bindings" ] && qt_bindings=$default
if [[ ${qt_bindings} == "pyqt" ]]
then
    USE_PYQT=1
else
    USE_PYQT=0
fi

default=yes
echo -n "Make a MacOSX application [$default] >> "
read use_app_bundle
[ -z "$use_app_bundle" ] && use_app_bundle=$default

if [[ ${use_app_bundle} == "yes" ]]
then
  default=Pychron
  echo -n "Application name [$default] >> "
  read app_name
  [ -z "$app_name" ] && app_name=$default
fi


default=0
echo -n "Application ID [$default] >> "
read APPLICATION_ID
[ -z "$APPLICATION_ID" ] && APPLICATION_ID=$default

default=Pychron
echo -n "Pychron Data directory [$default] >> "
read PYCHRONDATA_NAME
[ -z "$PYCHRONDATA_NAME" ] && PYCHRONDATA_NAME=$default


default=pychron3
echo -n "Conda environment name [$default] >> "
read CONDA_ENV
[ -z "$CONDA_ENV" ] && CONDA_ENV=$default



# =========== Configuration ===============

MINICONDA_URL=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
MINICONDA_INSTALLER_SCRIPT=miniconda_installer.sh

CONDA_DISTRO=$HOME/miniconda3
PYCHRON_APPNAME=pyview

PYCHRONDATA_PREFIX=~/${PYCHRONDATA_NAME}
LAUNCHER_SCRIPT_PATH=launcher.sh
PYCHRON_GIT_SOURCE_URL=https://github.com/${pychron_fork}/pychron.git

CONDA_REQ="qt=4
numpy
statsmodels
scikit-learn
PyYAML
yaml
envisage
sqlalchemy
Reportlab
lxml
xlrd
xlwt
xlsxwriter
requests
keyring
pillow
python.app
gitpython
cython
pytables
pymysql
certifi
jinja2
swig
"

if [[ ${USE_PYQT} == "1" ]]
then
    CONDA_REQ="pyqt ${CONDA_REQ}"
else
    CONDA_REQ="pyside ${CONDA_REQ}"
fi

PIP_REQ="uncertainties
peakutils
qimage2ndarray
chaco"


DEBUG=0

# ============== Install Pychron source ==============
UPDATE_ROOT=~/.pychron.${APPLICATION_ID}
PYCHRON_PATH=${UPDATE_ROOT}/pychron

if [ -d ${UPDATE_ROOT} ]
    then
        if [ ! -d ${PYCHRON_PATH} ]
        then
           mkdir ${PYCHRON_PATH}
        fi
else
    mkdir ${UPDATE_ROOT}
    mkdir ${PYCHRON_PATH}
fi


if [[ ${DEBUG} == 1 ]]
then
    echo "Skipping cloning source"
else
    if [ -d ${PYCHRON_PATH} ]
    then
        echo "Removing existing pychron source code"
        rm -rf ${PYCHRON_PATH}
    fi

    git clone ${PYCHRON_GIT_SOURCE_URL} --branch=${branch} ${PYCHRON_PATH}
fi

# =========== Conda =======================
# check for conda
if type ${CONDA_DISTRO}/bin/conda >/dev/null
then
    # update conda
    echo conda already installed
    ${CONDA_DISTRO}/bin/conda update --yes conda
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
     ${CONDA_DISTRO}/bin/conda update --yes conda
     echo Conda Updated

     rm ./$MINICONDA_INSTALLER_SCRIPT
fi

if [[ ${DEBUG} == 1 ]]
then
    echo "Skipping creating environment"
else
    ${CONDA_DISTRO}/bin/conda create --yes -n${CONDA_ENV} python=3.5

    # install requirements
    source ${CONDA_DISTRO}/bin/activate ${CONDA_ENV}
    conda install --yes ${CONDA_REQ}
    pip install ${PIP_REQ}
fi

# ========== Launcher Script ===============
if [[ -f ${LAUNCHER_SCRIPT_PATH} ]]
then
    rm ${LAUNCHER_SCRIPT_PATH}
fi

touch ${LAUNCHER_SCRIPT_PATH}
echo "#!/bin/bash" >> ${LAUNCHER_SCRIPT_PATH}
echo export GITHUB_ORGANIZATION=${go} >> ${LAUNCHER_SCRIPT_PATH}
echo export GITHUB_USER=${gu} >> ${LAUNCHER_SCRIPT_PATH}
echo export GITHUB_PASSWORD=${gp} >> ${LAUNCHER_SCRIPT_PATH}
echo export MassSpecDBVersion=${dbv} >> ${LAUNCHER_SCRIPT_PATH}
echo export CONDA_ENV=${CONDA_ENV} >> ${LAUNCHER_SCRIPT_PATH}
echo export CONDA_DISTRO=${CONDA_DISTRO} >> ${LAUNCHER_SCRIPT_PATH}
echo export PYCHRON_APPNAME=${PYCHRON_APPNAME} >> ${LAUNCHER_SCRIPT_PATH}
echo export APPLICATION_ID=${APPLICATION_ID} >> ${LAUNCHER_SCRIPT_PATH}

if [[ ${USE_PYQT} == "1" ]]
then
    echo export QT_API=pyqt >> ${LAUNCHER_SCRIPT_PATH}
else
    echo export QT_API=pyside >> ${LAUNCHER_SCRIPT_PATH}
fi

echo ROOT=${PYCHRON_PATH} >> ${LAUNCHER_SCRIPT_PATH}

echo ENTRY_POINT=\$ROOT/launchers/launcher.py >> ${LAUNCHER_SCRIPT_PATH}
echo export PYTHONPATH=\$ROOT >> ${LAUNCHER_SCRIPT_PATH}

echo \$CONDA_DISTRO/envs/\$CONDA_ENV/bin/pythonw \$ENTRY_POINT >> ${LAUNCHER_SCRIPT_PATH}


if [[ ${use_app_bundle} == "yes" ]]
then
    #  Create the app bundle
    APPNAME=${app_name}
    DIR="${APPNAME}.app/Contents/MacOS";
    mkdir -p "${DIR}"

    cp "${LAUNCHER_SCRIPT_PATH}" "${DIR}/${APPNAME}"
    chmod +x "${DIR}/${APPNAME}"

#  mkdir -p "${APPNAME}.app/Contents/Resources";
#
#  # write plist
#  PLIST="${APPNAME}.app/Contents/Info.plist"
#  touch ${PLIST}

#  cat > ${PLIST} << EOF
#<?xml version="1.0" encoding="UTF-8"?>
#<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
#<plist version="1.0"><dict>
#<key>CFBundleIconFile</key><string>${ICON_NAME}</string>
#</dict>
#</plist>
#EOF

#  mv ${APPNAME}.app /Applications
    rm ${LAUNCHER_SCRIPT_PATH}
else
    chmod +x ${LAUNCHER_SCRIPT_PATH}
    mv ${LAUNCHER_SCRIPT_PATH} ~/Desktop/
fi


# ===============================================================
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

    cat > ${PYCHRONDATA_PREFIX}/preferences/dvc.ini << EOF
[pychron.igsn]
url = 'https://app.geosamples.org/webservices/upload.php'
EOF

    cat > ${PYCHRONDATA_PREFIX}/preferences/update.ini << EOF
[pychron.update]
branch = ${branch}
build_repo = ${PYCHRON_PATH}
remote = ${go}/pychron

EOF

cat > ${PYCHRONDATA_PREFIX}/preferences/experiment.ini << EOF
[pychron.experiment]
success_color = '#FFFFFF'
extraction_color = '#FFFFFF'
measurement_color = '#FFFFFF'
canceled_color = '#FF0000'
truncated_color = '#FFFFFF'
failed_color = '#FFFFFF'
end_after_color = '#AAAAAA'
invalid_color = '#FF0000'
EOF

    cat > ${PYCHRONDATA_PREFIX}/setupfiles/initialization.xml << EOF
<root>
  <globals>
  </globals>
  <plugins>
    <general>
      <plugin enabled='true'>ArArConstants</plugin>
      <plugin enabled='true'>DVC</plugin>
      <plugin enabled='true'>GitHub</plugin>
      <plugin enabled='true'>Pipeline</plugin>
      <plugin enabled='true'>Update</plugin>
    </general>
    <hardware>
    </hardware>
    <data>
    </data>
    <social>
      <plugin enabled='false'>Email</plugin>
      <plugin enabled='false'>Twitter</plugin>
    </social>
  </plugins>
</root>
EOF

    cat > ${PYCHRONDATA_PREFIX}/setupfiles/startup_tests.yaml << EOF
- plugin: ArArConstantsPlugin
  tests:
- plugin: DVC
  tests:
    - test_database
    - test_dvc_fetch_meta
- plugin: GitHub
  tests:
    - test_api
EOF

fi


# ============= EOF =============================================
