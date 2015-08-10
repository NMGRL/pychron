# ===============================================================================
# Copyright 2015 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
class ErrorCode:
    msg = ''
    code = None
    description = ''

    def __str__(self):
        return 'ERROR {} : {}'.format(self.code, self.msg)


class PyScriptErrorCode(ErrorCode):
    msg = 'invalid pyscript {} does not exist'
    code = '001'

    def __init__(self, path, *args, **kw):
        self.msg = self.msg.format(path)


# ===== debug errors =====
class FuncCallErrorCode(ErrorCode):
    code = '002'
    msg = 'func call problem: err= {} args= {}'

    def __init__(self, err, data, *args, **kw):
        self.msg = self.msg.format(err, data)


class InvalidCommandErrorCode(ErrorCode):
    code = '003'
    msg = 'invalid command: {}'

    def __init__(self, command, *args, **kw):
        self.msg = self.msg.format(command)


class InvalidArgumentsErrorCode(ErrorCode):
    code = '004'
    msg = 'invalid arguments: {} {}'

    def __init__(self, command, err, *args, **kw):
        self.msg = self.msg.format(command, err)
        # super(InvalidArgumentsErrorCode, self).__init__(*args, **kw)


class InvalidValveErrorCode(ErrorCode):
    code = '005'
    msg = '{} is not a registered valve name'

    def __init__(self, name, *args, **kw):
        self.msg = self.msg.format(name)


class InvalidValveGroupErrorCode(ErrorCode):
    msg = 'Invalid valve group - {}'
    code = '006'

    def __init__(self, name, *args, **kw):
        self.msg = self.msg.format(name)


# ====== initialization problems with pychron
class ManagerUnavaliableErrorCode(ErrorCode):
    msg = 'manager unavaliable: {}'
    code = '007'

    def __init__(self, manager, *args, **kw):
        self.msg = self.msg.format(manager)


class DeviceConnectionErrorCode(ErrorCode):
    msg = 'device {} not connected'
    code = '008'

    def __init__(self, name, *args, **kw):
        self.msg = self.msg.format(name)


class InvalidIPAddressErrorCode(ErrorCode):
    msg = '{} is not a registered ip address'
    code = '009'

    def __init__(self, ip, *args, **kw):
        self.msg = self.msg.format(ip)


# ===== comm errors =====

class NoResponseErrorCode(ErrorCode):
    msg = 'no response from device'
    code = '010'


class PychronCommErrorCode(ErrorCode):
    msg = 'could not communicate with pychron through {}. socket.error = {}'
    code = '011'

    def __init__(self, path, err, *args, **kw):
        self.msg = self.msg.format(path, err)


# ===== security =====

class SystemLockErrorCode(ErrorCode):
    msg = 'Access restricted to {} ({}). You are {}'
    code = '012'

    def __init__(self, name, locker, sender, *args, **kw):
        self.msg = self.msg.format(name, locker, sender)


class SecurityErrorCode(ErrorCode):
    msg = 'Not an approved ip address {}'
    code = '013'

    def __init__(self, addr, *args, **kw):
        self.msg = self.msg.format(addr)


# ======= runtime errors ------

class ValveSoftwareLockErrorCode(ErrorCode):
    msg = 'Valve {} is software locked'
    code = '014'

    def __init__(self, name, *args, **kw):
        self.msg = self.msg.format(name)


class ValveActuationErrorCode(ErrorCode):
    msg = 'Valve {} failed to actuate {}'
    code = '015'

    def __init__(self, name, action, *args, **kw):
        self.msg = self.msg.format(name, action)
        super(ValveActuationErrorCode, self).__init__(*args, **kw)


class InvalidGaugeErrorCode(ErrorCode):
    msg = '{} {} not available'
    code = '016'

    def __init__(self, controller, gauge, *args, **kw):
        self.msg = self.msg.format(controller, gauge)


# class HMACSecurityErrorCode(ErrorCode):
#    msg = 'Computer {} was not authenticated. Invalid HMAC certificate'
#    code = 000
#    def __init__(self, addr, *args, **kw):
#        self.msg = self.msg.format(addr)
#        super(HMACSecurityErrorCode, self).__init__(*args, **kw)

class LogicBoardCommErrorCode(ErrorCode):
    msg = 'Failed communication with logic board'
    code = '101'


class EnableErrorCode(ErrorCode):
    msg = 'Laser failed to enable {}'
    code = '102'

    def __init__(self, reason, *args, **kw):
        self.msg = self.msg.format(reason)


class DisableErrorCode(ErrorCode):
    msg = 'Laser failed to disable {}'
    code = '103'

    def __init__(self, reason, *args, **kw):
        self.msg = self.msg.format(reason)


class InvalidSampleHolderErrorCode(ErrorCode):
    msg = 'Invalid sample holder. {}'
    code = '104'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)


class LaserMonitorErrorCode(ErrorCode):
    msg = 'emergency shutdown. {}'
    code = '105'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)


class SetpointErrorCode(ErrorCode):
    msg = 'failed to reach setpoint {}'
    code = '106'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)


class InvalidMotorErrorCode(ErrorCode):
    msg = 'no motor named {} available'
    code = '107'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)


class PositionErrorCode(ErrorCode):
    msg = 'positioning error. {}'
    code = '108'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)

# ============= EOF =====================================
