# ===============================================================================
# Copyright 2017 ross
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
from traits.api import HasTraits, List, Instance, Str, Int, on_trait_change, Any
from traitsui.api import View, UItem, TabularEditor, Item, EnumEditor, HGroup, VGroup, InstanceEditor, Controller, \
    VSplit

from pychron.envisage.browser.adapters import AnalysisAdapter
from pychron.pychron_constants import NULL_STR


class RunHistoryModel(HasTraits):
    analyses = List
    dvc = Instance('pychron.dvc.dvc.DVC')

    mass_spectrometer = Str
    mass_spectrometers = List
    n = Int(10)
    analysis_view = Instance('pychron.processing.analyses.view.analysis_view.AnalysisView')
    selected = Any
    _cache = None

    def load(self):
        self.dvc.create_session()
        self._load_analyses()
        self.mass_spectrometers = [NULL_STR] + self.dvc.get_mass_spectrometer_names()

    def destroy(self):
        self.dvc.close_session()
        self._cache = None

    @on_trait_change('mass_spectrometer, n')
    def _load_analyses(self):
        ms = self.mass_spectrometer
        if ms == NULL_STR:
            ms = None

        self.analyses = list(reversed(self.dvc.get_last_n_analyses(self.n, ms)))

    def _selected_changed(self, new):

        if self._cache is None:
            self._cache = {}
        uuid = new.uuid
        if uuid in self._cache:
            av = self._cache[uuid]
        else:
            a = self.dvc.make_analysis(new.record_views[0])
            av = a.analysis_view

        self._cache[new.uuid] = av
        self.analysis_view = av


class RunHistoryView(Controller):
    def closed(self, info, is_ok):
        self.model.destroy()

    def traits_view(self):
        agrp = HGroup(UItem('mass_spectrometer', editor=EnumEditor(name='mass_spectrometers')),
                      Item('n', label='Limit'))

        adapter = AnalysisAdapter()
        adapter.run_history_columns()

        v = View(VSplit(VGroup(agrp,
                               UItem('analyses', editor=TabularEditor(selected='selected',
                                                                      editable=False,
                                                                      adapter=adapter))),
                        UItem('analysis_view',
                              visible_when='analysis_view',
                              style='custom', editor=InstanceEditor())),
                 title='Run History',
                 width=700,
                 height=700,
                 resizable=True,
                 buttons=['OK'])
        return v

# ============= EOF =============================================
