CONDAENV=pychron3

conda install -y -n $CONDAENV --file ./requirements/basic_requirements.txt
conda install -y -n $CONDAENV pyqt=4
~/anaconda/envs/$CONDAENV/bin/pip install -r ./requirements/basic_pip_requirements.txt

APP=valve

if [ $APP=valve ]
then
    conda install -y -n pychron3 pyserial twisted pyzmq
fi