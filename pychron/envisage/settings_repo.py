# ===============================================================================
# Copyright 2019 ross
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
import os
import shutil

from traits.api import HasTraits, Str, List
from traitsui.api import UItem, ListStrEditor, VGroup

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.check_list_editor import CheckListEditor
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.globals import globalv
from pychron.paths import paths


class NameEntry(HasTraits):
    name = Str

    def traits_view(self):
        v = okcancel_view(
            UItem("name"), resizable=True, width=300, title="Enter Settings Name"
        )
        return v


class Selection(HasTraits):
    names = List
    selected = Str
    option_names = List
    available_option_names = List
    path = Str
    source = Str

    def traits_view(self):
        return okcancel_view(
            VGroup(
                UItem(
                    "names", editor=ListStrEditor(selected="selected", editable=False)
                ),
                UItem(
                    "option_names",
                    style="custom",
                    editor=CheckListEditor(name="available_option_names", cols=3),
                ),
            ),
            title="Select Settings",
        )

    def _selected_changed(self, new):
        if new:
            self.source = src = os.path.join(
                self.path, "settings", new, "plotter_options"
            )
            self.option_names = [
                d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d))
            ]
            self.available_option_names = self.option_names[:]


class SettingsRepoManager(GitRepoManager):
    def apply_settings(self):
        """
        pull from github
        get list of settings names
        user selects settings
        copy settings to proper locations

        :return:
        """
        select = Selection(path=self.path, names=self._get_existing_settings_names())
        info = select.edit_traits()
        if info.result:
            name = select.selected
            selected_options = select.option_names
            if name and selected_options:
                dest = os.path.join(paths.plotter_options_dir, globalv.username)
                if os.path.isdir(dest):
                    if not self.confirmation_dialog(
                        "You are about to overwrite your existing settings\n"
                        "Are you sure you want to continue?"
                    ):
                        return

                    self._rmtree(dest, selected_options)

                self._copytree(select.source, dest, selected_options)

    def _rmtree(self, dest, selected_options):
        if selected_options is None:
            shutil.rmtree(dest)
        else:
            for si in selected_options:
                p = os.path.join(dest, si)
                if os.path.isdir(p):
                    shutil.rmtree(p)

    def _copytree(self, src, dest, selected_options):
        if selected_options is None:
            shutil.copytree(src, dest)
        else:
            for si in selected_options:
                ss = os.path.join(src, si)
                dd = os.path.join(dest, si)
                shutil.copytree(ss, dd)

    def share_settings(self):
        """
        save current settings to the laboratory's repository

        pull from github
        ask for a <name> from user
        warn if settings name already exists
        save settings files in <name> directory
        push to github

        :return:
        """
        settings_root = os.path.join(self.path, "settings")

        if not os.path.isdir(settings_root):
            os.mkdir(settings_root)

        msg = "Added"
        existing_settings_names = self._get_existing_settings_names()
        name_entry = NameEntry()
        while 1:
            info = name_entry.edit_traits()
            if info.result:
                name = name_entry.name
                if name in existing_settings_names:
                    resp = self.confirmation_dialog(
                        'Settings "{}" already exists. Would you like to '
                        "overwrite?".format(name)
                    )
                    if resp:
                        msg = "Overwrote"
                        shutil.rmtree(os.path.join(settings_root, name))
                        break
                    else:
                        return
                else:
                    break
            else:
                return

        working_root = os.path.join(settings_root, name)
        os.mkdir(working_root)

        srctree = os.path.join(paths.plotter_options_dir, globalv.username)
        shutil.copytree(srctree, os.path.join(working_root, "plotter_options"))

        self.add_unstaged(add_all=True)
        self.commit('{} Settings "{}"'.format(msg, name))
        self.push()

    # private
    def _get_existing_settings_names(self):
        settings_root = os.path.join(self.path, "settings")
        if os.path.isdir(settings_root):
            ret = [
                d
                for d in os.listdir(settings_root)
                if os.path.isdir(os.path.join(settings_root, d))
            ]
        else:
            ret = []
        return ret


# ============= EOF =============================================
