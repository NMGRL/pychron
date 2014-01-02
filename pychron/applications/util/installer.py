#===============================================================================
# Copyright 2014 Jake Ross
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

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
import buildtools
import os
import subprocess
import imp

import MacOS
from pychron.applications.util.builder import Builder


def install(name):
    """
        make Pychrondata
        make .hidden
        clone git repo to .hidden/updates
        install dependencies
        build pychron
        move application to Applications

        valid names:
            pyexperiment
    """

    #setup application directory
    p = os.path.join(os.path.expanduser('~'), 'Pychrondata_install')
    wd = os.path.join(p, 'hidden', 'updates')
    #clone src code
    url = 'https://github.com/NMGRL/pychron.git'

    if not os.path.isdir(p):
        # #backup the previous version
        # ct = datetime.now().strftime('%m-%d-%y')
        # dst='{}-{}'.format(p, ct)
        # if os.path.isdir(dst):
        #     shutil.rmtree(dst)
        #
        # os.rename(p, dst)

        os.mkdir(p)
        os.mkdir(os.path.join(p, 'hidden'))
        # os.mkdir(wd)
        os.chdir(wd)
        subprocess.call(['git', 'clone', url])
    else:
        os.chdir(wd)
        subprocess.call(['git', 'pull'])

    # subprocess.Popen(['git', 'clone', url, wd])
    #install dependencies using pip
    # install_dependencies(wd)
    #
    #build
    build_pychron(wd, name)

def build_pychron(wd, name):
    filename = os.path.join(wd, 'launchers', '{}.py'.format(name))
    build_app(filename)

    builder = Builder()
    builder.launcher_name = name
    builder.root = wd

    ver = imp.new_module('ver')
    v = open(os.path.join(wd, 'pychron', 'version.py')).read()
    exec v in ver.__dict__
    builder.version=ver.__version__
    builder.run()


def install_dependencies(wd):
    """
        use pip's -r option to install from requirements file
    """

    rp = os.path.join(wd, 'requirements.txt')
    # subprocess.call(['pip', 'install', '-r{}'.format(rp)])
    # reqs=['pyproj','lxml','uncertainties','xlrd','xlwt',
    #       'statsmodels','pyshp','pytables','sqlalchemy','reportlab']
    with open(rp, 'r') as fp:
        for req in fp:
            subprocess.call(['easy_install', req])


def build_app(filename):
    template = buildtools.findtemplate()
    dstfilename = None
    rsrcfilename = None
    raw = 0
    extras = []
    verbose = None
    destroot = ''

    cr, tp = MacOS.GetCreatorAndType(filename)
    if tp == 'APPL':
        buildtools.update(template, filename, dstfilename)
    else:
        buildtools.process(template, filename, dstfilename, 1,
                           rsrcname=rsrcfilename, others=extras, raw=raw,
                           progress=verbose, destroot=destroot)


if __name__ == '__main__':
    install('pyexperiment')

#============= EOF =============================================

