# ===============================================================================
# Copyright 2017 ross
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
from __future__ import absolute_import

import re

import six
from traitsui.api import View, Item, HGroup, Group, ListEditor, InstanceEditor

from pychron.core.ui.color_map_bar_editor import BarGaugeEditor
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.gauges.base_controller import BaseGauge, BaseGaugeController

ACK_RE = re.compile(r'@\d\d\dACK(?P<value>\d+.\d\dE-*\d\d);FF')
LO_RE = re.compile(r'@\d\d\dACKLO<E-11;FF')
NO_GAUGE_RE = re.compile(r'@\d\d\dACKNO_GAUGE;FF')
OFF_RE = re.compile(r'@\d\d\dACKOFF;FF')
PROTOFF_RE = re.compile(r'@\d\d\dACKPROT_OFF;FF')


class Gauge(BaseGauge):
    def traits_view(self):
        v = View(HGroup(Item('display_name', show_label=False, style='readonly',
                             width=-50, ),
                        Item('pressure',
                             format_str='%0.2e',
                             show_label=False,
                             style='readonly'),
                        Item('pressure',
                             show_label=False,
                             width=self.width,
                             editor=BarGaugeEditor(low=self.low,
                                                   high=self.high,
                                                   scale='power',
                                                   color_scalar=self.color_scalar,
                                                   width=self.width))))
        return v


class MKSController(BaseGaugeController, CoreDevice):
    gauge_klass = Gauge
    scan_func = 'update_pressures'

    def initialize(self, *args, **kw):
        for g in self.gauges:
            if int(g.channel) in (1, 3, 5):
                self._power_onoff(g.channel, True, verbose=True)
        return True

    def get_pressures(self, verbose=False):
        r = self._read_pressure(verbose=verbose)
        return r

    def _power_onoff(self, ch, state, verbose=False):
        cmd = 'CP{}!{}'.format(ch, 'ON' if state else 'OFF')
        cmd = self._build_command(cmd)
        self.ask(cmd, verbose=verbose)

    def _read_pressure(self, name=None, verbose=False):
        if name is not None:
            gauge = name
            if isinstance(gauge, (str, six.text_type)):
                gauge = self.get_gauge(name)
            channel = gauge.channel
        else:
            channel = 'Z'

        cmd = self._build_query('PR{}'.format(channel))
        r = self.ask(cmd, verbose=verbose)
        if r is not None:
            match = ACK_RE.match(r)
            if match:
                v = float(match.group('value'))
                return v

            for reg, ret in ((NO_GAUGE_RE, 0), (LO_RE, 1e-12), (PROTOFF_RE, 760), (OFF_RE, 1000)):
                match = reg.match(r)
                if match:
                    return ret

    def _build_query(self, cmd):
        return self._build_command('{}?'.format(cmd))

    def _build_command(self, cmd):
        return '@{}{};FF'.format(self.address, cmd)

    def load_additional_args(self, config, *args, **kw):
        self.address = self.config_get(config, 'General', 'address', optional=False)
        self.display_name = self.config_get(config, 'General', 'display_name', default=self.name)
        # self.mode = self.config_get(config, 'Communications', 'mode', default='rs485')
        self._load_gauges(config)
        return True

    def gauge_view(self):
        v = View(Group(Item('gauges', style='custom',
                            show_label=False,
                            editor=ListEditor(mutable=False,
                                              style='custom',
                                              editor=InstanceEditor())),
                       show_border=True,
                       label=self.display_name))
        return v

# ============= EOF =============================================
