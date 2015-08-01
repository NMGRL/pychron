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
from twisted.internet import defer
from twisted.internet.protocol import Protocol
# ============= local library imports  ==========================
from pychron.pychron_constants import EL_PROTOCOL
from pychron.remote_hardware.errors import InvalidValveErrorCode, InvalidGaugeErrorCode, InvalidArgumentsErrorCode, \
    ValveSoftwareLockErrorCode, ValveActuationErrorCode, DeviceConnectionErrorCode
from pychron.tx.exceptions import ServiceNameError, ResponseError


def default_err(failure):
    failure.trap(BaseException)
    return failure


def service_err(failure):
    failure.trap(ServiceNameError)
    return failure


def response_err(failure):
    failure.trap(ResponseError)
    return failure


def nargs_err(failure):
    failure.trap(ValueError)
    return InvalidArgumentsErrorCode(str(failure.value))


class ServiceProtocol(Protocol):
    def __init__(self, *args, **kw):
        # super(ServiceProtocol, self).__init__(*args, **kw)
        self._services = {}
        self._delim = ' '

    def dataReceived(self, data):

        service = self._get_service(data)
        if service:
            self._get_response(service, data)

            # else:
            #     self.transport.write('Invalid request: {}'.format(data))

            # self.transport.loseConnection()

    def register_service(self, service_name, success, err=None):
        """

        """

        if err is None:
            err = default_err

        d = defer.Deferred()
        if not isinstance(success, (list, tuple)):
            success = (success,)

        for si in success:
            d.addCallback(si)

        d.addCallback(self._prepare_response)
        d.addCallback(self._send_response)

        d.addErrback(nargs_err)
        d.addErrback(service_err)
        d.addErrback(err)

        self._services[service_name] = d

    def _prepare_response(self, data):
        if isinstance(data, bool) and data:
            return 'OK'
        elif data is None:
            return 'No Response'
        else:
            return data

    def _send_response(self, data):
        self.transport.write(str(data))
        self.transport.loseConnection()

    def _get_service(self, data):
        args = data.split(self._delim)
        name = args[0]
        try:
            service = self._services[name]
            return service
        except KeyError:
            raise ServiceNameError(name, data)

    def _get_response(self, service, data):
        delim = self._delim
        data = delim.join(data.split(delim)[1:])
        service.callback(data)


# def sleep(secs):
#     d = defer.Deferred()
#     reactor.callLater(secs, d.callback, None)
#     return d



class ValveProtocol(ServiceProtocol):
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
                    ('GetValveStates', '_get_valve_states'),
                    ('GetValveLockStates', '_get_valve_lock_states'),
                    ('GetValveLockState', '_get_valve_lock_state'),
                    ('GetValveOwners', '_get_valve_owners'),
                    ('GetPressure', '_get_pressure'))
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

    def _set(self, data):
        dname, value = data.split(',')
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

    def _get_state_checksum(self, vnamestr):
        """

        """
        vnames = vnamestr.split(',')
        result = self._manager.get_state_checksum(vnames)
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

    def _get_valve_lock_states(self):
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

        :param controller: name of gauge controller
        :param gauge: name of gauge
        :return: pressure
        """
        manager = self._manager
        controller, gauge = data.split(',')

        p = None
        if manager:
            p = manager.get_pressure(controller, gauge)

        if p is None:
            p = InvalidGaugeErrorCode(controller, gauge)

        return str(p)

# ============= EOF =============================================
