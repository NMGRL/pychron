# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
from distutils.core import run_setup
import os
import shutil
# ============= standard library imports ========================
# ============= local library imports  ==========================

def copy_resources(root, dest, app_name):
    icon_name = 'py{}_icon.icns'.format(app_name)
    icon_file = os.path.join(root, 'resources', 'apps', icon_name)

    if os.path.isfile(icon_file):
        shutil.copyfile(icon_file,
                        os.path.join(dest, 'Resources', icon_name))

    # copy icons
    iroot = os.path.join(root, 'resources', 'icons')
    rdest = os.path.join(dest, 'Resources')
    idest = os.path.join(rdest, 'icons')
    if not os.path.isdir(idest):
        os.mkdir(idest)

    includes = []
    icon_req = os.path.join(root, 'resources','icon_req.txt')
    if os.path.isfile(icon_req):
        with open(icon_req, 'r') as fp:
            includes = [ri.strip() for ri in fp.read().split('\n')]

    for di in os.listdir(iroot):
        head,_ = os.path.splitext(di)
        if includes and head not in includes:
            continue

        copy_resource(idest, os.path.join(iroot, di))

    # copy splashes and abouts
    for ni, nd in (('splash', 'splashes'), ('about', 'abouts')):
        sname = '{}_{}.png'.format(ni, app_name)
        copy_resource(idest, os.path.join(root, 'resources', nd, sname), name='{}.png'.format(ni))

    # copy helper mod
    for a in ('helpers', ):
        m = os.path.join(root, 'launchers', '{}.py'.format(a))
        copy_resource(rdest, m)

    # copy qt_menu.nib
    p = '/anaconda/python.app/Contents/Resources/qt_menu.nib'
    if not os.path.isdir(p):
        p = '{}/{}'.format(os.path.expanduser('~'),
                           'anaconda/python.app/Contents/Resources/qt_menu.nib')
    copy_resource_dir(rdest, p)


def make_egg(root, dest, pkg_name, version):
    from setuptools import setup, find_packages

    pkgs = find_packages(root,
                         exclude=('app_utils', 'docs', 'launchers',
                                  'migration', 'test', 'test.*', 'qtegra',
                                  'sandbox', 'zobs'))
    os.chdir(root)
    try:
        setup(name=pkg_name,
              script_args=('bdist_egg',),
              packages=pkgs)
    except BaseException, e:
        import traceback
        traceback.print_exc()

    eggname = '{}-0.0.0-py2.7.egg'.format(pkg_name)
    # make the .pth file

    if dest.endswith('Contents'):
        rdest = os.path.join(dest, 'Resources')
        with open(os.path.join(rdest,
                               '{}.pth'.format(pkg_name)), 'w') as fp:
            fp.write('{}\n'.format(eggname))

        egg_root = os.path.join(root, 'dist', eggname)
        copy_resource(rdest, egg_root)

    # remove build dir
    for di in ('build', 'dist','pychron.egg-info'):
        p = os.path.join(root, di)
        print 'removing entire {} dir {}'.format(di, p)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            print 'not a directory {}'.format(p)


def resource_path(dest, name):
    return os.path.join(dest, name)


def copy_resource_dir(dest, src, name=None):
    if os.path.exists(src):
        if name is None:
            name = os.path.basename(src)

        rd = resource_path(dest, name)
        if not os.path.exists(rd):
            shutil.copytree(src, rd)
    else:
        print '++++++++++++++++++++++ Not a valid Resource {} +++++++++++++++++++++++'.format(src)


def copy_resource(dest, src, name=None):
    if os.path.isfile(src):
        if name is None:
            name = os.path.basename(src)
        shutil.copyfile(src, resource_path(dest, name))
    else:
        print '++++++++++++++++++++++ Not a valid Resource {} +++++++++++++++++++++++'.format(src)
# ============= EOF =============================================



