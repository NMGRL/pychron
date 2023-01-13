# ===============================================================================
# Copyright 2023 ross
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
import json
import os

import requests

from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.globals import globalv
from pychron.loggable import Loggable
from traitsui.api import View, UItem, ListStrEditor, HGroup, VGroup, TextEditor
from traits.api import Int, List, Button, Str, HasTraits, Property

from pychron.paths import paths

def memoize(function):
    """ """
    cache = {}

    def closure(*args):
        if args not in cache:
            cache[args] = function(*args)
        return cache[args]

    return closure


class Package(HasTraits):
    name = Str
    url = Str

    def get_settings(self):
        manifest = self.get_manifest_file()
        # for file in manifest.split('\n'):
        return manifest.split('\n')
    def get_setting(self, name):
        return self.get_file(name)
    def get_manifest_file(self):
        return self.get_file('manifest.txt')
    @memoize
    def get_file(self, path):
        url = self.url
        if url.startswith('https://github'):
            url = url.replace('https://github.com', 'https://raw.githubusercontent.com')
        url = f'{url}/main/{path}'
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
    def get_description(self, name):
        name = f'{".".join(name.split(".")[:-1])}.md'
        return self.get_file(name) or ''

class SettingsManager(Loggable):
    packages = List
    package_names = Property(depends_on='packages')
    selected_package = Str
    available_settings = List
    selected_settings = List
    install_settings_button = Button("Install")
    help_str = Str('Select a package to load available settings.  Select one or more settings '
                   'and then click the "Install" button')
    selected_description = Str

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._load_packages()

    def _load_package(self, package_name=None):
        p = self._get_package(package_name)
        self.available_settings = p.get_settings()

    def _load_packages(self):
        if not os.path.isfile(paths.packages_file):
            self.packages = [Package(name='PychronLabsLLC',
                                     url='https://github.com/PychronLabsLLC/settings_package')]
        else:
            with open(paths.packages_file, 'r') as rfile:
                ps = json.load(rfile)
                self.packages = ps
    def _dump_packages(self):
        with open(paths.packages_file, 'w') as wfile:
            json.dump(list(self.packages), wfile)
    def _install_settings_button_fired(self):
        print(self.selected_settings)
        p = self._get_package()
        for s in self.selected_settings:
            sfile = p.get_setting(s)

            # name will be something like spectrum.multigraph.json
            args = s.split('.')
            name = '.'.join(args[1:])
            basedir = args[0]
            destpath = os.path.join(paths.plotter_options_dir, globalv.username, basedir, name)
            with open(destpath, 'w') as wfile:
                wfile.write(sfile)

    def _selected_settings_changed(self):
        if self.selected_settings:
            s = self.selected_settings[-1]
            p = self._get_package()
            self.selected_description = p.get_description(s)

    def _selected_package_changed(self):
        self._load_package()

    def _get_package(self, name=None):
        if name is None:
            name = self.selected_package

        return next((p for p in self.packages if p.name==name), None)
    def _get_package_names(self):
        return [p.name for p in self.packages]

    def traits_view(self):
        v = View(VGroup(BorderVGroup(CustomLabel('help_str', size=14),),
                        HGroup(VGroup(BorderVGroup(UItem('package_names',
                                                  editor=ListStrEditor(editable=False, selected='selected_package')),
                                            label='Packages')),
                        VGroup(
                            # icon_button_editor('install_settings_button', 'document-import'),
                               BorderVGroup(UItem('available_settings', editor=ListStrEditor(editable=False,
                                                                         multi_select=True,
                                                                         selected='selected_settings')),
                                            UItem('selected_description',
                                                  style='custom',
                                                  editor=TextEditor(read_only=True)),
                                            label='Settings'
                                            ),
                            UItem("install_settings_button", enabled_when='selected_settings')
                        ))),
                 title='Install Settings')
        return v


if __name__ == '__main__':
    paths.build("~/PychronDev")
    s = SettingsManager()
    s.configure_traits()
# ============= EOF =============================================
