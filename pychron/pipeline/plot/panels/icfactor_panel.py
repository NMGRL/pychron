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
from traits.api import Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.panels.references_panel import ReferencesPanel
from pychron.pipeline.plot.plotter.icfactor import ICFactor


class ICFactorPanel(ReferencesPanel):
    _figure_klass = ICFactor
    references_name = Str

    def _figure_factory(self, *args, **kw):
        f = super(ICFactorPanel, self)._figure_factory(*args, **kw)
        f.references_name = self.references_name
        return f
# ============= EOF =============================================
