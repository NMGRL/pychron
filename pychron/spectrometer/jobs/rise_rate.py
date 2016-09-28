# ===============================================================================
# Copyright 2012 Jake Ross
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
from numpy import polyfit, linspace
from traits.api import HasTraits, Float, Any, Button, Bool, List, Color
from traitsui.api import View, Item, spring, ButtonEditor, HGroup, \
    VGroup, UItem
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.graph.guide_overlay import GuideOverlay
from spectrometer_task import SpectrometerTask


class ResultsAdapter(TabularAdapter):
    columns = [('N', 'cnt'), ('Endpoints', 'endpoints'), ('Linear', 'linear')]


class Result(HasTraits):
    linear = Float
    endpoints = Float

    def calculate(self, xs, ys, rise, starttime):
        ti = xs[-1]
        run = (ti - starttime) / 60.
        rrendpoints = rise / run

        rrfit = polyfit(linspace(0, run, len(ys)), ys, 1)[0]
        self.endpoints = rrendpoints
        self.linear = rrfit
        return rrendpoints, rrfit, ti, run


class RiseRate(SpectrometerTask):
    result_fit = Float
    result_endpoints = Float
    results = List
    graph = Any
    clear_button = Button('Clear')
    clear_results_button = Button('Clear Results')
    calculated = Bool

    end_color = Color('red')
    start_color = Color('black')

    _start_time = None
    _start_intensity = None

    def _clear_results_button_fired(self):
        self.results = []

    def _clear_button_fired(self):
        self.calculated = False

        plot = self.graph.plots[0]
        underlays = [oi for oi in plot.underlays if not isinstance(oi, GuideOverlay)]
        plot.underlays = underlays
        self.graph.redraw()

    def _execute(self):
        self.result = 0
        self._start_time = self.graph.get_data()[-1]
        self._start_intensity = self._get_intensity()
        self.graph.add_vertical_rule(self._start_time, color=self.start_color)
        self.graph.redraw()

    def _calculate_rise_rate(self):
        rise = self._get_intensity() - self._start_intensity

        xs = self.graph.get_data()
        ys = self.graph.get_data(axis=1, series=self.detector.series_id)
        ys = ys[xs >= self._start_time]

        result = Result(cnt=len(self.results) + 1)
        rrendpoints, rrfit, ti, run = result.calculate(xs, ys, rise, self._start_time)

        self.graph.add_vertical_rule(ti, color=self.end_color)
        self.graph.redraw()
        self.calculated = True
        self.info('calculated rise rate '
                  'endpoint={:0.2f}(rise/run= {:0.3f}/{:0.3f}), '
                  'linear={:0.3f}'.format(rrendpoints, rise, run, rrfit))

        self.result_endpoints = rrendpoints
        self.result_fit = rrfit

        self.results.append(result)

    def _get_intensity(self):
        return self.spectrometer.get_intensity(self.detector.name)

    def _end(self):
        self._calculate_rise_rate()

    def traits_view(self):
        v = View(VGroup(HGroup(spring,
                               Item('clear_button', show_label=False,
                                    enabled_when='calculated'),
                               Item('execute_button',
                                    editor=ButtonEditor(label_value='execute_label'),
                                    show_label=False)),

                        VGroup(Item('result_endpoints', style='readonly',
                                    format_str='%0.3f',
                                    label='Rise Rate endpoints (fA/min)'),
                               Item('result_fit', style='readonly',
                                    format_str='%0.3f',
                                    label='Rise Rate linear fit  (fA/min)')),
                        HGroup(UItem('clear_results_button')),
                        UItem('results',
                              editor=myTabularEditor(operations=[],
                                                     editable=False,
                                                     adapter=ResultsAdapter()))))
        return v

# ============= EOF =============================================
