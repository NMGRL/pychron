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
from traits.api import Bool, Int, Str
from traitsui.api import EnumEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.processing.fits.fit import Fit
from pychron.processing.fits.fit_selector import FitSelector


class FilterFit(Fit):
    use_filter = Bool
    filter_iterations = Int
    filter_std_devs = Int
    truncate= Str

    def _use_filter_changed(self):
        if self.use_filter:
            if not self.filter_iterations:
                self.filter_iterations = 1
            if not self.filter_std_devs:
                self.filter_std_devs = 2


class FilterFitSelector(FitSelector):
    fit_klass = FilterFit

    def _get_columns(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='show'),
                ObjectColumn(name='fit',
                             editor=EnumEditor(name='fit_types'),
                             width=75),
                ObjectColumn(name='error_type',
                             editor=EnumEditor(name='error_types'),
                             width=75),
                CheckboxColumn(name='use_filter'),
                ObjectColumn(name='filter_iterations', label='Filter Iter.'),
                ObjectColumn(name='filter_std_devs', label='Filter SD'),
                ObjectColumn(name='truncate', label='Trunc.'),
                CheckboxColumn(name='use', label='Save')]

        return cols

        #============= EOF =============================================
