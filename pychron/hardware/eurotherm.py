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



'''
Eurotherm 2000 series device abstraction

see 2000 Series Communications Manual - Issue 2
http://eurotherm.com/document-library/?ignoreeveryonegroup=0&assetdetesctl1390419=1833&search=2000+series&searchcontent=0

'''

#============= enthought library imports =======================
from traits.api import Float, Property
from traitsui.api import View, Item
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice
from pychron.paths import paths

EOT = chr(4)
ENQ = chr(5)
STX = chr(2)
ETX = chr(3)
ACK = chr(6)
NAK = chr(15)


class Eurotherm(CoreDevice):
    '''
    '''
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

    def _get_process_setpoint(self):
        '''
        '''
        return self._setpoint

    def _set_process_setpoint(self, v):
        '''
           
        '''
        if v is not None:
            self.set_process_setpoint(v)

    def _validate_process_setpoint(self, v):
        '''
        '''
        try:
            float(v)
        except ValueError:
            pass

        if self.setpoint_min <= v < self.setpoint_max:
            return v

    def load_additional_args(self, config):
        '''

        '''

        self.set_attribute(config, 'protocol', 'Communications', 'protocol', optional=True)

        if self.protocol == 'ei_bisynch':
            self._communicator.write_terminator = None

            self.set_attribute(config, 'GID', 'Communications', 'GID', cast='int', optional=True)

            self.set_attribute(config, 'UID', 'Communications', 'UID', cast='int', optional=True)

        return True

    def modbus_build_query(self, s):
        '''
        '''
        return s

    def modbus_parse_response(self, resp):
        '''
        '''
        return resp

    def ei_bisynch_build_command(self, cmd, value):
        def calculate_cksum(p):
            return chr(reduce(lambda x, y: x ^ y, [ord(pi) for pi in p[1:]]))

        GID = str(self.GID)
        UID = str(self.UID)
        v = str(value)

        packet = ''.join((STX, cmd, v, ETX))

        cksum = calculate_cksum(packet)
        return ''.join((EOT, GID, GID, UID, UID, packet, cksum))

    def ei_bisynch_build_query(self, s):
        '''

        '''

        GID = str(self.GID)
        UID = str(self.UID)

        return ''.join((EOT, GID, GID, UID, UID, s, ENQ))

    def ei_bisynch_parse_response(self, resp):
        '''

        '''
        if resp is not None:
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

    def ei_bisynch_parse_command_response(self, resp):
        '''

        '''
        return resp == ACK

    def set_pid_parameters(self, v):
        '''
        '''

        params = self.get_pid_parameters(v)

        if params:
            builder = getattr(self, '{}_build_command'.format(self.protocol))
            # parser = getattr(self, '%s_parse_command_response' % self.protocol)

            for pi in params[1].split(';'):
                cmd, value = pi.split(',')

                cmd = builder(cmd, value)
                self.ask(cmd)

    def get_pid_parameters(self, v):
        '''

        '''

        p = os.path.join(paths.device_dir, 'Eurotherm_control_parameters.txt')
        with open(p) as f:
            params = []

            for l in f.read().split('\n'):
                args = l.split('\t')
                params.append(args)
            f.close()

        for i, pi in enumerate(params[:-1]):

            if i == 0:
                continue

            low_t = int(pi[0])
            try:
                high_t = int(params[i + 1][0])
            except ValueError:
                return None

            if low_t <= v < high_t:
                return pi

    def set_process_setpoint(self, v):
        '''

        '''
        if v and self.use_pid_table:
            self.set_pid_parameters(v)

        cmd = 'SL'
        builder = getattr(self, '{}_build_command'.format(self.protocol))
        cmd = builder(cmd, v)
        resp = self.ask(cmd)
        parser = getattr(self, '{}_parse_command_response'.format(self.protocol))

        if not self.simulation:
            resp = parser(resp)
            if not resp:
                self.warning('Failed setting setpoint to {:0.2f}'.format(v))
            else:
                self._setpoint
                return True
        else:
            self._setpoint
            return True

    def get_process_value(self, **kw):
        '''
        '''
        cmd = 'PV'

        builder = getattr(self, '{}_build_query'.format(self.protocol))

        resp = self.ask(builder(cmd),
                        **kw
                        )

        parser = getattr(self, '{}_parse_response'.format(self.protocol))
        if not self.simulation:
            resp = parser(resp)

        if resp is None or resp == 'simulation':
            resp = self.get_random_value(0, 10)

        self.process_value = resp

        return resp

    def traits_view(self):
        '''
        '''
        return View(Item('process_setpoint'),
                    Item('process_value', style='readonly')
                    )
#============= EOF ====================================
# def __init__(self, *args, **kw):
#        super(Eurotherm, self).__init__(*args, **kw)
#
#        if self.setpoint_recording:
#            self._setup_setpoint_recording()
#
#    def _setup_setpoint_recording(self):
#        root = os.path.join(paths.data_dir, 'streams')
#        base = 'history'
#
#
#        self.setpoint_history_path = p = unique_path(root, base)
#        f = open(p, 'w')
#        f.write('timestamp    setpoint\n')
#        f.close()
#
#    def record_setpoint_history(self, v):
#        f = open(self.setpoint_history_path, 'a')
#        ti = time.time()
#        millisecs = math.modf(ti)[0] * 1000
#        tstamp = '%s +%0.5f' % (time.strftime("%Y-%m-%d %H:%M:%S"), millisecs)
#        line = '%s %s\n' % (tstamp, v)
#        f.write(line)
#        f.close()
