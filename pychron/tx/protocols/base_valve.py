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
from pychron.tx.errors import InvalidValveErrorCode, InvalidArgumentsErrorCode, ValveSoftwareLockErrorCode, \
    ValveActuationErrorCode
from pychron.tx.protocols.service import ServiceProtocol


class BaseValveProtocol(ServiceProtocol):
    manager_protocol = None

    def __init__(self, application, addr):
        ServiceProtocol.__init__(self)

        self._application = application
        man = None
        if application:
            if self.manager_protocol is None:
                raise NotImplementedError

            man = application.get_service(self.manager_protocol)

        self._manager = man
        self._addr = addr

        self._register_base_services()
        self._init_hook()

    # private
    def _init_hook(self):
        pass

    def _register_base_services(self):
        services = (('Open', '_open'),
                    ('Close', '_close'),
                    ('GetValveState', '_get_valve_state'),
                    ('GetStateChecksum', '_get_state_checksum'),
                    ('GetValveStates', '_get_valve_states'),
                    ('GetValveLockStates', '_get_valve_lock_states'),
                    ('GetValveLockState', '_get_valve_lock_state'),
                    ('GetValveOwners', '_get_valve_owners'))
        self._register_services(services)

    # command handlers
    def _get_valve_state(self, data):
        if isinstance(data, dict):
            data = data['value']
        result = self._manager.get_valve_state(data)
        if result is None:
            result = InvalidValveErrorCode(data)
        return result

    def _open(self, data):
        """
        Open a valve. Valve name e.g. A
        if vname ends with 'Flag' interpret this command as ``Set``

        :param vname: name of valve
        :return: OK or ErrorCode
        """
        if isinstance(data, dict):
            data = data['value']

        # intercept flags
        if data.endswith('Flag'):
            r = self.set(data, 1)
            return bool(r)

        manager = self._manager
        result, change = manager.open_valve(data, sender_address=self._addr)

        if result is True:
            result = 'OK' if change else 'ok'
        elif result is None:
            result = InvalidArgumentsErrorCode('Open', data)
        elif result == 'software lock enabled':
            result = ValveSoftwareLockErrorCode(data)
        else:
            result = ValveActuationErrorCode(data, 'open')

        return result

    def _close(self, data):
        """
        Close a valve. Valve name e.g. A
        if vname ends with 'Flag' interpret this command as ``Set``

        :param vname: name of valve
        :return: OK or ErrorCode
        """
        if isinstance(data, dict):
            data = data['value']

        # intercept flags
        if data.endswith('Flag'):
            r = self.set(data, 0)
            return bool(r)

        result, change = self._manager.close_valve(data, sender_address=self._addr)
        if result is True:
            result = 'OK' if change else 'ok'
        elif result is None:
            result = InvalidArgumentsErrorCode('Close', data, logger=self)
        elif result == 'software lock enabled':
            result = ValveSoftwareLockErrorCode(data, logger=self)
        else:
            result = ValveActuationErrorCode(data, 'close', logger=self)

        return result

    def _get_state_checksum(self, data):
        """
        """
        if isinstance(data, dict):
            data = data['value']

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
        if isinstance(data, dict):
            data = data['value']

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
        if isinstance(data, dict):
            data = data['value']

        result = self._manager.get_software_lock(data)
        return result

    def _get_valve_owners(self, data):
        result = self._manager.get_valve_owners()
        return result

# ============= EOF =============================================
