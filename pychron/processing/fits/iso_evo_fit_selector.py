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
from traits.api import Button
from traitsui.api import View, Item, HGroup, UItem, spring

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.fits.filter_fit_selector import FilterFitSelector


class IsoEvoFitSelector(FilterFitSelector):
    plot_button = Button('Plot')

    def load_fits(self, keys, fits):
        bs = ['{}bs'.format(ki) for ki in keys]
        bfs = ['average_SEM' for fi in fits]

        super(IsoEvoFitSelector, self).load_fits(keys + bs, fits + bfs)

    def _plot_button_fired(self):
        self.update_needed = True

    def _auto_update_changed(self):
        self.update_needed = True

    def traits_view(self):
        v = View(
            HGroup(UItem('plot_button',
                         tooltip='Replot the isotope evolutions. \
This may take awhile if many analyses are selected'),
                   spring,
                   Item('auto_update',
                        label='Auto Plot',
                        tooltip='Should the plot refresh after each change ie. "fit" or "show". \
It is not advisable to use this option with many analyses')),
            self._get_fit_group())
        return v

        #============= EOF =============================================
