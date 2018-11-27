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
# ============= standard library imports ========================
# ============= local library imports  ==========================
# from pychron.pipeline.plot. import ReferencesSeries
from __future__ import absolute_import

from six.moves import zip
from uncertainties import ufloat

from pychron.pipeline.plot.plotter.references_series import ReferencesSeries


class Blanks(ReferencesSeries):
    references_name = 'Blanks'

    def _get_interpolated_value(self, po, analysis):
        v, e = 0, 0
        iso = self._get_isotope(po, analysis)
        if iso:
            if iso.temporary_blank is not None:
                v, e = iso.temporary_blank.value, iso.temporary_blank.error
        return v, e

    def _set_interpolated_values(self, iso, fit, ans, p_uys, p_ues):
        for ui, v, e in zip(ans, p_uys, p_ues):
            if v is not None and e is not None:
                ui.set_temporary_blank(iso, v, e, fit)

    def _get_reference_data(self, po):
        _, mx = self._get_min_max()
        ans = self.sorted_references

        atypes = po.analysis_types
        if atypes:
            ans = [ai for ai in ans if ai.analysis_type in atypes]

        xs = self._get_xs([po], ans, tzero=mx)

        ys = [self._get_isotope(po, ai) for ai in ans]
        ys = [yi.get_baseline_corrected_value() if yi else ufloat(0, 0) for yi in ys]

        return ans, xs, ys

    def _get_current_data(self, po):
        isos = [self._get_isotope(po, ai) for ai in self.sorted_analyses]
        return [iso.blank.uvalue if iso else ufloat(0, 0) for iso in isos]

# ============= EOF =============================================
