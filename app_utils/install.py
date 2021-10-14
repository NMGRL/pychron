# ===============================================================================
# Copyright 2019 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os
import platform
import shutil
import subprocess
import sys

IS_MAC = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'

INITIALIZATION_TXT = '''<root>
    <globals>
    </globals>
    <plugins>
        <general>
            <plugin enabled="false">CanvasDesigner</plugin>
            <plugin enabled="true">PyScript</plugin>
            <plugin enabled="false">Video</plugin>
            <plugin enabled="false">Database</plugin>
            <plugin enabled="true">Entry</plugin>
            <plugin enabled="false">SystemMonitor</plugin>
            <plugin enabled="true">ArArConstants</plugin>
            <plugin enabled="false">Loading</plugin>
            <plugin enabled="false">LabBook</plugin>
            <plugin enabled="false">DashboardServer</plugin>
            <plugin enabled="false">DashboardClient</plugin>
            <plugin enabled="true">Pipeline</plugin>
            <plugin enabled="false">Geochron</plugin>
            <plugin enabled="false">MediaStorage</plugin>
            <plugin enabled="true">Update</plugin>
            <plugin enabled="true">DVC</plugin>
            <plugin enabled="false">MassSpec</plugin>
            <plugin enabled="false">IGSN</plugin>
            <plugin enabled="true">GitHub</plugin>
            <plugin enabled="false">MachineLearning</plugin>
            <plugin enabled="false">Image</plugin>
            <plugin enabled="false">RemoteExperiment</plugin>
            <plugin enabled="false">Experiment</plugin>
            <plugin enabled="false">LabspyClient</plugin>
            <plugin enabled="false">Classifier</plugin>
            <plugin enabled="false">Auto</plugin>
            <plugin enabled="false">MDD</plugin>
            <plugin enabled="false">Query</plugin>
            <plugin enabled="false">GitLab</plugin>
        </general>
        <hardware>{}
        </hardware>
        <social>
        </social>
        <data>
            <plugin enabled="false">USGSVSCData</plugin>
            <plugin enabled="false">WiscArData</plugin>
            <plugin enabled="false">Sparrow</plugin>
        </data>
    </plugins>
</root>
'''

HARDWARE_PLUGIN_TXT = """
            <plugin enabled="true">ExtractionLine
                <manager enabled="true">switch_manager
                <device enabled="true">switch_controller</device>
                </manager>
            </plugin>"""

DEFAULTS_TXT = '''#script defaults file
#defines default pyscripts for the analysis types
#this yaml file returns a dictionary of dictionaries
#.py does not have to be included for graphic clarity.
Bg:
 extraction: 
 measurement: 
 post_equilibration:
 post_measurement: 
Ba:
 extraction: air_x1
 measurement: air
 post_equilibration: pump_air
 post_measurement: pump_ms
Bc:
 extraction: cocktail_x1
 measurement: air
 post_equilibration: pump_air
 post_measurement: pump_ms
Bu:
 extraction:
 measurement: background
 post_equilibration: pump_unknown
 post_measurement: pump_ms
A:
 extraction: air_x1
 measurement: air
 post_equilibration: pump_air
 post_measurement: pump_ms
C:
 extraction: cocktail_x1
 measurement: background
 post_equilibration: pump_air
 post_measurement: pump_ms
U:
 extraction:
 measurement: unknown
 post_equilibration: pump_unknown
 post_measurement: pump_ms
 options: unknown
 FusionsCO2:
  cleanup: 10
  duration: 200
  extract_value: 1.28
  extract_units: watts
  beam_diameter: 1.2
 FusionsDiode:
  cleanup: 100
  duration: 20
  extract_value: 0.28
  extract_units: watts
  beam_diameter: 1.3
Pa:
 extraction: pause
 measurement:
 post_equilibration:
 post_measurement:
Dg:
 extraction: degas
 measurement:
 post_equilibration:
 post_measurement:
 extract_value: 0.28
 extract_units: watts
'''

SYSTEM_MONITOR_TXT = '''[General]
sample_delay=60
'''

MEASUREMENT_TXT = """
#!Measurement
'''
baseline:
  after: true
  before: false
  counts: 3
  detector: H1
  mass: 39.59
default_fits: nominal
equilibration:
  eqtime: 5
  inlet: R
  inlet_delay: 3
  outlet: S
  use_extraction_eqtime: false
multicollect:
  counts: 5
  detector: H1
  isotope: Ar40
peakcenter:
  after: false
  before: false
  detector: H1
  isotope: Ar40
peakhop:
  hops_name: hop
  use_peak_hop: true

'''


def main():
    #this is a comment
    '''
        this is a multiline
        comment aka docstring
    '''
    #display information with info(msg)
    info('unknown measurement script')

    #set the spectrometer parameters
    #provide a value
    set_source_parameters(YSymmetry=10)

    #or leave blank and values are loaded from a config file (setupfiles/spectrometer/config.cfg)
    set_source_optics()

    #set the cdd operating voltage
    set_cdd_operating_voltage(100)

    if mx.peakcenter.before:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)

    #open a plot panel for this detectors
    ACTIVE_DETECTORS=('H2','H1','AX','L1','L2', 'CDD')
    activate_detectors(*ACTIVE_DETECTORS)

    if mx.baseline.before:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector)


    #position mass spectrometer
    position_magnet(mx.multicollect.isotope, detector=mx.multicollect.detector)

    #gas is staged behind inlet

    #post equilibration script triggered after eqtime elapsed
    #equilibrate is non blocking
    #so use either a sniff of sleep as a placeholder until eq finished
    if mx.equilibration.use_extraction_eqtime:
        e = ex.eqtime
    else:
        e = mx.equilibration.eqtime

    equilibrate(eqtime=e, inlet=mx.equilibration.inlet, outlet=mx.equilibration.outlet)

    #equilibrate returns immediately after the inlet opens
    set_time_zero()

    sniff(e)
    #set default regression
    set_fits()
    set_baseline_fits()
    
    #multicollect on active detectors
    multicollect(ncounts=mx.multicollect.counts, integration_time=1)

    if mx.baseline.after:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector)

    if mx.peakcenter.after:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)
    info('finished measure script')

#========================EOF==============================================================
"""

EXTRACTION_TXT = """
def main():
    info('this is a info messeage')
    
    #this is a comment
    
    # the following is used to open a valve
    open('A')
    
    # can also open by description
    open(description='MS Inlet')
    
    # delay n seconds
    sleep(10)
    
    # close the valve
    close('A')

"""

PROCEDURE_TXT = """
def main():
    # This is a procedure. Most extraction script functions are available. 
    # the main exception is that a procedure CANNOT be used to interact with an extraction device such as a laser
    
    info('this is a test procedure')
    info('cycle valve 5 times delay 3 seconds between open and close
    
    for i in range(10):
        sleep(3)
        if i%2:
            open('A')
        else:
            close('A')
        
"""

CANVAS_XML = """<?xml version="1.0" ?>
<root>
    <!-- Spectrometer -->
    <spectrometer>Spec
        <translation>-24,0</translation><dimension>8,8</dimension><color>85,110,180</color>
    </spectrometer>
    
    <!-- Valves -->
    <valve>A
        <translation>-23,-3</translation>
    </valve>
    <valve>B
        <translation>-14,3</translation>
    </valve>
    
    <!-- pump -->
    <ionpump>IonPump
        <translation>-24,-8</translation><dimension>8,3</dimension><color>234,165,57</color>
    </ionpump>

    <!-- connections -->
    <connection orientation="vertical"><start>A</start><end>Spec</end></connection>
    <connection orientation="vertical"><start>A</start><end>IonPump</end></connection>
    <connection orientation="horizontal"><start>B</start><end>Spec</end></connection>
</root>
"""

CANVAS_TXT = """connection: []
getter: []
hconnection:
  - end:
      name: 'Spec'
      offset: ''
    start:
      name: 'B'
      offset: ''
ionpump:
  - name: IonPump
    color: 234,165,57
    dimension: 8,3
    translation: -24.0,-8
laser: []
manualswitch: []
spectrometer:
  - name: Spec
    border_width: 5
    color: 250,120,150,255
    dimension: 10.0, 10.0
    translation: -25.0,0.0
stage: []
switch: []
turbo:
- color: 250,250,0,255
  dimension: 4.0, 4.0
  translation: -11.0,-28.0
  name: Turbo
valve:
  - name: 'A'
    translation: -23, -3
  - name: 'B'
    translation: -14, 3
vconnection: 
  - start: 
      name: A
    end: 
      name: Spec
  - start:
      name: A
    end:
      name: IonPump
"""
CANVAS_CONFIG_TXT = """<root>
    <origin>0,0</origin>
    <xview>-28,28</xview>
    <yview>-25,25</yview>
    <color tag="bgcolor">lightblue</color>
    <color tag="gauge">255,255,0</color>
    <color tag="getter">94,87,94</color>
    <color tag="label">167, 201, 166</color>
</root>

"""
SWITCHES_TXT = """- name: 0
  address: 0
  description: Ion Pump
- name: 1
  address: 1
  description: QMS
- name: 2
  address: 2
  description: Getter
- name: 3
  address: 3
  description: Turbo
- name: 4
  address: 4
  description: Planchet
- name: 5
  address: 5
  description: DiffCell
- name: 6
  address: 6
  description: 4HeLine
- name: 7
  address: 7
  description: 4HeTank
- name: 8
  address: 8
  description: 3HeLine
- name: 9
  address: 9
  description: 3HeTank
- name: 10
  address: 10
  description: Foreline
- name: 11
  address: 11
  description: Shroud
"""
STARTUP_TXT = """- plugin: MassSpec
  tests: []
- plugin: ArArConstants
  tests: []
- plugin: ArgusSpectrometer
  tests:
  - test_communication
  - test_intensity
- plugin: ClientExtractionLine
  tests: []
- plugin: DVC
  tests:
  - test_database
  - test_dvc_fetch_meta
- plugin: GitHub
  tests:
  - test_api
- plugin: Experiment
  tests: []
- plugin: PyScript
  tests: []
- plugin: Pipeline
  tests: []
- plugin: Entry
  tests: []
- plugin: LabspyClient
  tests: []
- plugin: Update
  tests: []
- plugin: Email
  tests: []
- plugin: FusionsCO2
  tests:
  - test_communication
"""

EXPERIMENT_DEFAULTS = """columns:
  - Labnumber
  - Aliquot
  - Sample
  - Position
  - Extract
  - Units
  - Duration (s)
  - Cleanup (s)
  - Beam (mm)
  - Pattern
  - Extraction
  - Measurement
  - Conditionals
  - Comment

"""

LAUNCHER_SH = """#!/bin/bash
export GITHUB_ORGANIZATION={github_org:}
export GITHUB_TOKEN={github_token:}
export MassSpecDBVersion={massspec_db_version:}
export CONDA_ENV={conda_env_name:}
export CONDA_DISTRO={conda_distro:}
export APPLICATION_ID={app_id:}
export QT_API={qt_api:}

export PYCHRON_APPNAME={app_name:}
export PYCHRON_DATABASE_UPDATE={update_db:}
export PYCHRON_ALEMBIC_URL={alembic_url:}
export PYCHRON_USE_LOGIN=0

export PYTHONPATH={pychron_path:}

{conda_distro:}/envs/{conda_env_name:}/bin/pythonw {pychron_path:}/launchers/launcher.py"""

LAUNCHER_BAT = """call {conda_distro:}\\Scripts\\activate.bat {conda_distro:}\\envs\\{conda_env_name:}
set GITHUB_ORGANIZATION={github_org:}
set GITHUB_TOKEN={github_token:}
set MassSpecDBVersion={massspec_db_version:}
set CONDA_ENV={conda_env_name:}
set CONDA_DISTRO={conda_distro:}
set APPLICATION_ID={app_id:}
set QT_API={qt_api:}

set PYCHRON_APPNAME={app_name:}
set PYCHRON_DATABASE_UPDATE={update_db:}
set PYCHRON_ALEMBIC_URL={alembic_url:}
export PYCHRON_USE_LOGIN=0


set PYTHONPATH={pychron_path:}

{conda_distro:}\\envs\\{conda_env_name:}\\python.exe {pychron_path:}\\launchers\\launcher.py
"""

# =========== Default Preferences
EXTRACTION_LINE_PREFERENCES = """
[pychron.extraction_line]
use_hardware_update = True
hardware_update_period = 3.0
canvas_path = {canvas_path:}
canvas_config_path = {canvas_config_path:}
valves_path = {valves_path:}
"""

if IS_WINDOWS:
    GIT = 'C:\\Git\\bin\\git'
else:
    GIT = 'git'

HOME = os.path.expanduser('~')


def info_header(msg):
    print('========== {} =========='.format(msg))


def critical(msg):
    print('********** {} **********'.format(msg))


def welcome():
    msg = r'''
  _______     _______ _    _ _____   ____  _   _
 |  __ \ \   / / ____| |  | |  __ \ / __ \| \ | |
 | |__) \ \_/ / |    | |__| | |__) | |  | |  \| |
 |  ___/ \   /| |    |  __  |  _  /| |  | | . ` |
 | |      | | | |____| |  | | | \ \| |__| | |\  |
 |_|      |_|  \_____|_|  |_|_|  \_\\____/|_| \_|


Developer: Jake Ross (NMT)
Date: 10-02-2016
Updated: 7-10-2019
---*---*---*---*---*---*---*---*---*---*---*---*
Welcome to the Pychron Installer.

Hit "Enter" to continue

---*---*---*---*---*---*---*---*---*---*---*---*'''
    print(msg)
    input()

    msg = '''You will be asked to provide a series of configuration values. Each value has as default value, indicated in square
brackets e.g., [default]

To except the default value hit "Enter" when prompted


!!!WARNING!!!
This installer is beta and not guaranteed to work. USE WITH CAUTION

Hit "Enter" to continue'''
    print(msg)
    input()


def pre_checks():
    info_header('Pre Checks')
    if IS_MAC:
        if which('git'):
            print('Found: Git')
        else:
            critical('Git is Required. Please install manually')
            sys.exit(1)

        if which('conda'):
            print('Found: Conda')
        else:
            critical('Conda is Required. Please install manually')
            sys.exit(1)

        if which('gcc'):
            print('Found: XCode Commandline tools')
        else:
            print('XCode Commandline tools required')
            subprocess.call(['xcode-select', '--install'])


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file


def install_conda_only():
    info_header('Install conda env only')
    cfg = {'qt_bindings': 'pyqt=5',
           'qt_api': 'pyqt5',
           'conda_distro': os.path.join(os.path.expanduser('~'), 'miniconda3'),
           'conda_env_name': 'pychron3gis',
           'python_version': '3.9'}
    vv = input('Install conda env only [n]')
    if vv.lower() in ('y', 'yes'):
        ask(cfg, 'conda_distro', 'Conda Distro Path')
        ask(cfg, 'conda_env_name', 'Conda environment name')
        ask(cfg, 'install_gis_plugin', 'Install GIS Plugin')
        build_requirements(cfg)
        return cfg


def install_setupfiles_only():
    info_header('Install Setupfiles only')
    cfg = {}
    vv = input('Install setup files only [n]')
    if vv.lower() in ('y', 'yes'):
        cfg['install_exp_setupfiles'] = True
        cfg['pychron_data_dir'] = 'PychronUF'
        cfg['include_hardware_plugins'] = True

    return cfg


def ask(cfg, key, msg):
    default = cfg.get(key, '')
    vv = input('{} [{}] >> '.format(msg, default))
    if not vv:
        vv = default
    cfg[key] = vv


def ask_config():
    info_header('Getting User Configuration')
    YES = ('y', 'yes', 'Y', 'Yes', 'YES')
    distro = os.path.join(HOME, 'opt', 'miniconda3')

    config = {'github_org': 'NMGRL',
              'github_token': '',
              'massspec_db_version': 16,
              'fork': 'NMGRL',
              'branch': 'dev/dr',
              'app_name': 'pycrunch',
              'qt_bindings': 'pyqt=5',
              'qt_api': 'pyqt5',
              'use_all_defaults': 'no',
              'mac_os_app': False,
              'mac_app_name': 'Pychron',
              'app_id': 0,
              'pychron_data_dir': 'Pychron',
              'conda_distro': distro,
              'conda_env_name': 'pychron3',
              'update_db': 0,
              'alembic_url': 'mysql+pymysql://<user>:<pwd>@<host>/<db>',
              'install_gis_plugin': False,
              'install_exp_setupfiles': False,
              'include_hardware_plugins': False
              }

    ask(config, 'use_all_defaults', 'Use all defaults')
    if config['use_all_defaults'] not in YES:
        ask(config, 'github_org', 'Github organization')
        ask(config, 'github_token', 'Github token')
        ask(config, 'massspec_db_version', 'MassSpec Database Version')
        ask(config, 'fork', 'Pychron Fork')
        ask(config, 'branch', 'Pychron Branch')
        ask(config, 'app_name', 'Pychron Style')
        # ask(config, 'qt_bindings', 'Qt Bindings')

        if IS_MAC:
            ask(config, 'mac_os_app', 'Make a Mac OS application')
            if config['mac_os_app'] in YES:
                config['mac_os_app'] = True
                ask(config, 'mac_app_name', 'Application name')

        ask(config, 'app_id', 'Application ID')
        ask(config, 'pychron_data_dir', 'Pychron directory')
        ask(config, 'conda_distro', 'Conda Distro Path')
        ask(config, 'conda_env_name', 'Conda environment name')
        ask(config, 'update_db', 'Update Database automatically')
        ask(config, 'install_gis_plugin', 'Install GIS Plugin')
        ask(config, 'install_exp_setupfiles', 'Install Experiment setupfiles')
        if config['update_db'] in YES:
            ask(config, 'alembic_url', 'Database URL')
        else:
            config['alembic_url'] = ''

    # echo config
    print('------------ Config -------------')
    for k, v in config.items():
        print('{:<20s}: {}'.format(k, v))

    build_requirements(config)

    print()
    print()
    if yes('Continue? [y]/n >> '):
        return config


def build_requirements(cfg):
    pip_reqs = ['uncertainties',
                'peakutils',
                'qimage2ndarray',
                'chaco']

    # pip_git_reqs =  ['git+https://github.com/enthought/chaco.git#egg=chaco',
    #                 'git+https://github.com/enthought/enable.git#egg=enable']
    pip_git_reqs = []

    conda_reqs = ['numpy', 'statsmodels', 'scikit-learn', 'PyYAML', 'yaml', 'traits', 'traitsui', 'pyface',
                  'envisage', 'sqlalchemy', 'Reportlab', 'lxml', 'xlrd', 'xlwt', 'xlsxwriter', 'requests', 'keyring',
                  'pyparsing', 'pillow', 'gitpython', 'pytables', 'pyproj', 'pymysql', 'certifi', 'jinja2', 'swig=3',
                  'cython',
                  'importlib_resources', cfg['qt_bindings']]

    if IS_MAC:
        conda_reqs.append('python.app')

    if cfg['install_gis_plugin']:
        conda_reqs.append('qgis')
        # conda_reqs.append('qtkeychain=0.11.1')

    cfg['pip_requirements'] = pip_reqs
    cfg['pip_git_requirements'] = pip_git_reqs
    cfg['conda_requirements'] = conda_reqs

    print('=========Conda Reqs==============')
    print(' '.join(conda_reqs))
    print('=================================')
    print('=========PIP Reqs================')
    print(' '.join(pip_reqs))
    print('=================================')


# config['pip_requirements'] = 'uncertainties peakutils qimage2ndarray'
# config['pip_git_requirements'] =
#
# creq = 'pip qt numpy statsmodels scikit-learn PyYAML yaml traits=5 traitsui=6 pyface=6 envisage sqlalchemy ' \
#        'Reportlab lxml xlrd xlwt xlsxwriter requests keyring pillow gitpython cython pytables ' \
#         'pyproj pymysql certifi jinja2 swig=3 {}'.format(config['qt_bindings'])
#
# if IS_MAC:
#     creq = '{} python.app'.format(creq)
#
# if config['install_gis_plugin']:
#     creq = '{} '.format('qgis')

# config['conda_requirements'] = creq

def yes(msg):
    return input(msg) in ('', 'y', 'yes', 'Yes', 'YES')


def install_src(cfg):
    info_header('Install Pychron Source Code')
    update_root = os.path.join(HOME, '.pychron.{}'.format(cfg['app_id']))
    ppath = os.path.join(update_root, 'pychron')

    if not os.path.isdir(update_root):
        os.mkdir(update_root)

    cfg['update_root'] = update_root
    cfg['pychron_path'] = ppath

    if os.path.isdir(ppath):
        if not yes('Pychron source code already exists. Remove and re-clone'):
            return

        shutil.rmtree(ppath)

    url = 'https://github.com/{}/pychron.git'.format(cfg['fork'])

    try:
        subprocess.call([GIT, 'clone', url,
                         '--branch={}'.format(cfg['branch']),
                         ppath])

    except BaseException:
        subprocess.call(['git', 'clone', url,
                         '--branch={}'.format(cfg['branch']),
                         ppath])


def install_conda(cfg):
    info_header('Install Conda Environment')

    # update base conda
    subprocess.call(['conda', 'update', '-n', 'base', '--yes', 'conda'])

    # create env
    env_name = cfg['conda_env_name']
    subprocess.call(['conda', 'create', '-n', env_name, '--yes', 'python={}'.format(cfg['python_version'])])

    # install deps
    # subprocess.call(['conda', 'create','--name', env_name, '--yes',
    #                  'python=3.8'] + cfg['conda_requirements'])
    subprocess.call(['conda', 'install', '--yes', '--name', env_name]+cfg['conda_requirements'])
    # subprocess.call(['conda', 'install', '--yes',
    #                  '--name', env_name, '-c', 'dbanas', 'chaco'])
    if IS_MAC:
        # subprocess.call(['conda', 'activate', env_name])
        # install pip deps
        pip_path = os.path.join(cfg['conda_distro'], 'envs', env_name, 'bin', 'pip')
        # pip_path = 'pip'
        subprocess.call([pip_path, 'install'] + cfg['pip_requirements'])
        for r in cfg['pip_git_requirements']:
            subprocess.call([pip_path, 'install', '-e', r])
    else:
        print('WARNING!!!! Installing PIP dependencies on Windows currently not available. Please consult Pychron '
              'documentation or contact Pychron Labs for further instructions')


def install_launcher_script(cfg):
    info_header('Build launcher script')
    if IS_WINDOWS:
        lpath = 'pychron_launcher.bat'
        txt = LAUNCHER_BAT.format(**cfg)

    else:
        lpath = 'pychron_launcher.sh'
        txt = LAUNCHER_SH.format(**cfg)

    with open(lpath, 'w') as wfile:
        wfile.write(txt)

    cfg['launcher'] = lpath


def install_app(cfg):
    if IS_MAC:
        info_header('Install App')
        l = cfg['launcher']
        if cfg['mac_os_app']:
            d = os.path.join('{}.app'.format(cfg['mac_app_name']), 'Contents', 'MacOS')
            subprocess.call(['mkdir', '-p', d])
            dst = os.path.join(d, cfg['mac_app_name'])
            shutil.copy(l, dst)
            subprocess.call(['chmod', '+x', dst])

        else:
            subprocess.call(['chmod', '+x', l])
            shutil.move(l, os.path.join(HOME, 'Desktop', l))


def get_hardware_plugins(cfg):
    t = ''
    if cfg['include_hardware_plugins']:
        t = HARDWARE_PLUGIN_TXT
    return t


def install_setupfiles(cfg):
    root = os.path.join(HOME, cfg['pychron_data_dir'])

    def make_dir(name):
        for d in (root, os.path.join(root, name)):
            if not os.path.isdir(d):
                os.mkdir(d)

    def write(p, t):
        if not os.path.isfile(p):
            with open(p, 'w') as wfile:
                wfile.write(t)

    setupfiles = 'setupfiles'
    make_dir(setupfiles)

    p = os.path.join(root, setupfiles, 'initialization.xml')
    v = INITIALIZATION_TXT.format(get_hardware_plugins(cfg))
    write(p, v)

    if cfg['install_exp_setupfiles']:
        p = os.path.join(root, setupfiles, 'startup_tests.yaml')
        write(p, STARTUP_TXT)

        p = os.path.join(root, setupfiles, 'experiment_defaults.yaml')
        write(p, EXPERIMENT_DEFAULTS)

        # Scripts
        scripts = 'scripts'
        make_dir(scripts)
        p = os.path.join(root, scripts, 'defaults.yaml')
        write(p, DEFAULTS_TXT)

        measurement_args = 'measurement', 'unknown', MEASUREMENT_TXT
        extraction_args = 'extraction', 'extraction', EXTRACTION_TXT
        procedure_args = 'procedures', 'procedure', PROCEDURE_TXT

        for name, filename, txt in (measurement_args, extraction_args, procedure_args):
            d = os.path.join(scripts, name)
            make_dir(d)
            p = os.path.join(root, d, 'example_{}.py'.format(filename))
            write(p, txt)

        # Canvas
        canvas = os.path.join('setupfiles', 'canvas2D')
        make_dir(canvas)
        canvas_path = os.path.join(root, canvas, 'canvas.yaml')
        write(canvas_path, CANVAS_TXT)
        p = os.path.join(root, canvas, 'canvas.xml')
        write(p, CANVAS_XML)

        canvas_config_path = os.path.join(root, canvas, 'canvas_config.xml')
        write(canvas_config_path, CANVAS_CONFIG_TXT)
        p = os.path.join(root, canvas, 'alt_config.xml')
        write(p, CANVAS_CONFIG_TXT)

        # Extraction line
        el = os.path.join('setupfiles', 'extractionline')
        make_dir(el)
        valves_path = os.path.join(root, el, 'valves.yaml')
        write(valves_path, SWITCHES_TXT)

        # Monitors
        monitors = os.path.join(setupfiles, 'monitors')
        d = os.path.join(root, monitors)
        make_dir(d)

        p = os.path.join(d, 'system_monitor.cfg')
        write(p, SYSTEM_MONITOR_TXT)

        # Make preferences

        v = EXTRACTION_LINE_PREFERENCES.format(canvas_path=canvas_path,
                                               canvas_config_path=canvas_config_path,
                                               valves_path=valves_path)
        d = os.path.join(root, 'preferences')
        make_dir(d)
        p = os.path.join(d, 'extractionline.ini')
        write(p, v)


def main():
    welcome()

    pre_checks()
    cfg = install_setupfiles_only()
    if cfg:
        install_setupfiles(cfg)
    else:
        cfg = install_conda_only()
        if cfg:
            install_conda(cfg)
        else:
            cfg = ask_config()
            if cfg:
                install_src(cfg)
                install_setupfiles(cfg)
                install_conda(cfg)
                install_launcher_script(cfg)
                install_app(cfg)

                print()
                print('Installation Complete!')
            else:
                print('Failed getting configuration. Exiting')


if __name__ == '__main__':
    main()
# ============= EOF =============================================
