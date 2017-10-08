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
from traits.api import Str, Bool, Float, Property, List, Color, Enum
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.views.isochron_views import INVERSE_ISOCHRON_VIEWS, ISOCHRON_VIEWS
from pychron.options.options import AgeOptions
from pychron.pychron_constants import FIT_ERROR_TYPES


class IsochronOptions(AgeOptions):
    subview_names = List(['Main', 'Appearance'])

    def get_subview(self, name):
        name = name.lower()
        klass = self._get_subview(name)
        obj = klass(model=self)
        return obj

    def _get_subview(self, name):
        return ISOCHRON_VIEWS[name]

    def _aux_plots_default(self):
        return [self.aux_plot_klass(plot_enabled=True, name='inverse_isochron')]


class InverseIsochronOptions(IsochronOptions):
    error_calc_method = Enum(*FIT_ERROR_TYPES)
    fill_ellipses = Bool(False)
    show_nominal_intercept = Bool(False)
    nominal_intercept_label = Str('Atm', enter_set=True, auto_set=False)
    nominal_intercept_value = Property(Float, depends_on='_nominal_intercept_value')
    _nominal_intercept_value = Float(295.5, enter_set=True, auto_set=False)

    invert_nominal_intercept = Bool(True)
    inset_marker_size = Float(1.0)
    inset_marker_color = Color('black')

    def _set_nominal_intercept_value(self, v):
        self._nominal_intercept_value = v

    def _get_nominal_intercept_value(self):
        v = self._nominal_intercept_value
        if self.invert_nominal_intercept:
            v **= -1
        return v

    def _get_subview(self, name):
        return INVERSE_ISOCHRON_VIEWS[name]

# ============= EOF =============================================
