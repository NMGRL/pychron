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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Bool
from traitsui.api import View, Item

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class UpdatePreferencesHelper(BasePreferencesHelper):
    preferences_path = 'pychron.update'
    check_on_startup = Bool(False)
    update_url = Str
    development_url=Str

    use_development=Bool(False)


class UpdatePreferencesPane(PreferencesPane):
    model_factory = UpdatePreferencesHelper
    category = 'Update'
    def traits_view(self):
        v = View(Item('check_on_startup', label='Check for updates at startup'),
                 Item('update_url', label='Update URL'))
        return v

#============= EOF =============================================

