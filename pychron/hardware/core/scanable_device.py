# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Event, Property, Any, Bool, Float, Str, Instance, List
from traitsui.api import HGroup, VGroup, Item, spring, ButtonEditor
# ============= standard library imports ========================
import os
import time
from threading import Lock
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import generate_datetimestamp
from pychron.database.data_warehouse import DataWarehouse
from pychron.graph.plot_record import PlotRecord
from pychron.hardware.core.alarm import Alarm
from pychron.hardware.core.viewable_device import ViewableDevice
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.paths import paths


class ScanableDevice(ViewableDevice):
    scan_button = Event
    scan_label = Property(depends_on='_scanning')

    alarms = List(Alarm)

    is_scanable = Bool(False)
    scan_func = Any
    scan_lock = None
    timer = None
    scan_period = Float(1000, enter_set=True, auto_set=False)
    scan_width = Float(5, enter_set=True, auto_set=False)
    scan_units = 'ms'
    record_scan_data = Bool(False)
    graph_scan_data = Bool(False)
    scan_path = Str
    auto_start = Bool(False)
    scan_root = Str
    scan_name = Str

    graph = Instance('pychron.graph.graph.Graph')
    graph_ytitle = Str
    graph_klass = None

    data_manager = Instance(CSVDataManager)
    time_dict = dict(ms=1, s=1000, m=60000, h=3600000)

    _scanning = Bool(False)
    _auto_started = False

    def is_scanning(self):
        return self._scanning

    def _scan_path_changed(self):
        self.scan_root = os.path.split(self.scan_path)[0]
        self.scan_name = os.path.basename(self.scan_path)

    # ===============================================================================
    # streamin interface
    # ===============================================================================
    def setup_scan(self):
        self.debug('setup scan')
        # should get scan settings from the config file not the initialization.xml
        config = self.get_configuration()
        if config.has_section('Scan'):
            enabled = self.config_get(config, 'Scan', 'enabled', cast='boolean', optional=True, default=True)
            self.is_scanable = enabled
            if enabled:
                self.set_attribute(config, 'auto_start', 'Scan', 'auto_start', cast='boolean', default=False)
                self.set_attribute(config, 'scan_period', 'Scan', 'period', cast='float')
                self.set_attribute(config, 'scan_width', 'Scan', 'width', cast='float')
                self.set_attribute(config, 'scan_units', 'Scan', 'units')
                self.set_attribute(config, 'record_scan_data', 'Scan', 'record', cast='boolean')
                self.set_attribute(config, 'graph_scan_data', 'Scan', 'graph', cast='boolean')

                func = self.config_get(config, 'Scan', 'function', optional=True)
                if func:
                    self.scan_func = func

    def setup_alarms(self):
        self.debug('setup alarms')
        config = self.get_configuration()
        if config.has_section('Alarms'):
            for opt in config.options('Alarms'):
                self.alarms.append(Alarm(
                    name=opt,
                    alarm_str=config.get('Alarms', opt)))

    def _scan_hook(self, *args, **kw):
        pass

    def _scan_(self, *args):
        if self.scan_func:

            try:
                v = getattr(self, self.scan_func)(verbose=False)
            except AttributeError as e:
                print('exception', e)
                return

            if v is not None:
                # self.debug('current scan value={}'.format(v))
                self.current_scan_value = str(v)

                # self.debug('current scan func={}, value ={}'.format(self.scan_func, v))

                x = None
                if self.graph_scan_data:
                    if isinstance(v, tuple):
                        x = self.graph.record_multiple(v)
                    elif isinstance(v, PlotRecord):
                        for pi, d in zip(v.plotids, v.data):

                            if isinstance(d, tuple):
                                x = self.graph.record_multiple(d, plotid=pi)
                            else:
                                x = self.graph.record(d, plotid=pi)
                        v = v.as_data_tuple()

                    else:
                        x = self.graph.record(v)
                        v = (v,)

                if self.record_scan_data:
                    self.debug('recording scan data')
                    if x is None:
                        x = time.time()

                    ts = generate_datetimestamp()
                    self.data_manager.write_to_frame((ts, '{:<8s}'.format('{:0.2f}'.format(x))) + v)

                self._scan_hook(v)

            else:
                '''
                    scan func must return a value or we will stop the scan
                    since the timer runs on the main thread any long comms timeouts
                    slow user interaction
                '''
                if self._no_response_counter > 3:
                    self.timer.Stop()
                    self.info('no response. stopping scan func={}'.format(self.scan_func))
                    self._scanning = False
                    self._no_response_counter = 0

                else:
                    self._no_response_counter += 1

    def scan(self, *args, **kw):
        if self.scan_lock is None:
            self.scan_lock = Lock()

        with self.scan_lock:
            self._scan_(*args, **kw)

    def start_scan(self, period=None):
        """

        :param period: delapy between triggers in milliseconds
        :return:
        """
        if self.timer is not None:
            self.timer.Stop()
            self.timer.wait_for_completion()

        self._scanning = True
        self.info('Starting scan')

        d = self.scan_width * 60 #* 1000/self.scan_period
        # print self.scan_width, self.scan_period
        if self.graph_scan_data:
            self.info('Graph recording enabled')
            self.debug('scan width ={}'.format(d))
            self.graph.set_scan_widths(d)

        if self.record_scan_data:
            self.info('Recording scan enabled')
            dm = self.data_manager
            dm.delimiter = '\t'

            dw = DataWarehouse(root=paths.device_scan_dir)
            dw.build_warehouse()

            dm.new_frame(base_frame_name=self.name, directory=dw.get_current_dir())
            self.scan_path = dm.get_current_path()

        if period is None:
            period = self.scan_period * self.time_dict[self.scan_units]

        from pychron.core.helpers.timer import Timer
        self.timer = Timer(period, self.scan)
        self.info('Scan started func={} period={}'.format(self.scan_func, period))

    def stop_scan(self):
        self.info('Stoppiing scan')

        self._scanning = False
        if self.timer is not None:
            self.timer.Stop()

        if self.data_manager:
            self.data_manager.close_file()
        self._auto_started = False
        self.info('Scan stopped')

    def _get_scan_label(self):
        return 'Start' if not self._scanning else 'Stop'

    def _scan_button_fired(self):
        self.debug('scan button fired. scanning {}'.format(self._scanning))
        if self._scanning:
            self.stop_scan()
        else:
            self.start_scan()

    def _scan_period_changed(self):
        if self._scanning:
            self.stop_scan()
            self.start_scan()

    def _data_manager_default(self):
        return CSVDataManager()

    def _graph_default(self):
        from pychron.graph.time_series_graph import TimeSeriesStreamGraph

        klass = self.graph_klass
        if not klass:
            klass = TimeSeriesStreamGraph

        g = klass()
        self.graph_builder(g)

        return g

    def graph_builder(self, g, **kw):
        g.new_plot(padding=[50, 5, 5, 35],
                   zoom=True,
                   pan=True,
                   **kw)

        g.set_y_title(self.graph_ytitle)
        g.set_x_title('Time')
        g.new_series()

    def get_additional_tabs(self):
        g = VGroup(Item('graph', show_label=False, style='custom'),
                   VGroup(Item('scan_func', label='Function', style='readonly'),

                          HGroup(Item('scan_period', label='Period ({})'.format(self.scan_units)), spring),
                          Item('current_scan_value', style='readonly')),
                   VGroup(
                       HGroup(Item('scan_button', editor=ButtonEditor(label_value='scan_label'),
                                   show_label=False),
                              spring),
                       Item('scan_root',
                            style='readonly',
                            label='Scan directory',
                            visible_when='object.record_scan_data'),
                       Item('scan_name', label='Scan name',
                            style='readonly',
                            visible_when='object.record_scan_data'),
                       visible_when='object.is_scanable'),

                   label='Scan')
        return g,
        # v = super(ScanableDevice, self).current_state_view()
        # v.content.content.content.append(g)
        # return v

        # ============= EOF =============================================
