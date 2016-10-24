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
from traits.api import Bool, Button
from traits.has_traits import on_trait_change
from traitsui.api import EnumEditor, ButtonEditor
from traitsui.api import HGroup, UItem

from pychron.processing.fits.fit import FilterFit
from pychron.processing.fits.fit_selector import ObjectColumn, CheckboxColumn, FitSelector


class FilterFitSelector(FitSelector):
    fit_klass = FilterFit
    filter_all_button = Button('Toggle Filter')
    filter_state = Bool

    inc_baseline_all_button = Button('Toggle Inc. Base')
    inc_baseline_state = Bool

    def _filter_all_button_fired(self):
        self.filter_state = not self.filter_state
        fs = self._get_fits()
        for fi in fs:
            fi.filter_outliers = self.filter_state

    def _inc_baseline_all_button_fired(self):
        self.inc_baseline_state = not self.inc_baseline_state
        fs = self._get_fits()
        for fi in fs:
            fi.include_baseline_error = self.inc_baseline_state

    def _get_toggle_group(self):
        g = HGroup(
            UItem('show_all_button', editor=ButtonEditor(label_value='show_all_label')),
            UItem('filter_all_button'),
            UItem('inc_baseline_all_button'),
            UItem('use_all_button'))
        return g

    @on_trait_change('fits:[error_type, filter_outliers, include_baseline_error]')
    def _handle_fit_attr_changed(self, obj, name, old, new):
        if self.command_key:
            for fi in self.fits:
                fi.trait_set(**{name: new})
            self.command_key = False

        if self.auto_update:
            if name in ('error_type', 'filter_outliers'):
                self.update_needed = True

    def _get_columns(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='show'),
                CheckboxColumn(name='use', label='Save'),
                ObjectColumn(name='fit',
                             editor=EnumEditor(name='fit_types'),
                             width=75),
                ObjectColumn(name='error_type',
                             editor=EnumEditor(name='error_types'),
                             width=75, label='Error'),
                CheckboxColumn(name='filter_outliers', label='Out.'),
                ObjectColumn(name='filter_iterations', label='Iter.'),
                ObjectColumn(name='filter_std_devs', label='SD'),
                ObjectColumn(name='truncate', label='Trunc.'),
                CheckboxColumn(name='include_baseline_error', label='Inc. BsErr')]

        return cols

        # ============= EOF =============================================
