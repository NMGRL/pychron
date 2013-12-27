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
from traitsui.api import View, Item, HGroup, spring

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.fits.filter_fit_selector import FilterFitSelector


class IsoEvoFitSelector(FilterFitSelector):

    def load_fits(self, keys, fits):
        bs = ['{}bs'.format(ki) for ki in keys]
        bfs = ['average_SEM' for fi in fits]

        super(IsoEvoFitSelector, self).load_fits(keys + bs, fits + bfs)

    # def traits_view(self):
    #     v = View(
    #         self
    #         self._get_fit_group())
    #     return v

        #============= EOF =============================================
