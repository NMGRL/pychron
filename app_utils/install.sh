#!/bin/sh

#this script will install pychron and all dependencies including git and an anaconda environment
#
#1. install git, conda
#2. make default support files directories
#3. write a default xml initialization file
#4. clone repo to .hidden/updates
#5. create conda env
#6. install dependencies
#7. checkout branch
#8. build application
#9. move app to root
#10. move app to /Applications


#CONFIGURATION
#--------------------------------------------------
GIT_VERSION=1.9.5
AUTOCONF_VERSION=2.68

APP_PREFIX=experiment
CONDA_ENV=pychron_experiment
APP_NAME=experiment
VERSION=v2.1.0rc1
PYCHRONDATA_PREFIX=~/Pychron
ORGANIZATION=USGSDenverPychron
URL=https://github.com/${ORGANIZATION}/pychron.git
ANACONDA_PREFIX=$HOME/anaconda
BRANCH=release/v2.1.0

#--------------------------------------------------
#if [ "${APP_NAME}" == "view" ]
#then
#Requirements
CONDA_REQ="statsmodels>=0.5.0\n
PyYAML>=3\n
traits>=4.4\n
traitsui>=4.4\n
chaco>=4.4\n
enable>=4.3\n
pyface>=4.4\n
envisage\n
sqlalchemy\n
Reportlab\n
lxml\n
xlrd\n
xlwt\n
pip\n
PySide\n
matplotlib\n
pil"

PIP_REQ="uncertainties\n
PyMySQL\n
pint\n
GitPython"
#fi

#--------------------------------------------------

# note the launching directory
LDIR=`pwd`

#install dependencies
# install git


cd
if ! [ -d pychron_build ]
then
 echo making build directory at ${HOME}/pychron_build
 mkdir pychron_build
fi

cd pychron_build

if ! hash git >/dev/null
then
 echo Please install git. Goto http://git-scm.com/downloads
 exit
fi

if type ${ANACONDA_PREFIX}/bin/conda >/dev/null
then

 echo conda already installed
 {ANACONDA_PREFIX}/bin/conda update --yes conda
 echo Conda Updated

else
 echo conda doesnt exist
 # install conda

 if ! [ -e ./Anaconda-2.1.0-MacOSX-x86_64.sh ]
 then
  echo Downloading conda
  curl -LO http://09c8d0b2229f813c1b93-c95ac804525aac4b6dba79b00b39d1d3.r79.cf1.rackcdn.com/Anaconda-2.1.0-MacOSX-x86_64.sh
 fi

 chmod +x ./Anaconda-2.1.0-MacOSX-x86_64.sh
 echo Installing conda. This may take a few minutes. Please be patient
 ./Anaconda-2.1.0-MacOSX-x86_64.sh -b
 echo Conda Installed
 ${ANACONDA_PREFIX}/bin/conda update --yes conda
 echo Conda Updated
fi

#make root
if [ -d ${PYCHRONDATA_PREFIX} ]
then
    echo ${PYCHRONDATA_PREFIX} already exists
else
    echo Making root directory ${PYCHRONDATA_PREFIX}
    mkdir ${PYCHRONDATA_PREFIX}
    mkdir ${PYCHRONDATA_PREFIX}/.hidden
    mkdir ${PYCHRONDATA_PREFIX}/.hidden/updates
#    mkdir ${PYCHRONDATA_PREFIX}/setupfiles
    git clone ${URL} ${PYCHRONDATA_PREFIX}/.hidden/updates/pychron

    git clone ${SUPPORT_URL} ./tmp
    mv ./tmp/preferences .
    mv ./tmp/setupfiles .
    mv ./tmp/queue_conditionals .
    mv ./tmp/scripts .
    mv ./tmp/startup_tests.yaml .
    rm -rf ./tmp

fi

#update source
cd ${PYCHRONDATA_PREFIX}/.hidden/updates/pychron
git checkout ${BRANCH}
git pull

#install python dependencies
${ANACONDA_PREFIX}/bin/conda create --yes -n $CONDA_ENV python

#write the ENV file
EP=./launchers/ENV.txt
if [ -e ${EP} ]
then
 rm ${EP}
fi

cat <<EOT >> ${EP}
${CONDA_ENV}
${ANACONDA_PREFIX}
EOT

#write the requirements file
CREQ=./conda_requirements.txt
PREQ=./pip_requirements.txt
if [ -e ${CREQ} ]
then
 rm ${CREQ}
fi

if [ -e ${PREQ} ]
then
 rm ${PREQ}
fi

echo ${CONDA_REQ} >> ${CREQ}
echo ${PIP_REQ} >> ${PREQ}

cat ${CREQ}
cat ${PREQ}

${ANACONDA_PREFIX}/envs/${CONDA_ENV}/bin/conda install -n${CONDA_ENV} --yes --file ./conda_requirements.txt
${ANACONDA_PREFIX}/envs/${CONDA_ENV}/bin/pip install -r ./pip_requirements.txt

rm ${CREQ}
rm ${PREQ}

#build application
${ANACONDA_PREFIX}/envs/${CONDA_ENV}/bin/python ./app_utils/app_maker.py -A$APP_NAME -v$VERSION

#move application to Applications
if [ -e /Applications/py${APP_NAME}_${VERSION}.app ]
then
rm -rf /Applications/py${APP_NAME}_${VERSION}.app
fi
mv ./launchers/py${APP_NAME}_${VERSION}.app /Applications



#if type "autoconf" > /dev/null
#then
# echo autoconf already installed
#else
# if type "gcc" > /dev/null
# then
#    echo
#    echo
#    echo You need to install Xcode !!!!
#    #exit
# else
#     echo Downloading autoconf
#     # install autoconf
#     curl -OL http://ftpmirror.gnu.org/autoconf/autoconf-${AUTOCONF_VERSION}.tar.gz
#     tar xzf autoconf-${AUTOCONF_VERSION}.tar.gz
#     cd autoconf-${AUTOCONF_VERSION}
#     ./configure --prefix=/usr/local
#     make
#     make install
#     echo Autoconf Installed
# fi
#fi
#
#if type "git" > /dev/null
#then
# echo git already installed
#else
#    if type "gcc" > /dev/null
#     then
#        echo
#        echo
#        echo You need to install Xcode !!!!
#        exit
#     else
#         echo Downloading git
#         curl -LO https://github.com/git/git/archive/v${GIT_VERSION}.tar.gz
#         #curl -LO https://github.com/git/git/releases/tag/v${GIT_VERSION}
#         tar -xzf v${GIT_VERSION}.tar.gz
#         cd git-${GIT_VERSION}
#         make configure
#         ./configure --prefix=/usr/local
#         make
#         make install
#         echo Git Installed
#     fi
#fi
    #write boiler plate xml file
#    cat <<EOT >> ${PYCHRONDATA_PREFIX}/setupfiles/initialization.xml

#<root>
#  <globals>
#  </globals>
#  <plugins>
#    <general>
#      <plugin enabled="true">Database</plugin>
#      <plugin enabled="false">Geo</plugin>
#      <plugin enabled="false">Experiment</plugin>
#      <plugin enabled="true">Processing</plugin>
#      <plugin enabled="true">PyScript</plugin>
#      <plugin enabled="true">ArArConstants</plugin>
#      <plugin enabled="true">Entry</plugin>
#      <plugin enabled="false">SystemMonitor</plugin>
#    </general>
#    <hardware>
#    </hardware>
#    <data>
#    </data>
#    <social>
#      <plugin enabled="false">Email</plugin>
#      <plugin enabled="false">Twitter</plugin>
#    </social>
#  </plugins>
#</root>
#EOT