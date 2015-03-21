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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class QtegraDevice(CoreDevice):
    def read_decabin_temperature(self):
        v = self.ask('GetDecabinTemperature', verbose=True)
        return self._parse_response(v)

    def read_emission(self):
        v = self.ask('GetEmission')
        return self._parse_response(v)

    def read_hv(self):
        v = self.ask('GetHV')
        return self._parse_response(v)

    def _parse_response(self, v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return self.get_random_value()


            # scan_func = 'read_temperature'
            # get_func = 'check_cdd'

            # def get(self, *args, **kw):
            #     try:
            #         func = getattr(self, self.get_func)
            #         return func()
            #     except AttributeError:
            #         pass
            # def load_additional_args(self, config):
            #     self.set_attribute(config, 'get_func', 'General', 'get_func')
            #     return True

            # def _build_command(self, cmd, *args, **kw):
            #     return cmd
            #
            # def _parse_response(self, resp):
            #     if resp is not None:
            #         resp = resp.strip()
            #     return resp
            #
            # def read_temperature(self, **kw):
            #     cmd = 'Get {}'.format('Temp1')
            #     x = self.repeat_command(cmd, **kw)
            #     return x
            #
            # def check_cdd(self, **kw):
            #     x = self.repeat_command('GetData', **kw)
            #     tags = [xi.split(':')[0].strip() for xi in x.split(',')]
            #     return 'CDD' in tags


# ============= EOF =============================================



