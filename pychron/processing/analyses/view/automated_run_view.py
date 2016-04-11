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
from pychron.core.helpers.formatting import floatfmt
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.processing.analyses.view.adapters import IsotopeTabularAdapter
from pychron.processing.analyses.view.main_view import MainView
from pychron.processing.analyses.view.values import MeasurementValue


class AutomatedRunAnalysisView(MainView):

    def load(self, automated_run):
        isotope_group = automated_run.isotope_group
        self.isotopes = [isotope_group.isotopes[k] for k in isotope_group.isotope_keys]

        self._load_hook(automated_run, isotope_group)

        self.load_computed(isotope_group)
        self.load_extraction(automated_run.spec)
        self.load_measurement(automated_run.spec, isotope_group)

    def _load_hook(self, automated_run, isotope_group):
        pass

    def traits_view(self):
        teditor = myTabularEditor(adapter=IsotopeTabularAdapter(),
                                  drag_enabled=False,
                                  stretch_last_section=False,
                                  editable=False,
                                  multi_select=True,
                                  selected='selected',
                                  refresh='refresh_needed')

        # teditor, ieditor, ceditor, eeditor, meditor = es = self._get_editors()
        ceditor, eeditor, meditor = es = self._get_editors()
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


class ArArAutomatedRunAnalysisView(AutomatedRunAnalysisView):
    _corrected_enabled = False

    def _get_irradiation(self, an):
        return self._irradiation_str

    def _get_j(self, an):
        return self._j

    def _load_hook(self, automated_run, isotope_group):
        self._irradiation_str = automated_run.spec.irradiation
        self._j = isotope_group.j


class GenericAutomatedRunAnalysisView(AutomatedRunAnalysisView):
    def load_computed(self, an, new_list=True):
        pass

    def load_measurement(self, an, ar):
        ms = [
            MeasurementValue(name='DR Version',
                             value=an.data_reduction_tag),
            MeasurementValue(name='DAQ Version',
                             value=an.collection_version),
            MeasurementValue(name='AnalysisID',
                             value=self.analysis_id),
            MeasurementValue(name='Spectrometer',
                             value=an.mass_spectrometer),
            MeasurementValue(name='Run Date',
                             value=an.rundate.strftime('%Y-%m-%d %H:%M:%S')),
            MeasurementValue(name='Project',
                             value=an.project),
            MeasurementValue(name='Sample',
                             value=an.sample),
            MeasurementValue(name='Material',
                             value=an.material),
            MeasurementValue(name='Comment',
                             value=an.comment),
            MeasurementValue(name='Sens.',
                             value=floatfmt(an.sensitivity))]

        self.measurement_values = ms
# ============= EOF =============================================
