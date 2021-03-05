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


def ask_config():
    info_header('Getting User Configuration')
    YES = ('y', 'yes', 'Y', 'Yes', 'YES')
    distro = os.path.join(HOME, 'anaconda3')

    def ask(cfg, key, msg):
        default = cfg[key]
        vv = input('{} [{}] >> '.format(msg, default))
        if not vv:
            vv = default
        cfg[key] = vv

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
              'install_gis_plugin': False
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
                'qimage2ndarray']
    pip_git_reqs = ['git+https://github.com/enthought/chaco.git#egg=chaco',
                    'git+https://github.com/enthought/enable.git#egg=enable']

    conda_reqs = ['numpy', 'statsmodels', 'scikit-learn', 'PyYAML', 'yaml', 'traits=5', 'traitsui=6', 'pyface=6',
                  'envisage', 'sqlalchemy', 'Reportlab', 'lxml', 'xlrd', 'xlwt', 'xlsxwriter', 'requests', 'keyring',
                  'pillow', 'gitpython', 'cython', 'pytables', 'pyproj', 'pymysql', 'certifi', 'jinja2', 'swig=3',
                  cfg['qt_bindings']]

    if IS_MAC:
        conda_reqs.append('python.app')

    if cfg['install_gis_plugin']:
        conda_reqs.append('qgis')

    cfg['pip_requirements'] = pip_reqs
    cfg['pip_git_requirements'] = pip_git_reqs
    cfg['conda_requirements'] = conda_reqs

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
    subprocess.call(['conda', 'create', '-n', env_name, '--yes', 'python=3.7'])

    # install deps
    subprocess.call(['conda', 'install', '--yes',
                     '--name', env_name] + cfg['conda_requirements'])

    if IS_MAC:
        subprocess.call(['conda', 'activate', env_name])
        # install pip deps
        # pip_path = os.path.join(cfg['conda_distro'], 'envs', env_name, 'bin', 'pip')
        pip_path = 'pip'
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
        txt = '''
call {conda_distro:}\\Scripts\\activate.bat {conda_distro:}\\envs\\{conda_env_name:}
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

set ROOT={pychron_path:}
set PYTHONPATH=%ROOT%

{conda_distro:}\\envs\\{conda_env_name:}\\python.exe %ROOT%\\launchers\\launcher.py
'''.format(**cfg)

    else:
        lpath = 'pychron_launcher.sh'
        txt = '''#!/bin/bash
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

{conda_distro:}/envs/{conda_env_name:}/bin/pythonw {pychron_path:}/launchers/launcher.py
'''.format(**cfg)

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


def install_setupfiles(cfg):
    root = os.path.join(HOME, cfg['pychron_data_dir'])

    for d in (root, os.path.join(root, 'setupfiles')):
        if not os.path.isdir(d):
            os.mkdir(d)
    p = os.path.join(root, 'setupfiles', 'initialization.xml')
    if not os.path.isfile(p):
        with open(p, 'w') as wfile:
            wfile.write('''<root>
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
        <hardware>
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
''')


def main():
    welcome()

    pre_checks()

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
