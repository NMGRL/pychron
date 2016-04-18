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
import os
import pickle

from traits.api import Bool, Float, Property, Instance, Event, Button, Enum
# ============= standard library imports ========================
from numpy import Inf
# ============= local library imports  ==========================
from pychron.core.helpers.timer import Timer
from pychron.graph.graph import Graph
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.managers.manager import Manager
from pychron.paths import paths


class StreamGraphManager(Manager):
    graph = Instance(Graph)
    graph_scale = Enum('linear', 'log')

    graph_y_auto = Bool

    graph_ymin = Property(Float, depends_on='_graph_ymin')
    graph_ymax = Property(Float, depends_on='_graph_ymax')
    _graph_ymin = Float
    _graph_ymax = Float
    graph_scan_width = Float(enter_set=True, auto_set=False)  # in minutes
    clear_button = Event

    start_record_button = Button
    stop_record_button = Button

    snapshot_button = Button
    snapshot_output = Enum('png', 'pdf')

    # add_visual_marker_button = Button('Add Visual Marker')
    # marker_text = Str
    add_marker_button = Button('Add Marker')
    clear_all_markers_button = Button
    use_vertical_markers = Bool

    record_label = Property(depends_on='_recording')
    _recording = Bool(False)
    record_data_manager = Instance(CSVDataManager)

    timer = None
    update_period = 1

    def reset_scan_timer(self, func=None):
        self.info('reset scan timer')
        self.timer = self._timer_factory(func=func)

    def load_settings(self):
        self.info('load scan settings')

        params = self.get_settings()
        if params:
            self._set_graph_attrs(params)
            self._load_settings(params)
        else:
            self.warning('no scan settings')

    def dump_settings(self):
        self.info('dump scan settings')
        p = os.path.join(paths.hidden_dir, '{}.p'.format(self.settings_name))
        with open(p, 'wb') as wfile:
            d = dict()
            for ki in self.graph_attr_keys:
                d[ki] = getattr(self, ki)
            self._dump_settings(d)
            pickle.dump(d, wfile)

    def get_settings(self):
        p = os.path.join(paths.hidden_dir, '{}.p'.format(self.settings_name))
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                try:
                    return pickle.load(f)
                except (pickle.PickleError, EOFError):
                    self.warning('Failed unpickling scan settings file {}'.format(p))
                    return
        else:
            self.warning('No scan settings file {}'.format(p))

    # private
    def _get_graph_y_min_max(self, plotid=0):
        mi, ma = Inf, -Inf
        for k, plot in self.graph.plots[plotid].plots.iteritems():
            plot = plot[0]
            if plot.visible:
                ys = plot.value.get_data()
                ma = max(ma, max(ys))
                mi = min(mi, min(ys))
        return mi, ma

    def _update_scan_graph(self):
        pass

    def _timer_factory(self, func=None):

        if func is None:
            func = self._update_scan_graph

        if self.timer:
            self.timer.Stop()
            self.timer.wait_for_completion()

        mult = 1000
        return Timer(self.update_period * mult, func)

    def _graph_factory(self, *args, **kw):
        raise NotImplementedError

    def _record_data_manager_factory(self):
        return CSVDataManager()

    def _reset_graph(self):
        self.graph = self._graph_factory()

        # trigger a timer reset. set to 0 then default
        self.reset_scan_timer()

    def _update_graph_limits(self, name, new):
        if 'high' in name:
            self._graph_ymax = max(new, self._graph_ymin)
        else:
            self._graph_ymin = min(new, self._graph_ymax)

    # handlers
    def _graph_y_auto_changed(self, new):
        p = self.graph.plots[0]
        if not new:
            p.value_range.low_setting = self.graph_ymin
            p.value_range.high_setting = self.graph_ymax
        self.graph.redraw()

    def _graph_scale_changed(self, new):
        p = self.graph.plots[0]
        p.value_scale = new
        self.graph.redraw()

    def _graph_scan_width_changed(self):
        g = self.graph
        n = self.graph_scan_width
        print 'asdasd', n
        n = max(n, 1 / 60.)
        mins = n * 60
        g.set_data_limits(1.8 * mins)
        g.set_scan_widths(mins)

    def _clear_all_markers_button_fired(self):
        self.graph.clear_markers()

    def _start_record_button_fired(self):
        self._start_recording()
        self._recording = True

    def _stop_record_button_fired(self):
        self._stop_recording()
        self._recording = False

    def _snapshot_button_fired(self):
        self.debug('snapshot button fired')
        self.graph.save()

    def _add_marker_button_fired(self):
        xs = self.graph.plots[0].data.get_data('x0')

        self.record_data_manager.write_to_frame(tuple(' '))
        self.graph.add_vertical_rule(xs[-1])

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _validate_graph_ymin(self, v):
        try:
            v = float(v)
            if v < self.graph_ymax:
                return v
        except ValueError:
            pass

    def _validate_graph_ymax(self, v):
        try:
            v = float(v)
            if v > self.graph_ymin:
                return v
        except ValueError:
            pass

    def _get_graph_ymin(self):
        return self._graph_ymin

    def _get_graph_ymax(self):
        return self._graph_ymax

    def _set_graph_ymin(self, v):
        if v is not None:
            self._graph_ymin = v
            p = self.graph.plots[0]
            p.value_range.low_setting = v
            self.graph.redraw()

    def _set_graph_ymax(self, v):
        if v is not None:
            self._graph_ymax = v
            p = self.graph.plots[0]
            p.value_range.high_setting = v
            self.graph.redraw()

    def _get_record_label(self):
        return 'Record' if not self._recording else 'Stop'

    @property
    def graph_attr_keys(self):
        return ['graph_scale',
                'graph_ymin',
                'graph_ymax',
                'graph_y_auto',
                'graph_scan_width']

    def _dump_settings(self):
        pass

    def _set_graph_attrs(self, params):
        for pi in self.graph_attr_keys:
            try:
                setattr(self, pi, params[pi])
            except KeyError, e:
                print 'sm load settings', pi, e

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _graph_default(self):
        g = self._graph_factory()
        # self.graphs.append(g)
        return g


# ============= EOF =============================================



