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
from traitsui.api import View, UItem, Group

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.analyses.view.main_view import MainView


class AutomatedRunAnalysisView(MainView):
    # def update_values(self, arar_age):
    #     for ci in self.computed_values:
    #         v = getattr(arar_age, ci)

    def load(self, ar):
        an = ar.arar_age
        self.isotopes = [an.isotopes[k] for k in an.isotope_keys]
        self._irradiation_str = ar.spec.irradiation
        self._j = an.j

        self.load_computed(an)
        self.load_extraction(ar.spec)

        self.load_measurement(ar.spec, an)

    def _get_irradiation(self, an):
        return self._irradiation_str

    def _get_j(self, an):
        return self._j

    def traits_view(self):
        teditor, ieditor, ceditor, eeditor, meditor = es = self._get_editors()
        for ei in es:
            ei.adapter.font = 'arial 10'

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

#============= EOF =============================================
