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
from pychron.pipeline.plot.plotter.references_series import ReferencesSeries


class Blanks(ReferencesSeries):
    def _set_interpolated_values(self, iso, fit, ans, p_uys, p_ues):
        for ui, v, e in zip(ans, p_uys, p_ues):
            if v is not None and e is not None:
                ui.set_temporary_blank(iso, v, e, fit)

    def _get_reference_data(self, po):
        name = po.name
        ys = [ai.isotopes[name].get_intensity() for ai in self.sorted_references]
        return ys

    def _get_current_data(self, po):
        name = po.name
        return [ai.isotopes[name].blank.uvalue for ai in self.sorted_analyses]

# ============= EOF =============================================
