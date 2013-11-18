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
from traits.api import HasTraits, Str
from traitsui.api import View, UItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.ui.text_editor import myTextEditor


class ExperimentView(HasTraits):
    name = 'Experiment'
    text = Str

    def __init__(self, analysis, *args, **kw):
        super(ExperimentView, self).__init__(*args, **kw)
        self._load(analysis)

    def _load(self, an):
        self.text = an.experiment_txt

    def traits_view(self):
        editor = myTextEditor(bgcolor='#F7F6D0',
                              fontsize=10,
                              wrap=False,
                              tab_width=15)
        v = View(UItem('text', style='custom', editor=editor))
        return v

    #============= EOF =============================================
