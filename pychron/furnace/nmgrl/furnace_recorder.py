import time
import os
from traits.api import Instance, Float

from pychron.furnace.nmgrl.furnace_controller import NMGRLFurnaceController
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph
from pychron.managers.stream_graph_manager import StreamGraphManager
from pychron.paths import paths
from traitsui.api import View, UItem, Item, HGroup, VGroup


class SimpleFurnace(StreamGraphManager):
    controller = Instance(NMGRLFurnaceController)
    setpoint = Float(auto_set=False, enter_set=True)
    recording_period = Float(10)  # in minutes
    temperature_readback = Float
    _last_update = None
    _recorded_flow_state = None

    def _setpoint_changed(self, new):
        self.set_setpoint(new)

    def set_pid_parameters(self, v):
        self.debug('setting pid parameters for {}'.format(v))
        from pychron.hardware.eurotherm.base import get_pid_parameters
        params = get_pid_parameters(v)
        if params:
            _, param_str = params
            self._pid_str = param_str
            self.controller.set_pid(param_str)

    def set_setpoint(self, v):
        self.debug('set setpoint={}'.format(v))
        self.set_pid_parameters(v)
        self.graph.record(v)
        self.graph.record(v)
        if self.controller:
            self.controller.set_setpoint(v)
            d = self.graph.get_data(axis=1)

            if not self.graph_y_auto:
                self.graph.set_y_limits(min_=min(d.min(), v) * 0.9, max_=max(d.max(), v) * 1.1)

            self.graph.redraw()

    def _controller_default(self):
        c = NMGRLFurnaceController(name='controller',
                                   configuration_dir_name='furnace')
        return c

    def _update_scan(self):
        d = self.controller.get_summary(verbose=False)
        if d:
            state = d.get('h2o_state')
            if state in (0, 1):
                # self.water_flow_led.state = 2 if state else 0
                self.water_flow_state = 2 if state else 0
            else:
                self.water_flow_state = 1

            write_water_state = self._recorded_flow_state is None or self._recorded_flow_state != self.water_flow_state

            if write_water_state:
                with open(os.path.join(paths.data_dir, 'furnace_water.txt'), 'a') as wfile:
                    wfile.write('{},{}\n'.format(time.time(), state))
                    self._recorded_flow_state = state

            response = d.get('response')
            output = d.get('output')
            if response is not None:
                self.temperature_readback = response
            if output is not None:
                self.output_percent_readback = output

            self._update_scan_graph(response, output, d['setpoint'])

    def _update_scan_graph(self, response, output, setpoint):
        x = None
        update = False
        if response is not None:
            x = self.graph.record(response, series=1, track_y=False)
            update = True

        if output is not None:
            self.graph.record(output, x=x, series=0, plotid=1, track_y=False)
            update = True

        if update:
            ss = self.graph.get_data(plotid=0, axis=1)
            if len(ss) > 1:
                xs = self.graph.get_data(plotid=0)
                xs[-1] = x
                self.graph.set_data(xs, plotid=0)
            else:
                self.graph.record(setpoint, x=x, track_y=False)

            if self.graph_y_auto:
                temp_plot = self.graph.plots[0].plots['plot0'][0]
                setpoint_plot = self.graph.plots[0].plots['plot1'][0]

                temp_data = temp_plot.value.get_data()
                setpoint_data = setpoint_plot.value.get_data()

                ma = max(temp_data.max(), setpoint_data.max())
                if self.setpoint == 0:
                    mi = 0
                else:
                    mi = min(setpoint_data.min(), temp_data.min())

                self.graph.set_y_limits(min_=mi, max_=ma, pad='0.1', plotid=0)

            if self._recording:
                if not self._last_update or time.time() - self._last_update > (self.recording_period * 60):
                    self._last_update = time.time()
                    self.record_data_manager.write_to_frame((x, response or 0, output or 0))

    def _graph_factory(self, *args, **kw):
        g = TimeSeriesStreamStackedGraph()
        # g.plotcontainer.padding_top = 5
        # g.plotcontainer.padding_right = 5
        g.new_plot(xtitle='Time (s)', ytitle='Temp. (C)', padding_top=5, padding_left=75, padding_right=5)
        g.set_scan_width(600, plotid=0)
        g.set_data_limits(1.8 * 600, plotid=0)

        # setpoint
        g.new_series(plotid=0, line_width=2,
                     render_style='connectedhold')
        # response
        g.new_series(plotid=0)

        g.new_plot(ytitle='Output (%)', padding_top=5, padding_left=75, padding_right=5)
        g.set_scan_width(600, plotid=1)
        g.set_data_limits(1.8 * 600, plotid=1)
        g.new_series(plotid=1)
        g.set_y_limits(min_=-2, max_=102, plotid=1)

        return g

    def start_update(self):
        self.info('Start update')
        self.reset_scan_timer(func=self._update_scan)

    def _start_recording(self):
        self._recording = True
        self.record_data_manager = dm = self._record_data_manager_factory()
        dm.new_frame(directory=paths.furnace_scans_dir)
        dm.write_to_frame(('time', 'temperature', 'output'))
        self._start_time = time.time()

    def _stop_recording(self):
        self._recording = False

    def traits_view(self):
        v = View(VGroup(Item('setpoint'), Item('temperature_readback', style='readonly'),
                        HGroup(UItem('start_record_button'), UItem('stop_record_button'),
                               Item('recording_period', label='Period (m)')),
                        UItem('graph', style='custom')),

                 title='Standalone Furnace Controller')
        return v


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build(os.path.join(os.path.expanduser('~'), 'PychronFurnace'))
    logging_setup('furnace_record', use_archiver=False)
    f = SimpleFurnace()
    f.bootstrap()
    f.controller.bootstrap()
    f.start_update()
    f.configure_traits()
