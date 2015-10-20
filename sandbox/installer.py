# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
import os
import subprocess
import shutil
# ============= local library imports  ==========================

'''
    example execution
        >>sudo python installer.py
        
        
    this script executes pychron installation 
    
    install EPD
    
    install uncertainties
    install pandas 0.8
    install statsmodels 0.4
    install pymysql
    
    move support files into place
'''


def main():
    if install_epd():
        return

    root = os.getcwd()

    print
    if install_python_package(root, 'uncertainties', '1.9'):
        return

    print
    if install_python_package(root, 'pandas', '0.8.1'):
        return

    print
    if install_python_package(root, 'statsmodels', '0.4.3'):
        return

    print
    if install_python_package(root, 'PyMySQL', 'master'):
        return

    if move_support_files(root):
        return


def move_support_files(root, version='processing'):
    home = os.path.expanduser('~')

    name = 'Pychrondata_{}'.format(version)
    dst = os.path.join(home, name)
    src = os.path.join(root, name)
    shutil.copytree(src, dst)


def install_python_package(root, name, version=None):
    if version:
        name = '{}-{}'.format(name, version)
    os.chdir(os.path.join(root, name))
    subprocess.call(['python', 'setup.py', 'install'])


# def change_gcc_version(version):
#    '''
#        change gcc version to 4.0
#    '''
#    gcc = '/usr/bin/gcc'
#    print 'changing {} symlink to use gcc version {}'.format(gcc, version)
#
#    os.remove(gcc)
#    gcc_v = '/usr/bin/gcc-{}'.format(version)
#    os.symlink(gcc_v, gcc)

def install_epd():
    print 'open epd installer'

    if user_cancel():
        return True


def user_cancel():
    '''
        returns True if user doesnt enter y
    '''
    _input = raw_input('hit "enter" to continue. "n" to cancel>> ')

    if _input.strip() == 'n':
        return True


if __name__ == '__main__':
    main()

# ============= EOF =============================================
