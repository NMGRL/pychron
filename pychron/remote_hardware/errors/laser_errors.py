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

from error import ErrorCode  # , code_generator, get_code_decorator


# code_gen = code_generator(0, start=1)

# def generate_code(*args):
#    return get_code_decorator(code_gen)(*args)

# @generate_code
class LogicBoardCommErrorCode(ErrorCode):
    msg = 'Failed communication with logic board'
    code = '101'


# @generate_code
class EnableErrorCode(ErrorCode):
    msg = 'Laser failed to enable {}'
    code = '102'

    def __init__(self, reason, *args, **kw):
        self.msg = self.msg.format(reason)
        super(EnableErrorCode, self).__init__(*args, **kw)


# @generate_code
class DisableErrorCode(ErrorCode):
    msg = 'Laser failed to disable {}'
    code = '103'

    def __init__(self, reason, *args, **kw):
        self.msg = self.msg.format(reason)
        super(EnableErrorCode, self).__init__(*args, **kw)


# @generate_code
class InvalidSampleHolderErrorCode(ErrorCode):
    msg = 'Invalid sample holder. {}'
    code = '104'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)
        super(InvalidSampleHolderErrorCode, self).__init__(*args, **kw)


# @generate_code
class LaserMonitorErrorCode(ErrorCode):
    msg = 'emergency shutdown. {}'
    code = '105'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)
        super(LaserMonitorErrorCode, self).__init__(*args, **kw)


# @generate_code
class SetpointErrorCode(ErrorCode):
    msg = 'failed to reach setpoint {}'
    code = '106'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)
        super(SetpointErrorCode, self).__init__(*args, **kw)


# @generate_code
class InvalidMotorErrorCode(ErrorCode):
    msg = 'no motor named {} available'
    code = '107'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)
        super(InvalidMotorErrorCode, self).__init__(*args, **kw)


class PositionErrorCode(ErrorCode):
    msg = 'positioning error. {}'
    code = '108'

    def __init__(self, sh, *args, **kw):
        self.msg = self.msg.format(sh)
        super(LaserMonitorErrorCode, self).__init__(*args, **kw)
