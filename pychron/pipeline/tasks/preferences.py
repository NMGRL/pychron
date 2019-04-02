# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import Str, List
from traitsui.api import View, Item, UItem, VGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import CheckListEditor

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class PipelinePreferences(BasePreferencesHelper):
    preferences_path = 'pychron.pipeline'
    skip_meaning = Str
    _skip_meaning = List
    _initialized = False

    def _initialize(self, *args, **kw):
        super(PipelinePreferences, self)._initialize(*args, **kw)

        self._skip_meaning = sorted(self.skip_meaning.split(','))
        self._initialized = True

    def __skip_meaning_changed(self, new):
        if self._initialized:
            self.skip_meaning = ','.join(sorted(new))


class PipelinePreferencesPane(PreferencesPane):
    model_factory = PipelinePreferences
    category = 'Pipeline'

    def traits_view(self):
        v = View(VGroup(UItem('_skip_meaning',
                              tooltip='Select how the "Skip" tag is used. '
                                      'If X is selected all analyses tagged as "Skip" are excluded when making X',
                              style='custom',
                              editor=CheckListEditor(cols=5,
                                                     values=['Human Table', 'Machine Table', 'Ideogram',
                                                             'Spectrum', 'Series', 'Isochron'])),
                        label='Skip Tag Associations',
                        show_border=True))
        return v

# ============= EOF =============================================
