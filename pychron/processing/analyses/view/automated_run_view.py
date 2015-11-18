# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traitsui.api import View, UItem, Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.analyses.view.main_view import MainView
from pychron.pychron_constants import AR_AR


class AutomatedRunAnalysisView(MainView):
    def _get_irradiation(self, an):
        return self._irradiation_str

    def _get_j(self, an):
        return self._j

    def load(self, automated_run):
        isotope_group = automated_run.isotope_group
        self.isotopes = [isotope_group.isotopes[k] for k in isotope_group.isotope_keys]

        self.load_computed(isotope_group)
        self.load_extraction(automated_run.spec)
        self.load_measurement(automated_run.spec, isotope_group)

        self._load_hook(automated_run, isotope_group)

    def _load_hook(self, automated_run, isotope_group):
        pass

    def traits_view(self):
        teditor, ieditor, ceditor, eeditor, meditor = es = self._get_editors()
        for ei in es:
            ei.adapter.font = '10'

        isotopes = UItem('isotopes', editor=teditor, label='Isotopes')

        ratios = UItem('computed_values', editor=ceditor, label='Ratios')

        meas = UItem('measurement_values',
                     editor=meditor, label='General')

        extract = UItem('extraction_values',
                        editor=eeditor,
                        label='Extraction')

        v = View(
            Group(isotopes, ratios, extract, meas, layout='tabbed'))
        return v


class ArArAutomatedRunAnalysisView(MainView):
    _corrected_enabled = False

    def _load_hook(self, automated_run, isotope_group):
        if self.experiment_type == AR_AR:
            self._irradiation_str = automated_run.spec.irradiation
            self._j = isotope_group.j


class GenericAutomatedRunAnalysisView(MainView):
    def load_computed(self, an, new_list=True):
        pass
# ============= EOF =============================================
