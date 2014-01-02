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
import os
import plistlib
import shutil

#============= standard library imports ========================
#============= local library imports  ==========================

class Builder(object):

    root = None #path to working directory
    dest = None #path to pychron.app/Contents
    version = None
    icon_name=None
    launcher_name=None

    _package_name='pychron'

    def run(self):
        if self.root:
            if self.dest is None:
                self.dest=os.path.join(self.root,
                                       'launchers','{}.app'.format(self.launcher_name),'Contents')

        self.make_egg()
        self.copy_resources()
        self.make_argv()

    def make_egg(self):
        from setuptools import setup, find_packages

        pkgs = find_packages(self.root,
                             exclude=('app_utils','docs','launchers',
                                      'migration','test','qtegra',
                                      'sandbox','zobs'))

        pkg_name=self._package_name
        setup(name=pkg_name,
              script_args=('bdist_egg',),
              version=self.version,
              packages=pkgs)

        eggname=self._get_eggname()
        # make the .pth file
        with open(os.path.join(self.dest,
                               'Resources',
                               '{}.pth'.format(pkg_name)), 'w') as fp:
            fp.write('{}\n'.format(eggname))

        # remove build dir
        p = os.path.join(self.root, 'build')
        print 'removing entire build dir ', p
        shutil.rmtree(p)

    def _get_eggname(self):
        eggname = '{}-{}-py2.7.egg'.format(self._package_name, self.version)
        return eggname

    def copy_resources(self):
        """
            copy egg and resources to destination
        """
        eggname=self._get_eggname()
        egg_root = os.path.join(self.root, 'dist', eggname)
        self.copy_resource(egg_root)

        icon_name = self.icon_name
        if icon_name is None:
            icon_name = '{}_icon.icns'.format(self.launcher_name)

        dest=self.dest
        root=self.root

        self.set_plist(dest, self.launcher_name, icon_name)

        icon_file = os.path.join(self.root,'resources', 'apps', icon_name)
        self.copy_resource(icon_file)

        for ni, nd in (('splash', 'splashes'), ('about', 'abouts')):
            sname = '{}_{}.png'.format(ni, self.launcher_name)
            self.copy_resource(os.path.join(root, 'resources', nd, sname), name='{}.png'.format(ni))

        #copy entire icons dir
        iroot = os.path.join(root, 'resources', 'icons')
        for di in os.listdir(iroot):
            self.copy_resource(os.path.join(iroot, di))

        # copy helper mod
        helper = os.path.join(self.root, 'launchers', 'helpers.py')
        self.copy_resource(helper)

        #copy version

        version = os.path.join(self.root, 'launchers', 'version.py')
        self.copy_resource(version)

    def move(self):
        """
            move app to /Applications
        """
        name='{}.app'.format(self.launcher_name)
        src=os.path.join(self.root, 'launchers', name)
        dst='/Applications/{}'.format(name)
        shutil.move(src, dst)

    def make_argv(self):
        argv = '''
import os
execfile(os.path.join(os.path.split(__file__)[0], "{}.py"))
    '''.format(self.launcher_name)

        p = self._resource_path('__argvemulator_{}.py'.format(self.launcher_name))
        with open(p, 'w') as fp:
            fp.write(argv)

    def set_plist(self, dest, bundle_name, icon_name):
        info_plist = os.path.join(dest, 'Info.plist')
        tree = plistlib.readPlist(info_plist)

        tree['CFBundleIconFile'] = icon_name
        # tree['CFBundleDisplayName'] = bundle_name
        tree['CFBundleName'] = bundle_name
        plistlib.writePlist(tree, info_plist)

    def copy_resource(self, src, name=None):
        print os.path.isfile(src), src
        if os.path.isfile(src):
            if name is None:
                name = os.path.basename(src)
            shutil.copyfile(src, self._resource_path(name))

    def _resource_path(self, name):
        return os.path.join(self.dest, 'Resources', name)
#============= EOF =============================================

