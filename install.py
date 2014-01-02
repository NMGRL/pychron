#!~/Library/Enthought/Canopy_64bit/User/bin/python
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
import plistlib
import subprocess
import MacOS
import imp
import shutil


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
        os.mkdir(wd)
        subprocess.call(['git', 'clone', url, wd])

    # subprocess.call(['cd', wd])
    # subprocess.call(['pwd'])

    # subprocess.Popen(['git', 'clone', url, wd])
    #install dependencies using pip
    install_dependencies(wd)

    #build
    # build_pychron(wd, name)


def install_dependencies(wd):
    """
        use pip's -r option to install from requirements file
    """
    rp = os.path.join(wd, 'requirements.txt')

    print rp, os.path.isfile(rp)
    # subprocess.call(['pip','-h'])
    subprocess.call(['pip','install', '-r{}'.format(rp)])


def build_pychron(wd, name):
    filename = os.path.join(wd, 'launchers', '{}.py'.format(name))
    build_app(filename)

    dest = os.path.join(wd, 'launchers', '{}.app'.format(name), 'Contents')

    # set plist
    info_plist = os.path.join(dest, 'Info.plist')
    tree = plistlib.readPlist(info_plist)

    icon_name='{}_icon.icns'.format(name)
    tree['CFBundleIconFile'] =icon_name
    tree['CFBundleDisplayName'] = name
    tree['CFBundleName'] = name
    plistlib.writePlist(tree, info_plist)

    # make egg
    eggname = build_egg(wd, dest)

    #copy resources
    copy_resources(wd, dest, eggname, name, icon_name)


def build_egg(wd, dest):
    from setuptools import setup, find_packages

    # pkgs = find_packages(wd,
    #                      exclude=(
    #                             'app_utils',
    #                             'docs',
    #                             'launchers',
    #                             'migration',
    #                             'tests',
    #                              'qtegra',
    #                              'sandbox'
    #                               ))

    pkgs=find_packages(os.path.join(wd, 'pychron'))
    ver = imp.new_module('ver')
    v = open(os.path.join(wd, 'pychron','version.py')).read()
    exec v in ver.__dict__

    app_name = 'pychron'
    setup(name=app_name,
          script_args=('bdist_egg',),
          version=ver.__version__,
          packages=pkgs)

    eggname = '{}-{}-py2.7.egg'.format(app_name, ver.__version__)
    # make the .pth file
    with open(os.path.join(dest, 'Resources',
                           '{}.pth'.format(app_name)), 'w') as fp:
        fp.write('{}\n'.format(eggname))

        # remove build dir
        # p = os.path.join(wd, 'build')
        # print 'removing entire build dir ', p
        # shutil.rmtree(p)


def copy_resources(wd, dest, eggname, app_name, icon_name):
    egg_root = os.path.join(wd, 'dist', eggname)
    copy_resource(egg_root, dest)

    icon_file = os.path.join(wd, 'resources', 'apps', icon_name)
    copy_resource(icon_file, dest)

    for ni, nd in (('splash', 'splashes'), ('about', 'abouts')):
        sname = '{}_{}.png'.format(ni, app_name)
        copy_resource(os.path.join(wd, 'resources', nd, sname),
                      dest,
                      name='{}.png'.format(ni))

    #copy entire icons dir
    iroot = os.path.join(wd, 'resources', 'icons')
    for di in os.listdir(iroot):
        copy_resource(os.path.join(iroot, di), dest)

    # copy helper mod
    helper = os.path.join(wd, 'launchers', 'helpers.py')
    copy_resource(helper, dest)


def copy_resource(src, dest, name=None):
    if os.path.isfile(src):
        if name is None:
            name = os.path.basename(src)

        shutil.copyfile(src, os.path.join(dest, 'Resources', name))


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

