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
from enable.markers import marker_names
from traitsui.api import View, EnumEditor, UItem, HGroup, Item, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.table_editor import myTableEditor
from pychron.options.options import SubOptions, AppearanceSubOptions, MainOptions, object_column, checkbox_column
from pychron.pychron_constants import FIT_TYPES_INTERPOLATE, FIT_ERROR_TYPES, MAIN, APPEARANCE


class BlanksSubOptions(SubOptions):
    def traits_view(self):
        v = View()
        return v


class BlanksAppearance(AppearanceSubOptions):
    pass


class BlanksMainOptions(MainOptions):
    def _get_edit_view(self):
        v = View(VGroup(HGroup(Item('name', editor=EnumEditor(name='names')),
                               Item('fit', editor=EnumEditor(values=FIT_TYPES_INTERPOLATE)),
                               UItem('error_type', editor=EnumEditor(values=FIT_ERROR_TYPES))),
                        HGroup(UItem('marker', editor=EnumEditor(values=marker_names)),
                               Item('marker_size', label='Size'),
                               show_border=True, label='Marker'),
                        HGroup(Item('ymin', label='Min'),
                               Item('ymax', label='Max'),
                               show_border=True,
                               label='Y Limits'),
                        show_border=True))
        return v

    def _get_columns(self):
        return [object_column(name='name'),
                checkbox_column(name='plot_enabled', label='Enabled'),
                checkbox_column(name='save_enabled', label='Save'),
                object_column(name='fit',
                              editor=EnumEditor(values=FIT_TYPES_INTERPOLATE),
                              width=75),
                object_column(name='error_type',
                              editor=EnumEditor(values=FIT_ERROR_TYPES),
                              width=75, label='Error'),
                checkbox_column(name='filter_outliers', label='Out.'),
                object_column(name='filter_outlier_iterations', label='Iter.'),
                object_column(name='filter_outlier_std_devs', label='SD')]

    def traits_view(self):
        aux_plots_grp = UItem('aux_plots',
                              style='custom',
                              width=525,
                              editor=myTableEditor(columns=self._get_columns(),
                                                   sortable=False,
                                                   deletable=True,
                                                   clear_selection_on_dclicked=True,
                                                   orientation='vertical',
                                                   selected='selected',
                                                   selection_mode='rows',
                                                   edit_view=self._get_edit_view(),
                                                   reorderable=False))

        # rgrp = HGroup(Item('use_restricted_references'), show_border=True)
        atgrp = self._get_analysis_group()
        v = self._make_view(atgrp, aux_plots_grp)

        return v


class BlanksFitMatrix(SubOptions):
    def _get_columns(self):
        atypes = []
        for a in sorted(self.model.reference_types):
            label = ' '.join([ai.capitalize() for ai in a.split('_')])
            atypes.append((a.lower(), label))
        atypes = [checkbox_column(name='ref_{}'.format(atype), label=label) for atype, label in atypes]
        return [object_column(name='name')]+atypes

    def traits_view(self):
        aux_plots_grp = UItem('aux_plots',
                              style='custom',
                              width=525,
                              editor=myTableEditor(columns=self._get_columns(),
                                                   sortable=False,
                                                   deletable=True,
                                                   clear_selection_on_dclicked=True,
                                                   orientation='vertical',
                                                   selected='selected',
                                                   selection_mode='rows',
                                                   # edit_view=self._get_edit_view(),
                                                   reorderable=False))
        v = self._make_view(aux_plots_grp)
        return v


# ===============================================================
# ===============================================================
VIEWS = {MAIN.lower(): BlanksMainOptions,
         'blanks': BlanksSubOptions,
         APPEARANCE.lower(): BlanksAppearance,
         'fit matrix': BlanksFitMatrix}
# ===============================================================
# ===============================================================


# ============= EOF =============================================
