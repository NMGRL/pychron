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
from traits.api import HasTraits, Str, Bool, Property, List, Int

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pychron_constants import FIT_TYPES, FIT_ERROR_TYPES


class Fit(HasTraits):
    name = Str
    # use = Bool
    # show = Bool
    fit = Str
    fit_types = Property
    error_type = Str
    error_types = List(FIT_ERROR_TYPES)

    #     fit = Enum(FIT_TYPES)
    # valid = Property(depends_on=('fit, use, show'))
    # save = Property(depends_on=('fit', 'use'))

    def fit_tuple(self):
        return self.fit.lower(), self.error_type

    # def _get_save(self):
    #     return self.use and self.fit

    def _fit_default(self):
        return self.fit_types[0]

    def _get_fit_types(self):
        return FIT_TYPES

        # def _get_valid(self):
        #     return self.use and self.show and self.fit
        #
        # def _show_changed(self):
        #     self.use = self.show
        #
        # def traits_view(self):
        #     v = View(HGroup(
        #         UItem('name', style='readonly'),
        #         UItem('show'),
        #         UItem('fit',
        #               editor=EnumEditor(name='fit_types'),
        #               enabled_when='show',
        #               width=-50, ),
        #         UItem('use')))
        #     return v


class FilterFit(Fit):
    filter_outliers = Bool
    filter_outlier_iterations = Int
    filter_outlier_std_devs = Int
    truncate = Str
    include_baseline_error = Bool

    def _filter_outliers_changed(self):
        if self.filter_outliers:
            if not self.filter_outlier_iterations:
                self.filter_outlier_iterations = 1
            if not self.filter_outlier_std_devs:
                self.filter_outlier_std_devs = 2


class IsoFilterFit(FilterFit):
    use_sniff = Bool
    time_zero_offset = Int(0)

# ============= EOF =============================================
