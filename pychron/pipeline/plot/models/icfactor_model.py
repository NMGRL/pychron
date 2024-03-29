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
from pychron.pipeline.plot.models.figure_model import FigureModel
from pychron.pipeline.plot.panels.icfactor_panel import ICFactorPanel


class ICFactorModel(FigureModel):
    _panel_klass = ICFactorPanel
    references_name = Str

    def _panel_factory(self, *args, **kw):
        p = super(ICFactorModel, self)._panel_factory(*args, **kw)
        p.references_name = self.references_name
        return p


# ============= EOF =============================================
