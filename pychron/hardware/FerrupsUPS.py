#===============================================================================
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
#===============================================================================



#============= enthought library imports =======================
#============= standard library imports ========================
from datetime import datetime
#============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class FerrupsUPS(CoreDevice):
    scan_func = 'power_outage_scan'
    _power_out = False
    min_voltage_in = 5

    def _parse_response(self, resp):
        if self.simulation:
            resp = 'query', self.get_random_value(0, 10)

        elif resp is not None:
            resp = resp.strip()
            if '\n' in resp:
                EOF = '\n'
            else:
                EOF = '\r'
            resp = resp.split(EOF)
        return resp

    def _build_command(self, cmd):
        return cmd

    def _build_query(self, qry):
        return qry

    def set_password(self, pwd):
        qry = 'password {}'.format(pwd)
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)

    def get_parameter(self, pname, **kw):
        qry = 'pa {}'.format(pname)
        qry = self._build_query(qry)
        resp = self.ask(qry, **kw)
        return self._parse_response(resp)

    def get_parameters(self, start=1, end=2):
        qry = 'pa {} {}'.format(start, end)
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)

    def get_status(self):
        qry = 'status'
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)

    def get_ambient_temperature(self):
        qry = 'ambtemp'
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)

    def power_outage_scan(self):
        vin = self.get_voltage_in()
        if vin is None:
            return

        if vin < self.min_voltage_in:
            if self.application:
                tm = self.application.get_service('pychron.social.twitter_manager.TwitterManager')
                tm.post('Power Outage {} Vin= {}'.format(datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')), vin)
            self._power_out = True
        elif self._power_out:
            if self.application:
                tm = self.application.get_service('pychron.social.twitter_manager.TwitterManager')
                tm.post('Power Returned {} Vin= {}'.format(datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')), vin)
            self._power_out = False

        return vin

    def get_voltage_in(self):
        '''
            
        '''
        _query, resp = self.get_parameter(1, verbose=False)

        if self.simulation:
            # ensures True...  random 0-10
            return self.get_random_value() < 100
            # return not self._power_out

        vin = resp.split(' ')[-1]
        try:
            vin = float(vin)
        except ValueError, e:
            print e
            return

        return vin


if __name__ == '__main__':
    f = FerrupsUPS(name='ups')
    f.bootstrap()

    print f.check_power_outage()
#============ EOF ==============================================
