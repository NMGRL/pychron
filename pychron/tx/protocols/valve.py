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
import random

from pychron.pychron_constants import EL_PROTOCOL
from pychron.tx.errors import DeviceConnectionErrorCode, InvalidGaugeErrorCode
from pychron.tx.protocols.base_valve import BaseValveProtocol
from pychron.tx.registry import FUNC_REGISTRY


def make_wrapper(func, postprocess):
    def wrapper(*args, **kw):
        """
        handler signature is self, manager, args, sender
        """

        ret = func(*args[1:], **kw)
        if postprocess:
            ret = postprocess(ret)
        return ret

    return wrapper


class ValveProtocol(BaseValveProtocol):
    manager_protocol = EL_PROTOCOL

    def _init_hook(self):
        for k, v in FUNC_REGISTRY.items():
            self.register_service(k, make_wrapper(*v))

        services = (('GetData', '_get_data'),
                    ('Read', '_read'),
                    ('Set', '_set'),
                    ('GetPressure', '_get_pressure'))

        self._register_services(services)

    def _get_data(self, data):
        if isinstance(data, dict):
            offset = data['value']
        else:
            offset = float(data)
        v = random.random() + offset
        return str(v)

    def _get_device(self, name, protocol=None, owner=None):
        dev = None
        if self._application is not None:
            if protocol is None:
                protocol = 'pychron.hardware.core.i_core_device.ICoreDevice'
            dev = self._application.get_service(protocol, 'name=="{}"'.format(name))
            if dev is None:
                # possible we are trying to get a flag
                m = self._manager
                if m:
                    dev = m.get_flag(name)
                    if dev is None:
                        dev = m.get_mass_spec_param(name)
                    else:
                        if owner:
                            dev.set_owner(str(owner))
        return dev

    def _get_error(self, data):
        return self._manager.get_error()

    def _set(self, data):
        if isinstance(data, dict):
            dname, value = data['device'], data['value']
        else:
            dname, value = data.split(' ')

        d = self._get_device(dname, owner=self._addr)
        # self.debug('Set {name} {value}', name=dname, value=value)
        if d is not None:
            # self.info('Set {name} to {value}', name=dname, value=value)
            result = d.set(value)
        else:
            result = DeviceConnectionErrorCode(dname, logger=self)

        return result

    def _read(self, data):
        if isinstance(data, dict):
            data = data['value']
        # self.debug('Read {data}', data=data)
        d = self._get_device(data, owner=self._addr)
        if d is not None:
            result = d.get(current=True)
        else:
            result = DeviceConnectionErrorCode(data, logger=self)
        return result

    def _get_pressure(self, data):
        """
        Get the pressure from ``controller``'s ``gauge``

        """

        manager = self._manager
        if isinstance(data, dict):
            controller, gauge = data['controller'], data['gauge']
        else:
            controller, gauge = data

        p = None
        if manager:
            p = manager.get_pressure(controller, gauge)

        if p is None:
            p = InvalidGaugeErrorCode(controller, gauge)

        return str(p)

# ============= EOF =============================================
