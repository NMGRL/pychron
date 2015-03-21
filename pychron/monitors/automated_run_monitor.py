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
from traits.api import HasTraits, List, Str, Any, Array, Bool, Float
# ============= standard library imports ========================
from numpy import vstack, array
# ============= local library imports  ==========================
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

    _fatal_errors = List

    def monitor(self):
        self.clear_errors()
        return super(AutomatedRunMonitor, self).monitor()

    def clear_errors(self):
        self._fatal_errors = []

    def has_fatal_error(self):
        """
            return True if any of the checks yielded a fatal error
        """
        if self._fatal_errors:
            self.warning('fatal errors: {}'.format('\n'.join(self._fatal_errors)))
            return True

    def _load_hook(self, config):
        self.checks = []
        ok = True
        for section in config.sections():
            if section.startswith('Check'):
                pa = self.config_get(config, section, 'parameter')

                if 'Pressure' in pa and not ',' in pa:
                    self.warning_dialog(
                        'Invalid Pressure Parameter in AutomatedRunMonitor, '
                        'need to specify controller and name, e.g. Pressure, <controller>,<gauge_name>')
                    ok = False
                    continue

                else:
                    r = self.config_get(config, section, 'rule', default='')
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
                self._fatal_errors.append(ci.message)
                # if self.automated_run:
                # if self.automated_run.isAlive():
                #         self.automated_run.cancel()
                #         self.warning_dialog(ci.message)

                ok = False
                break

            if self.get_error():
                ok = False
                break

        return ok

    def get_error(self):
        pass

    def get_pressure(self, controller, name):
        elm = self.automated_run.extraction_line_manager
        p = elm.get_pressure(controller, name)
        return p

    def set_additional_connections(self, cons):
        pass

    def _get_value(self, q):
        elm = self.automated_run.extraction_line_manager
        dev = elm.get_device(q)
        if dev:
            return dev.get()


class RemoteAutomatedRunMonitor(AutomatedRunMonitor):
    handle = None
    handles = List
    # def __init__(self, host, port, kind, *args, **kw):
    # super(RemoteAutomatedRunMonitor, self).__init__(*args, **kw)
    #     self.handle = EthernetCommunicator()
    #     self.handle.host = host
    #     self.handle.port = port
    #     self.handle.kind = kind

    def load_additional_args(self, config, *args, **kw):
        sec = 'Communications'
        if sec in config.sections:
            h = self.config_get(config, sec, 'host')
            p = self.config_get(config, sec, 'port')
            k = self.config_get(config, sec, 'kind')
            self.handle = self._handle_factory(h, p, k)
            self.handles.append(self.handle)

    def _handle_factory(self, h, p, k):
        ec = EthernetCommunicator()
        ec.trait_set(host=h, port=p, kind=k)
        return ec

    def set_additional_connections(self, cons):
        for c in cons:
            if c.monitorable:
                h = self._handle_factory(c.host, c.port, c.kind)
                self.handles.append(h)

    def get_error(self):
        error = False
        for h in self.handles:
            e = h.ask('GetError')
            if e:
                self._fatal_errors.append(e)
                error = True

        return error

    def get_pressure(self, controller, name):
        cmd = 'GetPressure {}, {}'.format(controller, name)
        p = self.handle.ask(cmd)
        return self._float(p, default=1.0)

    def _get_value(self, name):
        p = self.handle.ask('Read {}'.format(name))
        return self._float(p)

    def _float(self, p, default=0.0):
        try:
            p = float(p)
        except (ValueError, TypeError):
            p = default
        return p

# ============= EOF =============================================
