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
import time

from pychron.applications.util.builder import Builder

DEFAULT_INIT='''<root>
  <globals>
  </globals>
  <plugins>
    <general>
      <plugin enabled="true">Database</plugin>
      <plugin enabled="true">Geo</plugin>
      <plugin enabled="false">Experiment</plugin>
      <plugin enabled="true">Processing</plugin>
      <plugin enabled="true">PyScript</plugin>
      <plugin enabled="true">ArArConstants</plugin>
      <plugin enabled="true">Entry</plugin>
      <plugin enabled="true">SystemMonitor</plugin>
    </general>
    <hardware>
    </hardware>
    <data>
    </data>
    <social>
      <plugin enabled="false">Email</plugin>
      <plugin enabled="false">Twitter</plugin>
    </social>
  </plugins>
</root>
'''


def install(name, setup_version='_install'):
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
    root = os.path.join(os.path.expanduser('~'), 'Pychrondata{}'.format(setup_version))
    wd = os.path.join(root, '.hidden', 'updates')
    #clone src code
    repo_name='pychron'
    url = 'https://github.com/NMGRL/{}.git'.format(repo_name)

    if not os.path.isdir(root):
        os.mkdir(root)
        os.mkdir(os.path.join(root, '.hidden'))
        os.mkdir(wd)

        os.chdir(wd)
        subprocess.call(['git', 'clone', url])
        time.sleep(2)
    else:
        os.chdir(os.path.join(wd, repo_name))
        subprocess.call(['git', 'pull'])

    #install dependencies using pip
    # install_dependencies(wd)

    #build
    wd=os.path.join(wd, repo_name)
    build_pychron(wd, name)

    #install setup files
    add_setup_files(root)


def add_setup_files(root, overwrite=False):
    setup_dir=os.path.join(root, 'setupfiles')
    if not os.path.isdir(setup_dir):
        os.mkdir(setup_dir)

    p=os.path.join(setup_dir, 'initialization.xml')
    if not os.path.isfile(p) or overwrite:
        with open(p,'w') as fp:
            fp.write(DEFAULT_INIT)


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

    builder.move()

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

    buildtools.process(template, filename, dstfilename, 1,
                       rsrcname=rsrcfilename, others=extras, raw=raw,
                       progress=verbose, destroot=destroot)


if __name__ == '__main__':
    install('pyexperiment')

#============= EOF =============================================

