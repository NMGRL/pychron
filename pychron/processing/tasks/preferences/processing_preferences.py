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
from canopy.plugin.preferences import PreferencesPane
from traits.api import Int, Bool
from traitsui.api import View, Item, Group

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class ProcessingPreferences(BasePreferencesHelper):
    use_easy = Bool
    recent_hours = Int
    preferences_path = 'pychron.processing'


class ProcessingPreferencesPane(PreferencesPane):
    model_factory = ProcessingPreferences
    category = 'Processing'

    def traits_view(self):
        recent_grp = Group(
            Item('recent_hours', label='Hours',
                 tooltip='Number of hours a "Recent" database search will include'),
            label='Recent',
            show_border=True)

        easy_grp = Group(Item('use_easy'))
        v = View(recent_grp,
                 easy_grp,
        )
        return v


class EasyPreferencesPane(PreferencesPane):
    model_factory = ProcessingPreferences
    category = 'Processing'

    def traits_view(self):
        easy_grp = Group(Item('use_easy'), label='Easy')
        v = View(easy_grp)
        return v

#============= EOF =============================================
