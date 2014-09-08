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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Int, Bool, Property
from traitsui.api import View, Item, Group

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class ProcessingPreferences(BasePreferencesHelper):
    recent_hours = Property(Int, depends_on='_recent_hours')
    preferences_path = 'pychron.processing'
    _recent_hours=Int

    graphical_filtering_max_days = Int

    def _get_recent_hours(self):
        return self._recent_hours

    def _set_recent_hours(self,v):
        if v:
            self._recent_hours=v

    def _validate_recent_hours(self,v):
        if v<0:
            return
        else:
            return v

class ProcessingPreferencesPane(PreferencesPane):
    model_factory = ProcessingPreferences
    category = 'Processing'

    def traits_view(self):
        recent_grp = Group(
            Item('recent_hours', label='Hours',
                 tooltip='Number of hours a "Recent" database search will include'),
            label='Recent', )
        graphical_filter_grp = Group(Item('graphical_filtering_max_days', label='Max. Days'),
                                     label='Graphical Filter')
        v = View(recent_grp, graphical_filter_grp)
        return v


class EasyPreferences(BasePreferencesHelper):
    use_easy = Bool
    preferences_path = 'pychron.processing'


class EasyPreferencesPane(PreferencesPane):
    model_factory = EasyPreferences
    category = 'Processing'

    def traits_view(self):
        easy_grp = Group(Item('use_easy'), label='Easy', show_border=True)
        v = View(easy_grp)
        return v

#============= EOF =============================================
