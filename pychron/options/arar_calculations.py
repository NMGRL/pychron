# ===============================================================================
# Copyright 2019 ross
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
from traits.api import Bool, Int, Enum, Float

from pychron.options.options import BaseOptions
from pychron.pychron_constants import ISOCHRON, SPECTRUM, IDEOGRAM, FLECK, MAHON, ERROR_TYPES


def clonable(klass, *args, **kw):
    return klass(clone=True, *args, **kw)


class ArArCalculationsOptions(BaseOptions):

    # isochron
    isochron_omit_non_plateau = clonable(Bool)
    isochron_exclude_non_plateau = clonable(Bool)

    # spectrum
    integrated_include_omitted = clonable(Bool)
    plateau_method = clonable(Enum(FLECK, MAHON))
    pc_nsteps = clonable(Int(3))
    pc_gas_fraction = clonable(Float(50))

    # ideogram
    error_calc_method = clonable(Enum(*ERROR_TYPES))
    probability_curve_kind = clonable(Enum('cumulative', 'kernel'))
    mean_calculation_kind = clonable(Enum('weighted mean', 'kernel'))

    def initialize(self):
        self.subview_names = [IDEOGRAM, SPECTRUM, ISOCHRON]

    def clone_to(self, options):
        for t in self.trait_names(clone=True):
            if hasattr(options, t):
                setattr(options, t, getattr(self, t))

    def _get_subview(self, name):
        from pychron.options.views.arar_calculation_views import VIEWS
        return VIEWS[name]
# ============= EOF =============================================
