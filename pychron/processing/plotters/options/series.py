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
from traitsui.api import View, Item, TableEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.processing.plotters.options.base import BasePlotterOptions
from pychron.processing.plotters.options.option import FitPlotterOption


class SeriesOptions(BasePlotterOptions):
    def load_aux_plots(self, ref):
        def f(kii):
            ff = FitPlotterOption(name=kii)
            ff.trait_set(use=False, fit='')
            return ff

        keys = ref.isotope_keys
        keys.extend(['{}bs'.format(ki) for ki in keys])
        if 'Ar40' in keys:
            if 'Ar39' in keys:
                keys.append('Ar40/Ar39')
            if 'Ar36' in keys:
                keys.append('Ar40/Ar36')

        keys.append('PC')
        ap = [f(k) for k in keys]
        self.trait_set(aux_plots=ap)

    def traits_view(self):
        cols = [
            CheckboxColumn(name='use'),
            ObjectColumn(name='name'),
            ObjectColumn(name='fit', width=135),
            ObjectColumn(name='scale', label='Y Scale'),
            #               ObjectColumn(name='height'),
            #               CheckboxColumn(name='x_error', label='X Error'),
            CheckboxColumn(name='y_error', label='Y Error'),
        ]
        aux_plots_grp = Item('aux_plots',
                             style='custom',
                             show_label=False,

                             editor=TableEditor(columns=cols,
                                                sortable=False,
                                                deletable=False,
                                                reorderable=False
                             ))
        v = View(aux_plots_grp)
        return v


#============= EOF =============================================
