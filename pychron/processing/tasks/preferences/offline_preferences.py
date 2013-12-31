#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Bool, File
from traitsui.api import View, Item, Group, FileEditor
from envisage.ui.tasks.preferences_pane import PreferencesPane

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper

#============= standard library imports ========================
#============= local library imports  ==========================


class OfflinePreferences(BasePreferencesHelper):
    preferences_path = 'pychron.vcs'
    use_offline_database=Bool
    database_path= File


class OfflinePreferencesPane(PreferencesPane):
    model_factory = OfflinePreferences
    category = 'Processing'

    def traits_view(self):
        a=Group(Item('use_offline_database'),
                Item('database_path', editor=FileEditor()),
                label='Offline')
        return View(a)




    #============= EOF =============================================
