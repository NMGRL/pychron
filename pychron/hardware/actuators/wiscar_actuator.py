# ===============================================================================
# Copyright 2019 ross
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
from pychron.core.helpers.strtools import to_bool
from pychron.hardware.actuators import get_switch_address, word, sim
from pychron.hardware.actuators.ascii_gp_actuator import ASCIIGPActuator
from pychron.hardware.actuators.client_gp_actuator import ClientMixin


def command(*args):
    return ','.join(args)


def set_channel(name, action):
    return command('set', 'valve', name, action)


def get_channel(name):
    return command('get', 'valve', name)


def actuate(name, action):
    return set_channel(name, action)


def validate_response(resp, cmd):
    cmd_args = cmd.split(',')
    args = resp.split(',')
    return all([c == a for c, a in zip(cmd_args, args)])


class WiscArGPActuator(ASCIIGPActuator, ClientMixin):
    """
        Used to communicate with PyValve valves
    """
    close_cmd = actuate('close')
    open_cmd = actuate('open')

    @word
    @sim
    def get_state_word(self, *args, **kw):
        return self.ask('get,valves,all')

    def get_channel_state(self, obj, *args, **kw):
        cmd = get_channel(get_switch_address(obj))
        resp = self.ask(cmd)

        if validate_response(resp, cmd):
            args = resp.split(',')
            return args[4].lower() == 'open'

    def affirmative(self, resp, cmd):
        """
        return True if response is valid and

        make sure cmd args match to response

        example set response
        set,valve,Ms-In,

        example get response

        :param resp:
        :return:
        """
        try:
            if validate_response(resp, cmd):
                ok = resp.split(',')[4]
                return to_bool(ok)
        except BaseException:
            return

# ============= EOF =============================================
