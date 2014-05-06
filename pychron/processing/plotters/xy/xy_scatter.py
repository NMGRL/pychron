#===============================================================================
# Copyright 2014 Jake Ross
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
from chaco.array_data_source import ArrayDataSource
from traits.api import Instance

#============= standard library imports ========================
from numpy import array
#============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.graph.error_bar_overlay import ErrorBarOverlay
# from pychron.processing.plotters.xy.xy_scatter_tool import XYScatterTool
from pychron.processing.plotter_options_manager import XYScatterOptionsManager
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
from pychron.pychron_constants import NULL_STR


class XYScatterEditor(GraphEditor):
    update_graph_on_set_items = True
    tool = None
    plotter_options_manager = Instance(XYScatterOptionsManager, ())

    def rebuild(self):
        self.rebuild_graph()

    def load_fits(self, refiso):
        pass

    def load_tool(self, tool=None):
        pass

    def dump_tool(self):
        pass

    def _normalize(self, vs, scalar):
        vs -= vs[0]
        return vs / scalar

    def _pretty(self, v):
        if '_' in v:
            v = ' '.join(map(str.capitalize, v.split('_')))
        return v

    def _rebuild_graph(self):
        ans = self.analyses
        if ans:
            g = self.graph
            g.new_plot()

            options = self.plotter_options_manager.plotter_options

            i_attr = options.index_attr
            v_attr = options.value_attr

            if i_attr == 'timestamp' or v_attr == 'timestamp':
                ans = sorted(ans, key=lambda x: x.timestamp)

            uxs = [ai.get_value(i_attr) for ai in ans]
            uys = [ai.get_value(v_attr) for ai in ans]
            xs = array([nominal_value(ui) for ui in uxs])
            ys = array([nominal_value(ui) for ui in uys])

            if i_attr == 'timestamp':
                xtitle = 'Normalized Analysis Time'
                xs = self._normalize(xs, options.index_time_scalar)
            else:
                xtitle = i_attr

            if v_attr == 'timestamp':
                ytitle = 'Normalized Analysis Time'
                ys = self._normalize(ys, options.value_time_scalar)
            else:
                ytitle = v_attr

            ytitle = self._pretty(ytitle)
            xtitle = self._pretty(xtitle)

            kw = options.get_marker_dict()
            fit = options.fit
            fit = fit if fit != NULL_STR else False

            s, _ = g.new_series(x=xs, y=ys, fit=fit, type='scatter', **kw)

            if options.index_error:
                exs = array([std_dev(ui) for ui in uxs])
                n = options.index_nsigma
                self._add_error_bars(s, exs, 'x', n, end_caps=options.index_end_caps)
                xmn, xmx = min(xs - exs), max(xs + exs)
            else:
                xmn, xmx = min(xs), max(xs)

            if options.value_error:
                eys = array([std_dev(ui) for ui in uys])
                n = options.value_nsigma
                self._add_error_bars(s, eys, 'y', n, end_caps=options.value_end_caps)
                ymn, ymx = min(ys - eys*n), max(ys + eys*n)
            else:
                ymn, ymx = min(ys), max(ys)

            g.set_x_limits(xmn, xmx, pad='0.1')
            g.set_y_limits(ymn, ymx, pad='0.1')

            g.set_x_title(xtitle)
            g.set_y_title(ytitle)

    def _add_error_bars(self, scatter, errors, axis, nsigma,
                        end_caps,
                        visible=True):
        ebo = ErrorBarOverlay(component=scatter,
                              orientation=axis,
                              nsigma=nsigma,
                              visible=visible,
                              use_end_caps=end_caps)

        scatter.underlays.append(ebo)
        setattr(scatter, '{}error'.format(axis), ArrayDataSource(errors))
        return ebo

#============= EOF =============================================

