# ===============================================================================
# Copyright 2018 ross
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

from traits.api import Enum, Float, Property, List, Int
from traitsui.api import Item, UItem, HGroup, VGroup, Spring

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.graph.plot_record import PlotRecord
from pychron.graph.stream_graph import StreamStackedGraph
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice
import re
from time import sleep, time
import string

IDN_RE = re.compile(r'\w{4},\w{8},\w{7}\/[\w\#]{7},\d.\d')

PRED_RE = re.compile(r'(?P<name>[A-Za-z])')


class RangeTest:
    def __init__(self, r, test):
        self._r = int(r)
        self._test = test
        self._attr = None
        match = PRED_RE.search(test)
        if match:
            self._attr = match.group('name')

    def test(self, v):
        if self._attr and eval(self._test, {self._attr: float(v)}):
            return self._r


class BaseLakeShoreController(CoreDevice):
    units = Enum('C', 'K')
    scan_func = 'update'

    input_a = Float
    input_b = Float
    setpoint1 = Float(auto_set=False, enter_set=True)
    setpoint1_readback = Float
    setpoint2 = Float(auto_set=False, enter_set=True)
    setpoint2_readback = Float
    range_tests = List
    num_inputs = Int
    ionames = List
    iolist = List
    iomap = List

    graph_klass = StreamStackedGraph

    def load_additional_args(self, config):
        self.set_attribute(config, 'units', 'General', 'units', default='K')

        # [Range]
        # 1=v<10
        # 2=10<v<30
        # 3=v>30

        if config.has_section('Range'):
            items = config.items('Range')

        else:
            items = [(1, 'v<10'), (2, '10<v<30'), (3, 'v>30')]

        if items:
            self.range_tests = [RangeTest(*i) for i in items]

        if config.has_section('IOConfig'):
            iodict = dict(config.items('IOConfig'))
            self.num_inputs = int(iodict['num_inputs'])
            for i, tag in enumerate(string.ascii_lowercase[:self.num_inputs]):
                try:
                    self.ionames.append(iodict['input_{}_name'.format(tag)])
                except ValueError:
                    self.ionames.append('input_{}'.format(tag))
                self.iolist.append('input_{}'.format(tag))
                mapsetpoint = iodict['input_{}'.format(tag)]
                if mapsetpoint.lower() == 'none':
                    self.iomap.append(None)
                else:
                    self.iomap.append(mapsetpoint)
        else:
            self.num_inputs = 2
            self.iolist = ['input_a', 'input_b']
            self.ionames = ['', '', '', '']
            self.iomap = ['setpoint1', 'setpoint2', 'setpoint3', 'setpoint4']

        return True

    def initialize(self, *args, **kw):
        self.communicator.write_terminator = chr(10)  # line feed \n
        return super(BaseLakeShoreController, self).initialize(*args, **kw)

    def test_connection(self):
        self.tell('*CLS')
        resp = self.ask('*IDN?')
        return bool(IDN_RE.match(resp))

    def update(self, **kw):
        for tag in self.iolist:
            func = getattr(self, 'read_{}'.format(tag))
            v = func(**kw)
            setattr(self, tag, v)

        for tag in self.iomap:
            v = self.read_setpoint(tag)
            setattr(self, '{}_readback'.format(tag), v)
        return self._update_hook()

    def _update_hook(self):
        return self.input_a

    def setpoints_achieved(self, tol=1):
        for i, (tag, key) in enumerate(zip(self.iomap, string.ascii_lowercase)):
            idx = i + 1
            v = self._read_input(key, self.units)
            if tag is not None:
                setpoint = getattr(self, tag)
                if abs(v - setpoint) > tol:
                    return
                else:
                    self.debug('setpoint {} achieved'.format(idx))

        return True

    @get_float(default=0)
    def read_setpoint(self, output, verbose=False):
        if output is not None:
            return self.ask('SETP? {}'.format(re.sub('[^0-9]', '', output)), verbose=verbose)

    def set_setpoints(self, *setpoints, block=False, delay=1):
        for i, v in enumerate(setpoints):
            if v is not None:
                idx = i + 1
                setattr(self, 'setpoint{}'.format(idx), v)

        if block:
            delay = max(0.5, delay)
            tol = 1
            if isinstance(block, (int, float)):
                tol = block

            while 1:
                if self.setpoints_achieved(tol):
                    break
                time.sleep(delay)

    def set_setpoint(self, v, output=1):
        self.set_range(v, output)
        self.tell('SETP {},{}'.format(output, v))

    def set_range(self, v, output):
        # if v <= 10:
        #     self.tell('RANGE {},{}'.format(output, 1))
        # elif 10 < v <= 30:
        #     self.tell('RANGE {},{}'.format(output, 2))
        # else:
        #     self.tell('RANGE {},{}'.format(output, 3))

        for r in self.range_tests:
            ra = r.test(v)
            if ra:
                self.tell('RANGE {},{}'.format(output, ra))
                break

        sleep(1)

    def read_input(self, v, **kw):
        if isinstance(v, int):
            v = string.ascii_lowercase[v - 1]
        return self._read_input(v, self.units, **kw)

    def read_input_a(self, **kw):
        return self._read_input('a', self.units, **kw)

    def read_input_b(self, **kw):
        return self._read_input('b', self.units, **kw)

    @get_float(default=0)
    def _read_input(self, tag, mode='C', verbose=False):
        return self.ask('{}RDG? {}'.format(mode, tag), verbose=verbose)

    def _setpoint1_changed(self):
        self.set_setpoint(self.setpoint1, 1)

    def _setpoint2_changed(self):
        self.set_setpoint(self.setpoint2, 2)

    def _update_hook(self):
        r = PlotRecord((self.input_a, self.input_b), (0, 1), ('a', 'b'))
        return r

    def get_control_group(self):
        grp = VGroup(Spring(height=10, springy=False),
                     HGroup(Item('input_a', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                            Item('setpoint1'),
                            UItem('setpoint1_readback', editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False)),
                     HGroup(Item('input_b', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                            Item('setpoint2'),
                            UItem('setpoint2_readback', editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False)))
        return grp

    def graph_builder(self, g, **kw):
        g.plotcontainer.spacing = 10
        g.new_plot(xtitle='Time (s)', ytitle='InputA',
                   padding=[100, 10, 0, 60])
        g.new_series()

        g.new_plot(ytitle='InputB',
                   padding=[100, 10, 60, 0])
        g.new_series(plotid=1)
# ============= EOF =============================================
