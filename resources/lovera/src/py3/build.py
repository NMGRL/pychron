#!/usr/bin/python
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
from os import path


# ============= local library imports  ==========================

def ifort_build(name, out):
    # subprocess.call(['touch', out])
    if path.isfile(name):
        subprocess.call(['Ifort', name, out, '-save'])
    else:
        print('invalid source file {}'.format(name))


def gfort_build(name, out):
    # subprocess.call(['touch', out])
    if path.isfile(name):
        subprocess.call(['gfortran', name, '-o', out])
        subprocess.call(['chmod', '+x', out])
    else:
        print('invalid source file {}'.format(name))


def build(names):
    # p = path.join(path.dirname(os.getcwd()), 'bin')
    # if not path.exists(p):
    #     os.mkdir(p)

    srcroot = os.path.abspath(os.path.dirname(__file__))
    root = os.path.join(os.path.dirname(srcroot), 'bin')
    if not os.path.isdir(root):
        os.mkdir(root)

    for f in names:
        out = '{}_py3'.format(f)
        out = os.path.join(root, out)
        #
        f = os.path.join(srcroot, f)
        f = '{}_py.f90'.format(f)
        print('src:     ', f)
        print('building:', out)

        gfort_build(f, out)


def main(args):
    names = ['files',
             'autoarr',
             'autoage-mon',
             'arrmulti',
             # 'autoage-free',
             'conf_int',
             'corrfft',
             'agesme',
             'arrme']

    build(names, )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Build MDD fortran source')
    parser.add_argument('-p', '--pychron',
                        action='store_true',
                        default=False,
                        help='build binaries with _py extension')
    args = parser.parse_args()

    main(args)

# ============= EOF =============================================
