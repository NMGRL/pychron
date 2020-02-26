# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Dict
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class QtegraDevice(CoreDevice):
    """
        qtegra_monitor.cfg

        [General]
        name=Jan
        [Communications]
        type=ethernet
        host=localhost
        port=1069
        [Parameters]
        manometer=MKS 1000

        dashboard.yaml
        - name: JanMonitor
          enabled: True
          device: qtegra_monitor
          values:
            - name: JanTrapCurrent
              func: get_trap_current
              enabled: True
              period: on_change
            - name: JanEmission
              func: get_emission
              enabled: True
              period: on_change
            - name: JanDecabinTemp
              func: get_decabin_temperature
              enabled: True
              period: on_change
    """
    _parameters = Dict
    # auto_handle_response = False
    def load_additional_args(self, config):

        section = 'Parameters'
        if config.has_section(section):
            for opt in config.options(section):
                v = config.get(section, opt)
                self._parameters[opt] = v

        return True

    def __getattr__(self, item):
        if item.startswith('read_'):
            tag = item[5:]
            param = self._parameters.get(tag)
            if param:
                return self.get_parameter(param)

    def read_decabin_temperature(self, **kw):
        # v = self.ask('GetParameter Temp1')
        # v = self._parse_response(v)
        v = self.get_parameter('Temp1')
        if v is not None:
            self.last_response = str(round(v, 1))

        return v

    def read_trap_current(self, **kw):
        return self.get_parameter('Trap Current Readback')

    def read_emission(self, **kw):
        return self.get_parameter('Source Current Readback')

    def read_hv(self):
        v = self.ask('GetHV')
        return self._parse_response(v)

    def get_parameter(self, m):
        v = self.ask('GetParameter {}'.format(m))
        return self._parse_response(v)

    def _parse_response(self, v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return self.get_random_value()



# ============= EOF =============================================
