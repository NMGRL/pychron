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



# ============= enthought library imports =======================

# ============= standard library imports ========================

# ============= local library imports  ==========================

# ============= views ===================================
from pychron.hardware.gauges.base_gauge import BaseGauge

class BaseMKSGauge(BaseGauge):
    def set_transducer_identify(self, value):
        '''
        sends command to transducer to toggle LED pulse
        
        @type value: C{str}
        @param value: ON or OFF
        
        @see: L{MKSComs}
        '''
        m = 'Setting %s, %s identify to %s' % (self.name, self.address, value)
        q = self._build_command(self.address, 'pulse', value)
        self.info(m)

        self.ask(q)

    def _build_query(self, addr, typetag, setpointindex=1):
        '''
        build a query
        
        @type addr: C{s}
        @param addr: RS-485 address
        @type typetag: C{s}
        @param typetag: query type
        @rtype: C{s}
        @return: a valid HPS serial command
        '''
        if typetag == 'pressure':
            s = 'PR1'
        elif typetag == 'filament':
            s = 'FS'
        elif typetag == 'setpoint_value':
            s = 'SP%i' % setpointindex
        elif typetag == 'setpoint_state':
            s = 'SS%i' % setpointindex
        elif typetag == 'setpoint_enable':
            s = 'EN%i' % setpointindex
        rs = '@%s%s?;FF' % (addr, s)
        return rs


    def _build_command(self, addr, typetag, value, setpointindex=1):
        '''
        build a command
        
        @type addr: C{str}
        @param addr: RS-485 address
        @type typetag: C{str}
        @param typetag: query type
        @type value: C{str}
        @param value: command value
        @rtype: C{str}
        @return: a valid HPS serial command
        
        '''
        base = '@%s%s!%s;FF'
        if typetag == 'power':
            tag = 'FP'

            s = base % (addr, tag, ('ON' if value else 'OFF'))
            # s='@%s%s!%s;FF' % (addr, tag, value)
        elif typetag == 'address':
            tag = 'AD'
            s = base % (addr, tag, value)
        elif typetag == 'pulse':
            tag = 'TST'
            s = base % (addr, tag, value)

            # s='@%s%s!%s;FF' % (addr, tag, value)
        elif typetag == 'setpoint_enable':
            tag = 'EN%i' % setpointindex

            s = base % (addr, tag, ('ON' if value else 'OFF'))

        elif typetag == 'setpoint':
            tag = 'SP%i' % setpointindex
            # for some reason mks gauges 925 do not like x.xxe-xx as sci notation
            # likes x.xxe-x
            # convert value
            scivalue = '%0.2e' % value
            a, b = scivalue.split('e')
            sign = b[:1]
            ex = b[-1:]

            v = '%sE%s%s' % (a, sign, ex)

            s = '@%s%s!%s;FF' % (addr, tag, v)
            # s='@%s%s!%0.1e;FF' % (addr, tag, value)


        elif typetag == 'hysteresis':
            tag = 'SH%i' % setpointindex
            s = '@%s%s!%s;FF' % (addr, tag, value)

        elif typetag == 'degas':
            tag = 'DG'
            s = '@%s%s!%s;FF' % (addr, tag, ('ON' if value else 'OFF'))
        return s
    def _parse_response(self, type_, raw):
        '''
        parse a serial response
        
        @type_ type_: C{str}
        @param type_: the response type_
        @type_ raw: C{str}
        @param raw: the raw response C{str}
        @rtype: C{str or boolean}
        @return: a float for pressure, boolean otherwise
        '''
        if self.simulation:
            return float(self.get_random_value(0, 10))


        if raw == None:
            return

        data = raw.split(';')
        i = 0 if len(data) <= 2 else len(data) - 2

        value = data[i]
        si = value.find('ACK')
        if si == -1:
            self.warning('%s' % raw)
            return
        else:
            si += 3

        if type_ in ['pressure', 'setpoint_value']:
            v = value[si:]
            try:

                return float(v)
            except ValueError, e:
                self.warning(e)
                return

        elif type_ in ['filament', 'setpoint_enable']:
            return True if value[si:] == 'ON' else False

# ============= EOF ====================================
