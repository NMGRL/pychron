# ===============================================================================
# Copyright 2018 ross
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
from traits.api import Int, Bool

from pychron.options.aux_plot import AuxPlot
from pychron.options.fit import FitOptions
from pychron.options.views.define_equilibration_views import VIEWS
from pychron.pychron_constants import MAIN, DISPLAY


class DefineEquilibrationAuxPlot(AuxPlot):
    equilibration_time = Int(100)


class DefineEquilibrationOptions(FitOptions):
    aux_plot_klass = DefineEquilibrationAuxPlot
    show_statistics = Bool(False)
    ncols = Int

    def initialize(self):
        self.subview_names = [MAIN, DISPLAY]

    def _get_subview(self, name):
        return VIEWS[name]
# ============= EOF =============================================
