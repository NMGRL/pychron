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
from pychron.pychron_constants import EL_PROTOCOL
from pychron.remote_hardware.registry import MetaHandler
from pychron.tx.errors import InvalidValveErrorCode, ValveActuationErrorCode, ValveSoftwareLockErrorCode, \
    InvalidArgumentsErrorCode, DeviceConnectionErrorCode, InvalidGaugeErrorCode
from pychron.tx.protocols.service import ServiceProtocol


class ValveProtocol(ServiceProtocol):
    __metaclass__ = MetaHandler

    def __init__(self, application, addr):
        ServiceProtocol.__init__(self)
        # self._application = application
        man = application.get_service(EL_PROTOCOL)
        self._manager = man
        self._addr = addr

        services = (('Read', '_read'),
                    ('Set', '_set'),
                    ('Open', '_open'),
                    ('Close', '_close'),
                    ('GetValveState', '_get_valve_state'),
                    ('GetStateChecksum', '_get_state_checksum'),
                    ('GetValveStates', '_get_valve_states'),
                    ('GetValveLockStates', '_get_valve_lock_states'),
                    ('GetValveLockState', '_get_valve_lock_state'),
                    ('GetValveOwners', '_get_valve_owners'),
                    ('GetPressure', '_get_pressure'),

                    # dynamically registered. need better way to load these
                    ('GetFaults', 'GetFaults'),
                    ('GetCoolantOutTemperature', 'GetCoolantOutTemperature'),
                    ('GetPneumaticsPressure', 'GetPneumaticsPressure'))
        self._register_services(services)

    def _register_services(self, services):
        for name, cb in services:
            if isinstance(cb, str):
                cb = getattr(self, cb)
            self.register_service(name, cb)

    def _get_device(self, name, protocol=None, owner=None):
        dev = None
        if self.application is not None:
            if protocol is None:
                protocol = 'pychron.hardware.core.i_core_device.ICoreDevice'
            dev = self.application.get_service(protocol, 'name=="{}"'.format(name))
            if dev is None:
                # possible we are trying to get a flag
                m = self._manager
                if m:
                    dev = m.get_flag(name)
                    if dev is None:
                        dev = m.get_mass_spec_param(name)
                    else:
                        if owner:
                            dev.set_owner(owner)
        return dev


    def _get_error(self, data):
        return self._manager.get_error()

    def _set(self, dname, value):
        d = self._get_device(dname, owner=self._addr)
        if d is not None:
            self.info('Set {} to {}'.format(d.name,
                                            value))
            result = d.set(value)
        else:
            result = DeviceConnectionErrorCode(dname, logger=self)

        return result

    def _read(self, data):
        d = self._get_device(data, owner=self._addr)
        if d is not None:
            result = d.get(current=True)
        else:
            result = DeviceConnectionErrorCode(data, logger=self)
        return result

    def _get_valve_state(self, data):
        result = self._manager.get_valve_state(data)
        if result is None:
            result = InvalidValveErrorCode(data)
        return result

    def _open(self, vname):
        """
        Open a valve. Valve name e.g. A
        if vname ends with 'Flag' interpret this command as ``Set``

        :param vname: name of valve
        :return: OK or ErrorCode
        """
        # intercept flags
        if vname.endswith('Flag'):
            r = self.set(vname, 1)
            return bool(r)

        manager = self._manager
        result, change = manager.open_valve(vname, sender_address=self._addr)

        if result is True:
            result = 'OK' if change else 'ok'
        elif result is None:
            result = InvalidArgumentsErrorCode('Open', vname)
        elif result == 'software lock enabled':
            result = ValveSoftwareLockErrorCode(vname)
        else:
            result = ValveActuationErrorCode(vname, 'open')

        return result

    def _close(self, vname):
        """
        Close a valve. Valve name e.g. A
        if vname ends with 'Flag' interpret this command as ``Set``

        :param vname: name of valve
        :return: OK or ErrorCode
        """
        # intercept flags
        if vname.endswith('Flag'):
            r = self.set(vname, 0)
            return bool(r)

        result, change = self._manager.close_valve(vname, sender_address=self._addr)
        if result is True:
            result = 'OK' if change else 'ok'
        elif result is None:
            result = InvalidArgumentsErrorCode('Close', vname, logger=self)
        elif result == 'software lock enabled':
            result = ValveSoftwareLockErrorCode(vname, logger=self)
        else:
            result = ValveActuationErrorCode(vname, 'close', logger=self)

        return result

    def _get_state_checksum(self, data):
        """

        """
        result = self._manager.get_state_checksum(data)
        return result

    def _get_valve_state(self, data):
        """
        Get the state (True,False) of the valve.

        - True == valve open
        - False == valve closed

        :param vname: name of valve
        :return: True, False, or InvalidValveErrorCode
        """
        result = self._manager.get_valve_state(data)
        if result is None:
            result = InvalidValveErrorCode(data)
        return result

    def _get_valve_states(self, data):
        """
        Get all the valve states::

            # 0 == close
            # 1 == open
            A0,B1,C0

        :return: valve state str
        """
        result = self._manager.get_valve_states()
        return result

    def _get_valve_lock_states(self, data):
        """
        Get all the valve lock states::

            # 0 == unlocked
            # 1 == locked
            A0,B1,C0

        :return: valve lock str
        """
        result = self._manager.get_valve_lock_states()
        return result

    def _get_valve_lock_state(self, data):
        """
        Get the lock state (True,False) of the valve.

        - True == valve locked
        - False == valve unlocked

        :param vname: name of valve
        :return: True, False
        """
        result = self._manager.get_software_lock(data)
        return result

    def _get_valve_owners(self, data):
        result = self._manager.get_valve_owners()
        return result

    def _get_pressure(self, data):
        """
        Get the pressure from ``controller``'s ``gauge``

        """
        manager = self._manager
        controller, gauge = data
        p = None
        if manager:
            p = manager.get_pressure(controller, gauge)

        if p is None:
            p = InvalidGaugeErrorCode(controller, gauge)

        return str(p)

# ============= EOF =============================================
