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
from traitsui.api import EnumEditor, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import AppearanceSubOptions, SubOptions, MainOptions, object_column, checkbox_column


class IsoEvoSubOptions(SubOptions):
    def traits_view(self):
        return self._make_view(Item('goodness_threshold'))


class IsoEvoAppearanceOptions(AppearanceSubOptions):
    pass


class IsoEvoMainOptions(MainOptions):
    def _get_columns(self):
        cols = [object_column(name='name', editable=False),
                checkbox_column(name='plot_enabled', label='Plot'),
                checkbox_column(name='save_enabled', label='Save'),
                object_column(name='fit',
                              editor=EnumEditor(name='fit_types'),
                              width=75),
                object_column(name='error_type',
                              editor=EnumEditor(name='error_types'),
                              width=75, label='Error'),
                checkbox_column(name='filter_outliers', label='Out.'),
                object_column(name='filter_outlier_iterations', label='Iter.'),
                object_column(name='filter_outlier_std_devs', label='SD'),
                object_column(name='truncate', label='Trunc.'),
                checkbox_column(name='include_baseline_error', label='Inc. BsErr')]
        return cols


VIEWS = {'main': IsoEvoMainOptions,
         'isoevo': IsoEvoSubOptions,
         'appearance': IsoEvoAppearanceOptions}
# ============= EOF =============================================
