FROM continuumio/miniconda3
WORKDIR .

# setup conda and other dependencies
RUN apt-get update
RUN apt-get install -y libgl1-mesa-dev qtbase5-dev libxcb-xinerama0-dev build-essential
RUN conda create --name pychron3 python=3.8
SHELL ["conda", "run", "--name", "pychron3", "/bin/bash", "-c"]


RUN conda install --yes traits traitsui pyqt qt
RUN conda install --yes yaml pyyaml pymysql numpy importlib_resources apptools envisage gitpython
RUN conda install --yes cython pytables pyproj requests xlrd xlwt xlsxwriter lxml sqlalchemy=1.3 reportlab
RUN conda install --yes statsmodels scikit-learn
RUN conda install --yes swig=3
RUN conda install --yes pyparsing
RUN conda install -c dbanas chaco
RUN pip3 install uncertainties qimage2ndarray peakutils

# copy src
RUN git clone https://github.com/NMGRL/pychron
WORKDIR pychron
RUN git checkout dev/docker
WORKDIR ..

# copy setupfiles
RUN mkdir /home/Pychron
COPY ./app_utils/setupfiles /home/Pychron/setupfiles
COPY ./app_utils/preferences /home/Pychron/preferences
COPY ./app_utils/demo.sqlite /home/Pychron/demo.sqlite
COPY ./app_utils/.appdata /home/Pychron/.appdata

RUN mkdir /home/Pychron/data
RUN mkdir /home/Pychron/data/.dvc
RUN mkdir /home/Pychron/data/.dvc/repositories

RUN git clone https://github.com/PychronTrainingData/Irradiation-NM-313 /home/Pychron/data/.dvc/repositories/Irradiation-NM-313
RUN git clone https://github.com/PychronTrainingData/Morgan01099 /home/Pychron/data/.dvc/repositories/Morgan01099
RUN git clone https://github.com/PychronTrainingData/MetaData /home/Pychron/data/.dvc/MetaData

# setup environment
ENV QT_GRAPHICSSYSTEM="native"
ENV QT_DEBUG_PLUGINS=0
ENV PYTHONPATH=./pychron
ENV PYCHRON_APPNAME=pycrunch
ENV PYCHRON_ENV=/home/Pychron
ENV PYCHRON_USE_LOGIN=0

ENTRYPOINT ["conda", "run", "--no-capture-output", "--name", "pychron3", "python", "./pychron/launchers/launcher.py"]