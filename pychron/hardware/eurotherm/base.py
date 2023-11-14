# ===============================================================================
# Copyright 2016 Jake Ross
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

# ============= standard library imports ========================
import os
import re
from functools import reduce

# ============= enthought library imports =======================
from traits.api import HasTraits, Float, Property, provides, TraitError

# ============= local library imports  ==========================
from pychron.furnace.ifurnace_controller import IFurnaceController
from pychron.hardware.eurotherm import STX, ETX, EOT, ACK, ENQ
from pychron.hardware.furnace.base_furnace_controller import BaseFurnaceController
from pychron.paths import paths

PID_REGEX = re.compile(r"[A-Z]{2},\d+(;[A-Z]{2},\d+)*")


def modify_pid_parameter(param_str, key, value):
    nparam = []
    for a in param_str.split(";"):
        k, v = a.split(",")
        if k.strip() == key:
            v = value
        nparam.append("{},{}".format(k, v))
    return ";".join(nparam)


def get_pid_parameters(v):
    """ """
    p = os.path.join(paths.device_dir, "furnace", "eurotherm_control_parameters.txt")
    with open(p) as f:
        params = [[li.strip() for li in l.split("|")] for l in f]

    for i, pa in enumerate(reversed(params[:-1])):
        t = int(pa[0])
        # if i == 0:
        #     if v >= t:
        #         return pa
        # else:
        if v >= t:
            return pa
        # t = int(pa[0])
        # if v <= t:
        #     return pa

        # if i == 0:
        #     if v < low_t:
        #         return pa
        #     continue
        #
        # try:
        #     high_t = int(params[i + 1][0])
        # except ValueError:
        #     return None
        #
        # if low_t < v < high_t:
        #     return pa,


class BaseEurotherm(BaseFurnaceController):
    """

    Series 2000 Communications Handbook
    http://buphy.bu.edu/~stein/etherm/2000cmms.pdf
    Part No HA026230

    See Modbus & EI Bisynch Addresses, Chapter 5.
    """

    scan_func = "get_process_value"
    GID = 0
    UID = 1
    protocol = "ei_bisynch"

    use_pid_table = False

    # ifurnacecontroller
    def get_output_hook(self, **kw):
        resp = self._query("OP", **kw)
        return resp

    def get_response(self, force=False):
        if force or not self.process_value:
            self.get_process_value()
        return self.process_value

    # configloadable
    def load_additional_args(self, config):
        """ """

        self.set_attribute(
            config, "protocol", "Communications", "protocol", optional=True
        )

        if self.protocol == "ei_bisynch":
            self.set_attribute(
                config, "GID", "Communications", "GID", cast="int", optional=True
            )

            self.set_attribute(
                config, "UID", "Communications", "UID", cast="int", optional=True
            )

        return True

    def initialize(self, *args, **kw):
        if self.communicator:
            self.communicator.write_terminator = None
        return True

    def set_pid_str(self, s):
        if PID_REGEX.match(s):
            for pa in s.split(";"):
                self.debug("set pid parameters {}".format(pa))
                cmd, value = pa.split(",")
                self._command(cmd, value)
            return True
        else:
            self.warning('invalid pid string "{}"'.format(s))

    def set_pid_parameters(self, v):
        """ """
        params = get_pid_parameters(v)
        self.debug("set pid parameters temp={}, params={}".format(v, params))
        if params:
            self.set_pid_str(params[1])

    def set_process_setpoint_hook(self, v):
        """ """
        if v and self.use_pid_table:
            self.set_pid_parameters(v)

        cmd = "SL"
        resp = self._command(cmd, v, verbose=True)
        if not self.simulation:
            if resp is None:
                self.warning("Failed setting setpoint to {:0.2f}".format(v))
            else:
                return True
        else:
            return True

    def get_process_value_hook(self, **kw):
        """ """
        return self._query("PV", **kw)

    # private
    def _command(self, cmd, v, **kw):
        builder = getattr(self, "_{}_build_command".format(self.protocol))
        resp = self.ask(
            builder(cmd, v), read_terminator=ACK, terminator_position=0, **kw
        )
        parser = getattr(self, "_{}_parse_command_response".format(self.protocol))

        if not self.simulation:
            resp = parser(resp)
        return resp

    def _query(self, cmd, **kw):
        builder = getattr(self, "_{}_build_query".format(self.protocol))

        resp = self.ask(builder(cmd), **kw)

        parser = getattr(self, "_{}_parse_response".format(self.protocol))
        if not self.simulation:
            resp = parser(resp)
        return resp

    # ei_bisynch
    def _ei_bisynch_build_command(self, cmd, value):
        def calculate_cksum(p):
            return chr(reduce(lambda x, y: x ^ y, [ord(pi) for pi in p[1:]]))

        gid = str(self.GID)
        uid = str(self.UID)
        v = str(value)

        packet = "".join((STX, cmd, v, ETX))

        cksum = calculate_cksum(packet)
        return "".join((EOT, gid, gid, uid, uid, packet, cksum))

    def _ei_bisynch_build_query(self, s):
        """ """

        gid = str(self.GID)
        uid = str(self.UID)

        return "".join((EOT, gid, gid, uid, uid, s, ENQ))

    def _ei_bisynch_parse_response(self, resp):
        """ """
        if resp is not None:
            resp = resp.strip()
            if not resp:
                return

            # remove frame chrs
            resp = resp[1:-2]

            # remove the mnemonic chrs
            resp = resp[2:]

            # extract the data
            try:
                resp = float(resp)
            except ValueError as e:
                resp = None
                self.warning(e)

        return resp

    def _ei_bisynch_parse_command_response(self, resp):
        """ """
        return resp == ACK




# ============= EOF =============================================
