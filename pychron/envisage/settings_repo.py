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
from traitsui.api import UItem, ListStrEditor

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.globals import globalv
from pychron.paths import paths


class NameEntry(HasTraits):
    name = Str

    def traits_view(self):
        v = okcancel_view(UItem('name'),
                          resizable=True,
                          width=300,
                          title='Enter Settings Name')
        return v


class Selection(HasTraits):
    names = List
    selected = Str

    def traits_view(self):
        return okcancel_view(UItem('names', editor=ListStrEditor(selected='selected')),
                             title='Select Settings')


class SettingsRepoManager(GitRepoManager):
    def apply_settings(self):
        """
        pull from github
        get list of settings names
        user selects settings
        copy settings to proper locations

        :return:
        """
        select = Selection(names=self._get_existing_settings_names())
        info = select.edit_traits()
        if info.result:
            name = select.selected
            if name:
                src = os.path.join(self.path, 'settings', name, 'plotter_options')
                dest = os.path.join(paths.plotter_options_dir, globalv.username)
                if os.path.isdir(dest):
                    if not self.confirmation_dialog('You are about to overwrite your existing settings'
                                                    'Are you sure you want to continue?'):
                        return
                    shutil.rmtree(dest)

                shutil.copytree(src, dest)

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
        settings_root = os.path.join(self.path, 'settings')

        if not os.path.isdir(settings_root):
            os.mkdir(settings_root)

        msg = 'Added'
        existing_settings_names = self._get_existing_settings_names()
        name_entry = NameEntry()
        while 1:
            info = name_entry.edit_traits()
            if info.result:
                name = name_entry.name
                if name in existing_settings_names:
                    resp = self.confirmation_dialog('Settings "{}" already exists. Would you like to '
                                                    'overwrite?'.format(name))
                    if resp:
                        msg = 'Overwrote'
                        shutil.rmtree(os.path.join(settings_root, name))
                        break
                else:
                    break
            else:
                return

        working_root = os.path.join(settings_root, name)
        os.mkdir(working_root)

        # copy settings directories
        srctree = os.path.join(paths.plotter_options_dir, globalv.username)
        shutil.copytree(srctree, os.path.join(working_root, 'plotter_options'))

        self.add_unstaged(add_all=True)
        self.commit('{} Settings "{}"'.format(msg, name))
        self.push()

    # private
    def _get_existing_settings_names(self):
        settings_root = os.path.join(self.path, 'settings')
        if os.path.isdir(settings_root):
            ret = [d for d in os.listdir(settings_root) if os.path.isdir(os.path.join(settings_root, d))]
        else:
            ret = []
        return ret
# ============= EOF =============================================
