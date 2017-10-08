# ===============================================================================
# Copyright 2015 Jake Ross
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
from pychron.pychron_constants import FURNACE_PROTOCOL
from pychron.tx.protocols.base_valve import BaseValveProtocol


class FurnaceProtocol(BaseValveProtocol):
    manager_protocol = FURNACE_PROTOCOL

    def _init_hook(self):
        services = ('DumpSample', '_dump_sample',
                    'DumpComplete', '_dump_complete',
                    'SetSetpoint', '_set_setpoint')
        self._register_services(services)

    # command handlers
    def _dump_sample(self, data):
        if isinstance(data, dict):
            data = data['value']

        result = self._manager.dump_sample(data)
        return result

    def _dump_complete(self, data):
        result = self._manager.is_dump_complete()
        return result

    def _set_setpoint(self, data):
        if isinstance(data, dict):
            data = data['value']

        result = self._manager.set_setpoint(data)
        return result
# ============= EOF =============================================
