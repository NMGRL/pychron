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

# =============enthought library imports=======================

# =============standard library imports ========================
# import time
# =============local library imports  ==========================
from pychron.core import Q_
from pychron.hardware.core.core_device import CoreDevice


class AnalogDigitalConverter(CoreDevice):
    """
    """
    scan_func = 'read_device'
    read_voltage = 0

    def read_device(self, **kw):
        """
        """
        if self.simulation:
            return self.get_random_value()


class M1000(AnalogDigitalConverter):
    """
    """
    short_form_prompt = '$'
    long_form_prompt = '#'
    voltage_scalar = 1
    units = ''

    def load_additional_args(self, config):
        """
        """
        self.set_attribute(config, 'address', 'General', 'address')
        self.set_attribute(config, 'voltage_scalar', 'General',
                           'voltage_scalar', cast='float')
        self.set_attribute(config, 'units', 'General',
                           'units')
        if self.address is not None:
            return True

    def read_device(self, **kw):
        """
        """
        res = super(M1000, self).read_device(**kw)
        if res is None:
            cmd = 'RD'
            addr = self.address
            cmd = ''.join((self.short_form_prompt, addr, cmd))

            res = self.ask(cmd, **kw)
            res = self._parse_response_(res)
            if res is not None:
                res = Q_(res, self.units)

        return res

    def _parse_response_(self, r, form='$', type_=None):
        """
            typical response form
            short *+00072.00
            long *1RD+00072.00A4
        """
        func = lambda X: float(X[5:-2]) if form == self.long_form_prompt else float(X[2:])

        if r:
            if type_ == 'block':
                r = r.split(',')
                return [func(ri) for ri in r if ri is not '']
            else:
                return func(r)


class KeithleyADC(M1000):
    """
    """


class OmegaADC(M1000):
    """
    """
    def read_block(self):
        """
        """
        com = 'RB'
        r = self.ask(''.join((self.short_form_prompt, self.address, com)),
                          remove_eol=False, replace=[chr(13), ','])

        return self._parse_response_(r, type_='block')
# ============= EOF =====================================
