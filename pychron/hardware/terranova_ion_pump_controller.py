# ===============================================================================
# Copyright 2011 Jake Ross
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



#============= enthought library imports =======================
from traits.api import Float
from traitsui.api import View, VGroup

#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice

CR = chr(13)
STX = '*'


class TerraNovaIonPumpController(CoreDevice):
    pressure = Float
    voltage = Float
    current = Float

    def read_hv_state(self):
        qry = 'HV'
        self._read_bool(qry)

    def read_pressure(self):
        qry = 'PR'
        self._update_value(qry, 'pressure')

    def read_voltage(self):
        qry = 'VO'
        self._update_value(qry, 'voltage')

    def read_current(self):
        qry = 'CU'
        self._update_value(qry, 'current')

    def _update_value(self, qry, attr):
        r = self._read_float(qry)

        if r is not None:
            setattr(self, attr, r)

#============= views ===================================
    def traits_view(self):
        v = View(VGroup('pressure',
                      'current',
                      'voltage'))
        return v

    def _build_commad(self, cmd, value):
        cksum = '00'
        cmd = ''.join([STX, self.address, cmd, ':', value, cksum, CR])
        return cmd

    def _build_query(self, qry):
        cksum = '00'
        qry = ''.join([STX, self.address, qry, '?,', cksum, CR])
        return qry

    def _parse_response(self, r, kind='float'):
        print r

        args = r.split(':')
        if args[0] == 'OK':
            value = args[1].split(',')[0]
            if kind == 'float':
                resp = float(value)
            elif kind == 'bool':
                resp = value == 'On'
            return resp

    def _read_float(self, qry):
        qry = self._build_query(qry)
        r = self.ask(qry)
        r = self._parse_response(r)
        return r

    def _read_bool(self, qry):
        qry = self._build_query(qry)
        r = self.ask(qry)
        r = self._parse_response(r, kind='bool')
        return r

if __name__ == '__main__':
    t = TerraNovaIonPumpController()
    t.configure_traits()
#============= EOF ====================================
