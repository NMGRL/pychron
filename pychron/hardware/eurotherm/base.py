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

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, provides, TraitError
# ============= standard library imports ========================
import os
import re
# ============= local library imports  ==========================
from pychron.furnace.ifurnace_controller import IFurnaceController
from pychron.hardware.eurotherm import STX, ETX, EOT, ACK, ENQ
from pychron.paths import paths


PID_REGEX = re.compile(r'[A-Z]{2},\d+(;[A-Z]{2},\d+)*')

@provides(IFurnaceController)
class BaseEurotherm(HasTraits):
    scan_func = 'get_process_value'
    GID = 0
    UID = 1
    protocol = 'ei_bisynch'
    process_value = Float
    process_setpoint = Property(Float(enter_set=True, auto_set=False),
                                depends_on='_setpoint')
    _setpoint = Float
    setpoint_min = 0
    setpoint_max = 1800
    use_pid_table = False

    # ifurnacecontroller
    def get_response(self, force=False):
        if force or not self.process_value:
            self.get_process_value()
        return self.process_value

    def set_setpoint(self, v):
        self.process_setpoint = v

    # configloadable
    def load_additional_args(self, config):
        """
        """

        self.set_attribute(config, 'protocol', 'Communications', 'protocol', optional=True)

        if self.protocol == 'ei_bisynch':
            self.set_attribute(config, 'GID', 'Communications', 'GID', cast='int', optional=True)

            self.set_attribute(config, 'UID', 'Communications', 'UID', cast='int', optional=True)

        return True

    def initialize(self, *args, **kw):
        if self.communicator:
            self.communicator.write_terminator = None
        return True

    def set_pid_str(self, s):
        if PID_REGEX.match(s):
            builder = getattr(self, '_{}_build_command'.format(self.protocol))

            for pa in s.split(';'):
                self.debug('set pid parameters {}'.format(pa))
                cmd, value = pa.split(',')
                cmd = builder(cmd, value)
                self.ask(cmd, verbose=True)
                return True
        else:
            self.warning('invalid pid string "{}"'.format(s))

    def set_pid_parameters(self, v):
        """
        """
        params = self.get_pid_parameters(v)
        self.debug('set pid parameters temp={}, params={}'.format(v, params))
        if params:
            self.set_pid_str(params[1])

    def get_pid_parameters(self, v):
        """
        """
        p = os.path.join(paths.device_dir, 'furnace', 'eurotherm_control_parameters.txt')
        with open(p) as f:
            params = [l.split('\t') for l in f]

        for i, pa in enumerate(params[:-1]):

            low_t = int(pa[0])
            if i == 0:
                if v < low_t:
                    return pa
                continue

            try:
                high_t = int(params[i + 1][0])
            except ValueError:
                return None

            if low_t <= v < high_t:
                return pa

    def set_process_setpoint(self, v):
        """
        """
        if v and self.use_pid_table:
            self.set_pid_parameters(v)

        cmd = 'SL'
        resp = self._command(cmd, v, verbose=True)
        if not self.simulation:
            if resp is None:
                self.warning('Failed setting setpoint to {:0.2f}'.format(v))
            else:
                return True
        else:
            return True

    def get_process_value(self, **kw):
        """
        """
        resp = self._query('PV', **kw)
        try:
            self.process_value = resp
        except TraitError:
            pass

        return resp

    # private
    def _command(self, cmd, v, **kw):
        builder = getattr(self, '_{}_build_command'.format(self.protocol))
        resp = self.ask(builder(cmd, v), read_terminator=ACK, terminator_position=0, **kw)
        parser = getattr(self, '_{}_parse_command_response'.format(self.protocol))

        if not self.simulation:
            resp = parser(resp)
        return resp

    def _query(self, cmd, **kw):
        builder = getattr(self, '_{}_build_query'.format(self.protocol))

        resp = self.ask(builder(cmd), **kw)

        parser = getattr(self, '_{}_parse_response'.format(self.protocol))
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

        packet = ''.join((STX, cmd, v, ETX))

        cksum = calculate_cksum(packet)
        return ''.join((EOT, gid, gid, uid, uid, packet, cksum))

    def _ei_bisynch_build_query(self, s):
        """
        """

        gid = str(self.GID)
        uid = str(self.UID)

        return ''.join((EOT, gid, gid, uid, uid, s, ENQ))

    def _ei_bisynch_parse_response(self, resp):
        """
        """
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
            except ValueError, e:
                resp = None
                self.warning(e)

        return resp

    def _ei_bisynch_parse_command_response(self, resp):
        """
        """
        return resp == ACK

    def _get_process_setpoint(self):
        """
        """
        return self._setpoint

    def _set_process_setpoint(self, v):
        """
        """
        if v is not None:
            self._setpoint = v
            self.set_process_setpoint(v)

    def _validate_process_setpoint(self, v):
        """
        """
        try:
            float(v)
        except ValueError:
            pass

        if self.setpoint_min <= v < self.setpoint_max:
            return v

# ============= EOF =============================================
