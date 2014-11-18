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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Float
from traitsui.api import View, VGroup, HGroup, Item
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.fits.filter_fit_selector import FilterFitSelector


class IsoEvoFitSelector(FilterFitSelector):
    default_error_type = 'SEM'

    time_zero_offset = Float

    def load_fits(self, keys, fits):
        bs = ['{}bs'.format(ki) for ki in keys]
        # bfs = ['average' for fi in fits]
        vs = keys + bs + ['Ar40/Ar39', 'Ar40/Ar38', 'Ar40/Ar36', 'Ar37/Ar39', 'Ar36/Ar39']
        fits = fits + [('linear', 'sem', {}),
                       ('linear', 'sem', {}),
                       ('linear', 'sem', {}),
                       ('linear', 'sem', {}),
                       ('linear', 'sem', {})]
        super(IsoEvoFitSelector, self).load_fits(vs, fits)

    def traits_view(self):
        v = View(VGroup(
            self._get_auto_group(),
            self._get_toggle_group(),
            HGroup(Item('time_zero_offset',
                        label='Time Zero Offset (s)',
                        tooltip='Subtract the "Time Zero Offset" from the data points')),
            self._get_fit_group()))
        return v

#============= EOF =============================================
