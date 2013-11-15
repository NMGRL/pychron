#===============================================================================
# Copyright 2011 Jake Ross
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
#===============================================================================



import os
from setuptools import setup, find_packages

AUTHOR = 'Jake Ross'
AUTHOR_EMAIL = 'jirhiker@gmail.com'
DESCRIPTION = 'Extraction Line Controller'
LICENSE = 'GNU'
URL = 'http://code.google.com/p/arlab'

def readtxt(fname):
    root = os.path.dirname(__file__)
    return open(os.path.join(root, fname)).read()

def read_version_file():
    root = os.getcwd()
    p = os.path.join(root, 'version_info.txt')
    with open(p, 'r') as f:
        lines = [l.strip() for l in f]
    return lines

def get_version():
    lines = read_version_file()
    major = lines[1].split('=')[1]
    minor = lines[2].split('=')[1]
    return '.'.join((major, minor))

def get_name():
    lines = read_version_file()
    return lines[0]

def get_top_level_modules():
    return ['pychron_beta', 'remote_hardware_server']

def get_data_files():
    home = os.path.expanduser('~')
    dsthome = os.path.join(home, 'pychron_data_beta')

    data = os.path.join(os.getcwd(), 'data')
    fss = []
    for root, _dirs, files in os.walk(data):

        try:
            ri = root.split('data/')[1]
        except IndexError:
            continue

        dst = os.path.join(dsthome, ri)

        # filter out hidden files
        fs = [os.path.join('data', os.path.basename(root), f)
             for f in files
                if not f.startswith('.')]
        if fs:
            fss.append((dst, fs))

    return fss
# python setup.py sdist adds everything under version control
setup(

    packages=find_packages(),
    py_modules=get_top_level_modules(),

    data_files=get_data_files(),
    # info
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=readtxt('README'),
    license=LICENSE,
    url=URL,
    name=get_name(),
    version=get_version()
    )


