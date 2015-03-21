# # ===============================================================================
# # Copyright 2014 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# # http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# # ============= enthought library imports =======================
#
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
# import buildtools
# import os
# import plistlib
# import shutil
# import subprocess
# import imp
#
# DEFAULT_INIT = '''<root>
#   <globals>
#   </globals>
#   <plugins>
#     <general>
#       <plugin enabled="true">Database</plugin>
#       <plugin enabled="true">Geo</plugin>
#       <plugin enabled="false">Experiment</plugin>
#       <plugin enabled="true">Processing</plugin>
#       <plugin enabled="true">PyScript</plugin>
#       <plugin enabled="true">ArArConstants</plugin>
#       <plugin enabled="true">Entry</plugin>
#       <plugin enabled="true">SystemMonitor</plugin>
#     </general>
#     <hardware>
#     </hardware>
#     <data>
#     </data>
#     <social>
#       <plugin enabled="false">Email</plugin>
#       <plugin enabled="false">Twitter</plugin>
#     </social>
#   </plugins>
# </root>
# '''
#
#
# def install(name, setup_version='_install'):
#     """
#         make Pychrondata
#         make .hidden
#         clone git repo to .hidden/updates
#         install dependencies
#         build pychron
#         move application to Applications
#
#         valid names:
#             pyexperiment
#     """
#
#     #setup application directory
#     root = os.path.join(os.path.expanduser('~'), 'Pychrondata{}'.format(setup_version))
#     wd = os.path.join(root, '.hidden', 'updates')
#
#     #clone src code
#     repo_name = 'pychron'
#     url = 'https://github.com/NMGRL/{}.git'.format(repo_name)
#
#     if not os.path.isdir(root):
#         os.mkdir(root)
#         os.mkdir(os.path.join(root, '.hidden'))
#         os.mkdir(wd)
#
#         os.chdir(wd)
#         subprocess.call(['git', 'clone', url])
#         os.chdir(os.path.join(wd, repo_name))
#
#     else:
#         os.chdir(os.path.join(wd, repo_name))
#         subprocess.call(['git', 'pull'])
#
#     #install dependencies using pip
#     # install_dependencies(wd)
#
#     #build
#     wd = os.path.join(wd, repo_name)
#     build_pychron(wd, name)
#
#     #install setup files
#     add_setup_files(root)
#
#
# def add_setup_files(root, overwrite=False):
#     setup_dir = os.path.join(root, 'setupfiles')
#     if not os.path.isdir(setup_dir):
#         os.mkdir(setup_dir)
#
#     p = os.path.join(setup_dir, 'initialization.xml')
#     if not os.path.isfile(p) or overwrite:
#         with open(p, 'w') as fp:
#             fp.write(DEFAULT_INIT)
#
#
# def build_pychron(wd, name):
#     filename = os.path.join(wd, 'launchers', '{}.py'.format(name))
#     build_app(filename)
#
#     builder = Builder()
#     builder.launcher_name = name
#     builder.root = wd
#
#     ver = imp.new_module('ver')
#     v = open(os.path.join(wd, 'pychron', 'version.py')).read()
#     exec v in ver.__dict__
#     builder.version = ver.__version__
#     builder.run()
#
#     builder.move()
#
#
# def install_dependencies(wd):
#     """
#         use pip's -r option to install from requirements file
#     """
#
#     rp = os.path.join(wd, 'requirements.txt')
#     # subprocess.call(['pip', 'install', '-r{}'.format(rp)])
#     # reqs=['pyproj','lxml','uncertainties','xlrd','xlwt',
#     #       'statsmodels','pyshp','pytables','sqlalchemy','reportlab']
#     with open(rp, 'r') as fp:
#         for req in fp:
#             subprocess.call(['easy_install', req])
#
#
# def build_app(filename):
#     template = buildtools.findtemplate()
#     dstfilename = None
#     rsrcfilename = None
#     raw = 0
#     extras = []
#     verbose = None
#     destroot = ''
#
#     buildtools.process(template, filename, dstfilename, 1,
#                        rsrcname=rsrcfilename, others=extras, raw=raw,
#                        progress=verbose, destroot=destroot)
#
#
# # ===========================================================
# class Builder(object):
#     root = None  #path to working directory
#     dest = None  #path to pychron.app/Contents
#     version = None
#     icon_name = None
#     launcher_name = None
#
#     _package_name = 'pychron'
#
#     def run(self):
#         if self.root:
#             if self.dest is None:
#                 self.dest = os.path.join(self.root,
#                                          'launchers', '{}.app'.format(self.launcher_name), 'Contents')
#
#         self.make_egg()
#         self.copy_resources()
#         self.make_argv()
#
#     def make_egg(self):
#         from setuptools import setup, find_packages
#
#         pkgs = find_packages(self.root,
#                              exclude=('app_utils', 'docs', 'launchers',
#                                       'migration', 'test', 'qtegra',
#                                       'sandbox', 'zobs'))
#
#         pkg_name = self._package_name
#         setup(name=pkg_name,
#               script_args=('bdist_egg',),
#               version=self.version,
#               packages=pkgs)
#
#         eggname = self._get_eggname()
#         # make the .pth file
#         with open(os.path.join(self.dest,
#                                'Resources',
#                                '{}.pth'.format(pkg_name)), 'w') as fp:
#             fp.write('{}\n'.format(eggname))
#
#         # remove build dir
#         p = os.path.join(self.root, 'build')
#         print 'removing entire build dir ', p
#         shutil.rmtree(p)
#
#     def _get_eggname(self):
#         eggname = '{}-{}-py2.7.egg'.format(self._package_name, self.version)
#         return eggname
#
#     def copy_resources(self):
#         """
#             copy egg and resources to destination
#         """
#         eggname = self._get_eggname()
#         egg_root = os.path.join(self.root, 'dist', eggname)
#         self.copy_resource(egg_root)
#
#         icon_name = self.icon_name
#         if icon_name is None:
#             icon_name = '{}_icon.icns'.format(self.launcher_name)
#
#         dest = self.dest
#         root = self.root
#
#         self.set_plist(dest, self.launcher_name, icon_name)
#
#         icon_file = os.path.join(self.root, 'resources', 'apps', icon_name)
#         self.copy_resource(icon_file)
#
#         for ni, nd in (('splash', 'splashes'), ('about', 'abouts')):
#             sname = '{}_{}.png'.format(ni, self.launcher_name)
#             self.copy_resource(os.path.join(root, 'resources', nd, sname), name='{}.png'.format(ni))
#
#         #copy entire icons dir
#         iroot = os.path.join(root, 'resources', 'icons')
#         for di in os.listdir(iroot):
#             self.copy_resource(os.path.join(iroot, di))
#
#         # copy helper mod
#         helper = os.path.join(self.root, 'launchers', 'helpers.py')
#         self.copy_resource(helper)
#
#         #copy version
#         # version = os.path.join(self.root, 'launchers', 'version.py')
#         # self.copy_resource(version)
#
#     def move(self):
#         """
#             move app to /Applications
#         """
#         name = '{}.app'.format(self.launcher_name)
#         src = os.path.join(self.root, 'launchers', name)
#         dst = '/Applications/{}_{}.app'.format(self.launcher_name, self.version)
#
#         i = 1
#         if os.path.exists(dst):
#             while 1:
#                 name = dst[:-4]
#                 bk = '{}_{:03d}bk.app'.format(name, i)
#
#                 if not os.path.exists(os.path.join(os.path.dirname(dst), bk)):
#                     os.rename(dst, bk)
#                     break
#                 i += 1
#
#         shutil.move(src, dst)
#
#     def make_argv(self):
#         argv = '''
# import os
# execfile(os.path.join(os.path.split(__file__)[0], "{}.py"))
#     '''.format(self.launcher_name)
#
#         p = self._resource_path('__argvemulator_{}.py'.format(self.launcher_name))
#         with open(p, 'w') as fp:
#             fp.write(argv)
#
#     def set_plist(self, dest, bundle_name, icon_name):
#         info_plist = os.path.join(dest, 'Info.plist')
#         tree = plistlib.readPlist(info_plist)
#
#         tree['CFBundleIconFile'] = icon_name
#         # tree['CFBundleDisplayName'] = bundle_name
#         tree['CFBundleName'] = bundle_name
#         plistlib.writePlist(tree, info_plist)
#
#     def copy_resource(self, src, name=None):
#         if os.path.isfile(src):
#             if name is None:
#                 name = os.path.basename(src)
#             shutil.copyfile(src, self._resource_path(name))
#
#     def _resource_path(self, name):
#         return os.path.join(self.dest, 'Resources', name)
#
#
# if __name__ == '__main__':
#     install('pyexperiment')
#
# # ============= EOF =============================================
#
