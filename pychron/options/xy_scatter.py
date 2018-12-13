# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Str, List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.aux_plot import AuxPlot
from pychron.options.options import AuxPlotFigureOptions
from pychron.options.views.xy_scatter_views import VIEWS
from pychron.pychron_constants import MAIN, APPEARANCE


class XYScatterAuxPlot(AuxPlot):
    y_n = Str
    y_d = Str
    x_n = Str
    x_d = Str

    x_key = Str
    y_key = Str
    available_names = List

    def _make_ratio(self, axis):
        d = getattr(self, '{}_d'.format(axis))
        n = getattr(self, '{}_n'.format(axis))
        if d:
            if n:
                r = '{}/{}'.format(n, d)
            else:
                r = d
        elif n:
            r = n

        return r

    @property
    def ytitle(self):
        r = ''
        name = self.name
        if name == 'Ratio':
            r = self._make_ratio('y')
        elif name == 'Scatter':
            r = self.y_key
        return r

    @property
    def xtitle(self):
        r = ''
        name = self.name
        if name == 'TimeSeries':
            r = 'Time (hrs)'
        elif name == 'Ratio':
            self._make_ratio('x')
        elif name == 'Scatter':
            r = self.x_key

        return r


NAMES = ['Ratio', 'TimeSeries', 'Scatter']


class XYScatterOptions(AuxPlotFigureOptions):
    aux_plot_klass = XYScatterAuxPlot

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE]

    def set_names(self, isotope_keys):
        nn = isotope_keys + NAMES
        anames = isotope_keys + ['age', 'kca',
                                 'extract_value', 'extract_duration', 'cleanup_duration']
        for ai in self.aux_plots:
            if ai.name not in nn:
                ai.plot_enabled = False
                ai.save_enabled = False
                ai.name = ''

            ai.names = NAMES
            ai.available_names = anames

    def _get_subview(self, name):
        return VIEWS[name]

# ============= EOF =============================================
