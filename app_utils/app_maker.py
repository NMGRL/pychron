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

import argparse
import buildtools
import MacOS
import os
import plistlib
import shutil


def make():
    parser = argparse.ArgumentParser(description='Make a pychron application')
    parser.add_argument('-A', '--applications',
                        nargs=1,
                        type=str,
                        # default=['pychron', 'remote_hardware_server', 'bakeout'],
                        help='set applications to build')
    parser.add_argument('-v', '--version',
                        nargs=1,
                        type=str,
                        default=['1.0'],
                        help='set the version number e.g 1.0')

    parser.add_argument(
        '-r',
        '--root',
        type=str,
        nargs=1,
        default='.',
        help='set the root directory',
        )

    args = parser.parse_args()
    apps = args.applications
    for name in apps:
        template = None
        flavors = ('diode', 'co2', 'valve', 'uv', 'experiment', 'view', 'bakedpy')
        if name in flavors:
            template = Template()
            template.root = args.root[0]
            template.version = args.version[0]
            template.name = name
            if name in ('bakedpy',):
                template.root = args.root[0]
#                template.version = args.version[0]
#                template.name = name
                template.icon_name = '{}_icon.icns'.format(name)
                template.bundle_name = name
            else:
#                template = Template()
                
    
                template.icon_name = 'py{}_icon.icns'.format(name)
                template.bundle_name = 'py{}'.format(name)
            
        if template is not None:
            template.build()
        else:
            print "Invalid application flavor. Use {}".format(', '.join(map("'{}'".format, flavors)))


class Template(object):
    name = None
    icon_name = None
    root = None
    bundle_name = None
    version = None

    def build(self):
        root = os.path.realpath(self.root)

        dest = os.path.join(root, 'launchers',
                              '{}.app'.format(self.bundle_name),
                              'Contents'
                              )
        ins = Maker()
        ins.root = root
        ins.dest = dest
        ins.name = self.bundle_name
        ins.apppath = os.path.join(root, 'launchers',
                              '{}.app'.format(self.bundle_name))
        ins.version = self.version

        op = os.path.join(root, 'launchers',
                          '{}.py'.format(self.bundle_name))
        #=======================================================================
        # build
        #=======================================================================
        ins.build_app(op)
        ins.make_egg()
        ins.make_migrate_repos()
        ins.make_argv()


        #=======================================================================
        # copy
        #=======================================================================
        icon_name = self.icon_name
        if icon_name is None:
            icon_name = ''

        ins.set_plist(dest, self.bundle_name, icon_name)

        icon_file = os.path.join(self.root,
                                 'resources', 'apps',
                                 icon_name)

        if os.path.isfile(icon_file):
            shutil.copyfile(icon_file,
                            os.path.join(dest, 'Resources', icon_name))

        for ni, nd in (('splash', 'splashes'), ('about', 'abouts')):
            sname = '{}_{}.png'.format(ni, self.name)
            ins.copy_resource(os.path.join(root, 'resources', nd, sname), name='{}.png'.format(ni))

#        for pn in ('start', 'stop'):
#            ins.copy_resource(os.path.join(root,
#                                           'resources', 'icons',
#                                           '{}.png'.format(pn)))
        #copy entire icons dir
        iroot=os.path.join(root, 'resources','icons')
        for di in os.listdir(iroot):
#            print di
            ins.copy_resource(os.path.join(iroot, di))
        
        # copy helper mod
        helper = os.path.join(self.root,
                              'launchers', 'helpers.py')
        ins.copy_resource(helper)

        #=======================================================================
        # rename
        #=======================================================================
        ins.rename_app()

class PychronTemplate(Template):
    pass


class Maker(object):
    root = None
    dest = None
    version = None
    name = None
    def copy_resource(self, src, name=None):
        if os.path.isfile(src):
            if name is None:
                name = os.path.basename(src)
            shutil.copyfile(src,
                            self._resource_path(name))

    def _resource_path(self, name):
        return os.path.join(self.dest, 'Resources', name)

    def make_migrate_repos(self):

        root = self.root
        p = os.path.join(root, 'pychron', 'database', 'migrate')
        shutil.copytree(p, self._resource_path('migrate_repositories'))


    def make_egg(self):
        from setuptools import setup, find_packages

        pkgs = find_packages(self.root,
                            exclude=('launchers', 'tests',
                                     'app_utils')
                            )

        setup(name='pychron',
              script_args=('bdist_egg',),
#                           '-b','/Users/argonlab2/Sandbox'),
              version=self.version,
              packages=pkgs

              )

        eggname = 'pychron-{}-py2.7.egg'.format(self.version)
        # make the .pth file
        with open(os.path.join(self.dest,
                               'Resources',
                               'pychron.pth'), 'w') as fp:
            fp.write('{}\n'.format(eggname))

        egg_root = os.path.join(self.root, 'dist', eggname)
        shutil.copyfile(egg_root,
                        self._resource_path(eggname)
                        )

        # remove build dir
        p = os.path.join(self.root, 'build')
        print 'removing entire build dir ', p
        shutil.rmtree(p)

    def make_argv(self):
        argv = '''
import os
execfile(os.path.join(os.path.split(__file__)[0], "{}.py"))
'''.format(self.name)

        p = self._resource_path('__argvemulator_{}.py'.format(self.name))
        with open(p, 'w') as fp:
            fp.write(argv)

    def set_plist(self, dest, bundle_name, icon_name):
        info_plist = os.path.join(dest, 'Info.plist')
        tree = plistlib.readPlist(info_plist)

        tree['CFBundleIconFile'] = icon_name
        tree['CFBundleDisplayName'] = bundle_name
        tree['CFBundleName'] = bundle_name
        plistlib.writePlist(tree, info_plist)

    def build_app(self, filename):
        print filename
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

    def rename_app(self):
        old = self.apppath
        new = os.path.join(os.path.dirname(old),
                           '{}_{}.app'.format(self.name, self.version))
        i = 1
#        print old, new
        while 1:
#        for i in range(3):
            try:
                os.rename(old, new)
                break
            except OSError, e:
#                print e
                name = new[:-4]
                bk = '{}_{:03d}bk.app'.format(name, i)
                print '{} already exists. backing it up as {}'.format(new, bk)
                try:
                    os.rename(new, bk)
                except OSError:
                    i += 1

if __name__ == '__main__':
    make()
