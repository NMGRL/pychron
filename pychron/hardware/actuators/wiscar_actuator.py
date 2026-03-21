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
from pychron.hardware.actuators import get_switch_address, word, sim
from pychron.hardware.actuators.ascii_gp_actuator import ASCIIGPActuator
from pychron.hardware.actuators.client_gp_actuator import ClientMixin


def command(*args):
    return ",".join(args)


def set_channel(name, action):
    return command("set", "valve", name, action)


def get_channel(name):
    return command("get", "valve", name)


# def actuate(name, action):
#    return set_channel(name, action)


def actuate(action):
    def fa(obj, name):
        return set_channel(name, action)

    return fa


def validate_response(resp, cmd):
    if resp:
        cmd_args = cmd.split(",")
        args = resp.split(",")

        # print('casd', cmd_args)
        # print('aaaa', args)
        # return all([c == a for c, a in zip(cmd_args, args)])
        try:
            return cmd_args[2].lower() == args[2].lower()
        except IndexError:
            print("too few arguments to compare. cmd={}, resp={}".format(cmd, resp))


class WiscArGPActuator(ASCIIGPActuator, ClientMixin):
    """
    :::
    name: WiscAr CRio based GP Actuator
    description: Used to communicate with PyValve valves
    """

    close_cmd = actuate("close")
    open_cmd = actuate("open")

    @sim
    def get_state_word(self, *args, **kw):
        resp = self.ask("get,valve,all", verbose=False)
        if resp:
            # convert resp into a word dict
            args = resp.split(",")
            # remove the command header args
            args = args[3:]
            try:
                worddict = {
                    args[i]: args[i + 1] == "Open" for i in range(0, len(args), 2)
                }
            except IndexError:
                self.debug(f"failed parsing get,valve,all response={resp}")
                return

            return worddict

    def get_channel_state(self, obj, *args, **kw):
        cmd = get_channel(get_switch_address(obj))
        resp = self.ask(cmd, verbose=True)

        if validate_response(resp, cmd):
            args = resp.split(",")
            return args[3].lower() == "open"
        else:
            self.debug("invalid response: cmd={}, resp={}".format(cmd, resp))

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
                return all(
                    (
                        r.lower() == c.lower()
                        for c, r in list(zip(cmd.split(","), resp.split(",")))[2:]
                    )
                )
                # respstate = resp.split(',')[4].lower()
                # resqueststate = cmd.split(',')[3].lower()
                # self.debug('resp={} request={}'.format(respstate, requeststate))
                # return respstate ==requeststate
            else:
                self.debug(
                    "invalid affirmative response: cmd={} resp={}".format(cmd, resp)
                )
        except BaseException:
            self.debug_exception()
            return


# ============= EOF =============================================
