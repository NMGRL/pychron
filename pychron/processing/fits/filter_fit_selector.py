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
from traits.api import Bool, Int, Str, Button
from traitsui.api import EnumEditor, ButtonEditor
from traitsui.api import HGroup, UItem

#============= standard library imports ========================
#============= local library imports  ==========================

from pychron.processing.fits.fit import Fit
from pychron.processing.fits.fit_selector import FitSelector, ObjectColumn, CheckboxColumn

class FilterFit(Fit):
    filter_outliers = Bool
    filter_iterations = Int
    filter_std_devs = Int
    truncate = Str
    include_baseline_error = Bool

    def _filter_outliers_changed(self):
        if self.filter_outliers:
            if not self.filter_iterations:
                self.filter_iterations = 1
            if not self.filter_std_devs:
                self.filter_std_devs = 2


class FilterFitSelector(FitSelector):
    fit_klass = FilterFit
    filter_all_button = Button('Toggle Filter')
    filter_state = Bool

    inc_baseline_all_button = Button('Toggle Inc. Base')
    inc_baseline_state = Bool

    def _filter_all_button_fired(self):
        self.filter_state = not self.filter_state
        for fi in self.fits:
            fi.filter_outliers = self.filter_state

    def _inc_baseline_all_button_fired(self):
        self.inc_baseline_state = not self.inc_baseline_state
        for fi in self.fits:
            fi.include_baseline_error = self.inc_baseline_state

    def _get_toggle_group(self):
        g = HGroup(
            UItem('show_all_button', editor=ButtonEditor(label_value='show_all_label')),
            UItem('filter_all_button'),
            UItem('inc_baseline_all_button'),
            UItem('use_all_button'))
        return g

    def _get_columns(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='show'),
                ObjectColumn(name='fit',
                             editor=EnumEditor(name='fit_types'),
                             width=75),
                ObjectColumn(name='error_type',
                             editor=EnumEditor(name='error_types'),
                             width=75),
                CheckboxColumn(name='filter_outliers', label='F. Outliers'),
                ObjectColumn(name='filter_iterations', label='F. Iter.'),
                ObjectColumn(name='filter_std_devs', label='F. SD'),
                ObjectColumn(name='truncate', label='Trunc.'),
                CheckboxColumn(name='include_baseline_error', label='Inc. BsErr'),
                CheckboxColumn(name='use', label='Save')]

        return cols

        #============= EOF =============================================
