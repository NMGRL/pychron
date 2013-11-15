#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, List, Str, Any, Array, Bool, Float
#============= standard library imports ========================
from numpy import vstack, array
#============= local library imports  ==========================
from pychron.monitors.monitor import Monitor
from pychron.hardware.core.communicators.ethernet_communicator import EthernetCommunicator
import time


class Check(HasTraits):
    name = Str
    parameter = Str
    action = Str
    rule = Str

    data = Array
    tripped = Bool
    message = Str

    def check_condition(self, v):

        vs = (time.time(), v)
        if not len(self.data):
            self.data = array([vs])
        else:
            self.data = vstack((self.data, vs))

        r = eval(self.rule, {'x': v})
        if r:
            self.message = 'Automated Run Check tripped. {} {} {}'.format(self.parameter, v, r)
            self.tripped = True

        return r


class AutomatedRunMonitor(Monitor):
    checks = List
    automated_run = Any

    pneumatics = Float
    ctemp = Float
    humidity = Float

    def _load_hook(self, config):
        self.checks = []
        ok = True
        for section in config.sections():
            if section.startswith('Check'):
                pa = self.config_get(config, section, 'parameter')

                if 'Pressure' in pa and not ',' in pa:
                    self.warning_dialog(
                        'Invalid Pressure Parameter in AutomatedRunMonitor, need to specify controller and name, e.g. Pressure, <controller>,<gauge_name>')
                    ok = False
                    continue

                else:
                    r = self.config_get(config, section, 'rule')
                    if 'x' not in r:
                        self.warning_dialog('Invalid rule. Include "x" variable. e.g "x>10"')
                        ok = False
                        continue

                    ch = Check(name=section,
                               parameter=pa,
                               rule=r)
                    self.checks.append(ch)

        return ok

    def _fcheck_conditions(self):
        ok = True
        for ci in self.checks:
            pa = ci.parameter
            if pa.startswith('Pressure'):
                pa, controller, name = pa.split(',')
                v = self.get_pressure(controller, name)
            else:
                v = self._get_value(pa)
                if v:
                    self.trait_set(**{ci.name.lower(): v})

            if ci.check_condition(v):
                if self.automated_run:
                    if self.automated_run.isAlive():
                        self.automated_run.cancel()
                        self.warning_dialog(ci.message)

                ok = False
                break

        return ok

    def _get_value(self, q):
        elm = self.automated_run.extraction_line_manager
        dev = elm.get_device(q)
        if dev:
            return dev.get()

    def get_pressure(self, controller, name):
        elm = self.automated_run.extraction_line_manager
        p = elm.get_pressure(controller, name)
        return p


class RemoteAutomatedRunMonitor(AutomatedRunMonitor):
    handle = None

    def __init__(self, host, port, kind, *args, **kw):
        super(RemoteAutomatedRunMonitor, self).__init__(*args, **kw)
        self.handle = EthernetCommunicator()
        self.handle.host = host
        self.handle.port = port
        self.handle.kind = kind

    def _get_value(self, name):
        p = self.handle.ask('Read {}'.format(name))
        return self._float(p)

    def get_pressure(self, controller, name):
        cmd = 'GetPressure {}, {}'.format(controller, name)
        p = self.handle.ask(cmd)
        return self._float(p, default=1.0)

    def _float(self, p, default=0.0):
        try:
            p = float(p)
        except (ValueError, TypeError):
            p = default
        return p

#============= EOF =============================================
