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
from json import JSONDecodeError

import requests

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup, HTTPStr
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.globals import globalv
from pychron.loggable import Loggable
from traitsui.api import View, UItem, ListStrEditor, HGroup, VGroup, TextEditor, Item
from traits.api import Int, List, Button, Str, HasTraits, Property

from pychron.paths import paths, r_mkdir


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
    url = HTTPStr
    test_button = Button
    test_result = Str

    def json(self):
        j = {attr: getattr(self, attr) for attr in ("name", "url")}
        return j

    def add(self):
        if self.edit_traits():
            return True

    def _test_button_fired(self):
        mf = self.get_manifest_file(cached=False)
        if mf:
            self.test_result = "OK"
            return

        self.test_result = "Invalid"

    def traits_view(self):
        v = okcancel_view(
            Item("name"),
            HGroup(Item("url", label="URL"), UItem("test_button")),
            UItem("test_result", style="readonly"),
            width=600,
            title="Add Package",
        )
        return v

    def get_settings(self):
        manifest = self.get_manifest_file()
        # for file in manifest.split('\n'):
        return manifest.split("\n")

    def get_setting(self, name):
        return self.get_file(name)

    def get_manifest_file(self, cached=True):
        func = self.get_file if cached else self._get_file
        return func("manifest.txt")

    @memoize
    def get_file(self, path):
        return self._get_file(path)

    def _get_file(self, path):
        url = self.url
        if url.startswith("https://github"):
            url = url.replace("https://github.com", "https://raw.githubusercontent.com")
        url = f"{url}/main/{path}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text

    def get_description(self, name):
        name = f'{".".join(name.split(".")[:-1])}.md'
        return self.get_file(name) or ""


class SettingsManager(Loggable):
    packages = List
    package_names = Property(depends_on="packages")
    selected_package = Str
    available_settings = List
    selected_settings = List
    add_package_button = Button
    install_settings_button = Button("Install")
    help_str = Str(
        "Select a <b>Package</b> to load available <b>Settings</b>.<br>Select one or more <b>Settings</b> "
        'and then click the "Install" button'
    )
    selected_description = Str

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._load_packages()

    def _load_package(self, package_name=None):
        p = self._get_package(package_name)
        self.available_settings = p.get_settings()

    def _load_packages(self):
        if not os.path.isfile(paths.packages_file):
            self.packages = [
                Package(
                    name="PychronLabsLLC",
                    url="https://github.com/PychronLabsLLC/settings_package",
                )
            ]
        else:
            with open(paths.packages_file, "r") as rfile:
                try:
                    ps = json.load(rfile)
                except JSONDecodeError:
                    self.packages = [
                        Package(
                            name="PychronLabsLLC",
                            url="https://github.com/PychronLabsLLC/settings_package",
                        )
                    ]
                    return

                self.packages = [Package(**pii) for pii in ps]

    def _dump_packages(self):
        with open(paths.packages_file, "w") as wfile:
            json.dump([p.json() for p in self.packages], wfile)

    def _add_package_button_fired(self):
        np = Package()
        if np.add():
            self.packages.append(np)
            self._dump_packages()

    def _install_settings_button_fired(self):
        p = self._get_package()
        for s in self.selected_settings:
            sfile = p.get_setting(s)

            # name will be something like spectrum.multigraph.json
            args = s.split(".")
            name = ".".join(args[1:])
            basedir = args[0]

            root = os.path.join(paths.plotter_options_dir, globalv.username, basedir)
            r_mkdir(root)

            destpath = os.path.join(root, name)

            with open(destpath, "w") as wfile:
                wfile.write(sfile)
            self.information_dialog(f'"{s}" installed successfully')

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

        return next((p for p in self.packages if p.name == name), None)

    def _get_package_names(self):
        return [p.name for p in self.packages]

    def traits_view(self):
        v = View(
            VGroup(
                BorderVGroup(
                    CustomLabel("help_str", size=14),
                ),
                HGroup(
                    VGroup(
                        HGroup(icon_button_editor("add_package_button", "add")),
                        BorderVGroup(
                            UItem(
                                "package_names",
                                editor=ListStrEditor(
                                    editable=False, selected="selected_package"
                                ),
                            ),
                            label="Packages",
                        ),
                    ),
                    VGroup(
                        # icon_button_editor('install_settings_button', 'document-import'),
                        BorderVGroup(
                            UItem(
                                "available_settings",
                                editor=ListStrEditor(
                                    editable=False,
                                    multi_select=True,
                                    selected="selected_settings",
                                ),
                            ),
                            UItem(
                                "selected_description",
                                style="custom",
                                editor=TextEditor(read_only=True),
                            ),
                            label="Settings",
                        ),
                        UItem(
                            "install_settings_button", enabled_when="selected_settings"
                        ),
                    ),
                ),
            ),
            title="Install Settings",
        )
        return v


if __name__ == "__main__":
    paths.build("~/PychronDev")
    s = SettingsManager()
    s.configure_traits()
# ============= EOF =============================================
