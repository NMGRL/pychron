# ===============================================================================
# Copyright 2019 ross
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

from traits.api import Instance, Float
from traitsui.api import View, UItem, HGroup, VGroup, ButtonEditor

import time

from pychron.execute_mixin import ExecuteMixin
from pychron.graph.stream_graph import StreamStackedGraph
from pychron.loggable import Loggable
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.paths import paths


class MeltingPointCalibrator(Loggable, ExecuteMixin):
    graph = Instance(StreamStackedGraph)
    setpoint = Float(enter_set=True, auto_set=False)
    record_data_manager = None
    detector = 'L2(CDD)'

    def setup(self):
        self.record_data_manager = CSVDataManager()
        self.record_data_manager.new_frame(directory=paths.device_scan_dir)
        self.graph = StreamStackedGraph()
        self.graph.new_plot()
        self.graph.new_series()
        self.graph.new_plot()
        self.graph.new_series(plotid=1)

        dl = 1.8*600
        self.graph.set_data_limits(dl)
        self.graph.set_scan_widths(600)

    def _do_execute(self):
        self.setup()
        self.laser.enable_laser()
        period = 1
        st = time.time()
        while self.executing:
            self._iter(time.time() - st)
            time.sleep(period)

        self.laser.disable_laser()
        self.record_data_manager.close_file()

    # private
    def _setpoint_changed(self, new):
        self.laser.extract(new)

    def _iter(self, t):
        intensity = self.spectrometer_manager.get_intensity(self.detector)
        temperature = self.laser.get_pyrometer_temperature()

        self._record(t, intensity, temperature)
        self._graph(t, intensity, temperature)

    def _graph(self, t, intensity, temperature):
        self.graph.record(intensity, x=t, plotid=0, track_x=True, track_y=True)
        self.graph.record(temperature, x=t, plotid=1, track_x=True, track_y=True)

    def _record(self, t, intensity, temperature):
        self.record_data_manager.write_to_frame((t, intensity, temperature))

    def traits_view(self):
        tgrp = HGroup(UItem('execute', editor=ButtonEditor(label_value='execute_label')), UItem('setpoint'))
        ggrp = VGroup(UItem('graph', style='custom'))

        v = View(VGroup(tgrp, ggrp), resizable=True, title='Melting Point Calibration')
        return v

# ============= EOF =============================================
