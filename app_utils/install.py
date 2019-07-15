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

    def ask(cfg, key, msg, default):
        v = input('{} [{}] >> '.format(msg, default))
        if not v:
            v = default
        cfg[key] = v

    config = {}
    ask(config, 'github_org', 'Github organization', 'NMGRL')
    ask(config, 'github_user', 'Github user name', 'nmgrluser')
    ask(config, 'github_pwd', 'Github password', '')
    ask(config, 'massspec_db_version', 'MassSpec Database Version', 16)
    ask(config, 'fork', 'Pychron Fork', 'NMGRL')
    ask(config, 'branch', 'Pychron Branch', 'develop')
    ask(config, 'app_name', 'Pychron Style', 'pyexperiment')
    ask(config, 'qt_bindings', 'Qt Bindings', 'pyqt')

    config['mac_os_app'] = False
    if IS_MAC:
        ask(config, 'mac_os_app', 'Make a Mac OS application', 'yes')
        if config['mac_os_app'] in ('y', 'yes'):
            config['mac_os_app'] = True
            ask(config, 'mac_app_name', 'Application name', 'Pychron')

    ask(config, 'app_id', 'Application ID', 0)
    ask(config, 'pychron_data_dir', 'Pychron Data directory', 'Pychron')

    distro = os.path.join(HOME, 'anaconda3')
    ask(config, 'conda_distro', 'Conda Distro Path', distro)
    ask(config, 'conda_env_name', 'Conda environment name', 'pychron3')

    # echo config
    print('------------ Config -------------')
    for k, v in config.items():
        print('{:<20s}: {}'.format(k, v))

    config['pip_requirements'] = 'uncertainties peakutils qimage2ndarray chaco'
    creq = 'qt numpy statsmodels scikit-learn PyYAML yaml traitsui=6.0.0 envisage sqlalchemy ' \
           'Reportlab lxml xlrd xlwt xlsxwriter requests keyring pillow gitpython cython pytables ' \
           'pymysql certifi jinja2 swig {}'.format(config['qt_bindings'])
    if IS_MAC:
        creq = '{}\npython.app'.format(creq)

    config['conda_requirements'] = creq

    print()
    print()
    if yes('Continue? [y]/n >> '):
        return config


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


    subprocess.call([GIT, 'clone', url,
                     '--branch={}'.format(cfg['branch']),
                     ppath])


def install_conda(cfg):
    info_header('Install Conda Environment')

    # update base conda
    subprocess.call(['conda', 'update', '-n', 'base', '--yes', 'conda'])

    # create env
    env_name = cfg['conda_env_name']
    subprocess.call(['conda', 'create', '-n', env_name, '--yes', 'python=3.5'])
    # subprocess.call(['conda', 'activate', cfg['conda_env_name']])

    # install deps
    subprocess.call(['conda', 'install', '--yes',
                     '--name', env_name] + cfg['conda_requirements'].split(' '))

    # install pip deps
    pip_path = os.path.join(cfg['conda_distro'], 'envs', env_name, 'bin', 'pip')
    subprocess.call([pip_path, 'install'] +cfg['pip_requirements'].split(' '))


def install_launcher_script(cfg):
    info_header('Build launcher script')
    if IS_WINDOWS:
        lpath = 'pychron_launcher.bat'
        txt = '''
set GITHUB_ORGANIZATION={github_org:}
set GITHUB_USER={github_user:}
set GITHUB_PASSWORD={github_pwd:}
set MassSpecDBVersion={massspec_db_version:}
set CONDA_ENV={conda_env_name:}
set CONDA_DISTRO={conda_distro:}
set PYCHRON_APPNAME={app_name:}
set APPLICATION_ID={app_id:}
set QT_API={qt_bindings:}

ROOT=%{pychron_path:}%
set PYTHONPATH=%ROOT%

{conda_distro:}\\envs\\{conda_env:}\\python %ROOT%\\launchers\\launcher.py
'''.format(**cfg)

    else:
        lpath = 'pychron_launcher.sh'
        txt = '''#!/bin/bash
export GITHUB_ORGANIZATION={github_org:}
export GITHUB_USER={github_user:}
export GITHUB_PASSWORD={github_pwd:}
export MassSpecDBVersion={massspec_db_version:}
export CONDA_ENV={conda_env_name:}
export CONDA_DISTRO={conda_distro:}
export PYCHRON_APPNAME={app_name:}
export APPLICATION_ID={app_id:}
export QT_API={qt_bindings:}

ROOT=${pychron_path:}
export PYTHONPATH=$ROOT

{conda_distro:}/envs/{conda_env_name:}/bin/pythonw $ROOT/launchers/launcher.py
'''.format(**cfg)

    with open(lpath, 'w') as wfile:
        wfile.write(txt)

    cfg['launcher'] = lpath


def install_app(cfg):
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


def main():
    welcome()

    pre_checks()

    cfg = ask_config()
    if cfg:
        install_src(cfg)
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
