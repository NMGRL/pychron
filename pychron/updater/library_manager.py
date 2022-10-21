# ===============================================================================
# Copyright 2022 ross
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
import os.path
import subprocess
import sys

from PyQt5.QtWidgets import QApplication
from traits.api import HasTraits, Str, List, Int, Button
from traitsui.api import View, UItem, Item, TabularEditor, HGroup
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.loggable import Loggable


class LibraryAdapter(TabularAdapter):
    columns = [("Name", "name"), ("Version", "version")]
    name_width = Int(200)


PV = View(
    HGroup(
        icon_button_editor("copy_as_text", "copy", tooltip='Copy Library list as text'),
        icon_button_editor("install_library_button", "add", tooltip='Install library'),
    ),
    UItem(
        "libraries",
        editor=TabularEditor(adapter=LibraryAdapter(), stretch_last_section=False),
    ),
    title="Library Manager",
    width=400,
    height=600,
    resizable=True,
)

LV = okcancel_view("library_entry", title="Install Library")


def pip_cmd(*args):
    pyexecutable = sys.executable
    pipexecutable = os.path.join(os.path.dirname(pyexecutable), "pip")

    cmd = (pipexecutable,) + args
    return subprocess.check_output(cmd).decode("utf8")


class Library(HasTraits):
    name = Str
    version = Str

    def __init__(self, a, *args, **kw):
        super(Library, self).__init__(*args, **kw)
        args = a.split(" ")
        self.name, self.version = args[0].strip(), args[-1].strip()

    def tostr(self):
        return f"{self.name} {self.version}"


class LibraryManager(Loggable):
    libraries = List
    copy_as_text = Button()
    install_library_button = Button()
    library_entry = Str

    def _copy_as_text_fired(self):
        txt = "\n".join((p.tostr() for p in self.libraries))
        clipboard = QApplication.clipboard()
        clipboard.setText(txt)

    def _install_library_button_fired(self):
        info = self.edit_traits(LV)
        if info.result:
            self._install_library(self.library_entry)

    def install_dependencies(self, *args, **kw):
        p = './dependencies.txt'
        fails = []
        with open(p, 'r') as rfile:
            for line in rfile:
                d = line.strip()
                name = self._install_library(d, warn=True)
                if name:
                    fails.append(name)

        if fails:
            self.warning(f"The libraries {fails} failed to install. Please install manually or contact a python "
                         f"expert")

    def _install_library(self, entry, warn=False):

        # parse entry for name and version
        name, version = entry, ""
        try:
            pip_cmd("install", name)
            self.info(f"installed {name} successfully")
        except subprocess.CalledProcessError:
            if warn:
                self.critical(f'"{name}" could not be located. Parts of pychron will be broken if not resolved')
                return name
            else:
                self.information_dialog(
                    f'"{name}" could not be located.\n\nPlease make sure the library name is spelled '
                    f"correctly"
                )

    def load_libraries(self):
        args = pip_cmd("list")
        self.libraries = [Library(a) for a in args.splitlines()[2:]]

    def traits_view(self):
        return PV


if __name__ == "__main__":
    d = LibraryManager()
    d.load_libraries()
    d.configure_traits()
# ============= EOF =============================================
