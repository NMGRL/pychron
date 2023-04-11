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


# ============= enthought library imports =======================
from __future__ import absolute_import
from __future__ import print_function
import time
from threading import Lock

from numpy import array, hstack
from traits.api import Float, Int, Str, Bool, Property, Array

from pychron.hardware.core.checksum_helper import computeBCC
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.data_helper import make_bitarray
from six.moves import map
from six.moves import range

STX = chr(2)
ETX = chr(3)
EOT = chr(4)
ENQ = chr(5)
DLE = chr(16)
ANSWER_ADDR = "0002"
STATUS = ["Powering On", "Laser Off", "Turning On", "Laser On"]
ACTION = ["Turn Off", "Turn on", "Single Shot", "Run", "Firing"]


class ATLLaserControlUnit(CoreDevice):
    """ """

    energy_readback = Float
    pressure_readback = Float
    burst_readback = Int
    status_readback = Str
    action_readback = Str
    firing = Bool

    burst_shot = Property(Int(enter_set=True, auto_set=False), depends_on="_burst_shot")
    _burst_shot = Int

    reprate = Property(Int(enter_set=True, auto_set=False), depends_on="_reprate")
    _reprate = Int
    _was_fired = False

    energies = Array
    stablization_mode = None

    #    _timer = None
    #    _enabled = Bool(False)
    #    triggered = Bool(False)
    #
    #    energy = Float(0)
    #    energymin = Constant(0.0)
    #    energymax = Constant(15.0)
    #    update_energy = Float
    #
    #    hv = Float(11)
    #    hvmin = Constant(11.0)
    #    hvmax = Constant(16.0)
    #    update_hv = Float(11)
    #
    #    reprate = Float(100)
    #    repratemin = Constant(100.0)
    #    repratemax = Constant(300.0)
    #    update_reprate = Float(100)
    #
    #    trigger_modes = ['External I',
    #                      'External II',
    #                      'Internal'
    #                      ]
    #    trigger_mode = Str('External I')
    #    stablization_modes = ['High Voltage', 'Energy']
    #    stablization_mode = Str('High Voltage')
    #
    #    stop_at_low_e = Bool
    #
    #    cathode = Float(0.0)
    #    reservoir = Float(0.0)
    #    missing_pulses = Int(0)
    #    halogen_filter = Float(0.0)
    #
    #    laser_head = Float(0.0)
    #    laser_headmin = Constant(0.0)
    #    laser_headmax = Constant(7900.0)
    #
    #    burst = Bool
    #    nburst = Int(enter_set=True, auto_set=False)
    #    cburst = Int

    #    def start_update_timer(self):
    #        '''
    #        '''
    #        self.stop_update_timer()
    #        self._timer = Timer(1000, self._update_parameters)
    #        self._timer.Start()
    #
    #    def stop_update_timer(self):
    #        if self._timer:
    #            self._timer.Stop()

    #    def trigger_laser(self):
    #        '''
    #        '''
    #        self.start_update_timer()
    #
    #        self.triggered = True
    #
    #    def stop_triggering_laser(self):
    #        '''
    #        '''
    #        self.triggered = False
    def __init__(self, *args, **kw):
        super(ATLLaserControlUnit, self).__init__(*args, **kw)
        self._lock = Lock()

    def initialize(self, *args, **kw):
        r = super(ATLLaserControlUnit, self).initialize(self, *args, **kw)
        self.communicator.write_terminator = None

        self._burst_shot = self.get_nburst()

        # reading reprate not working correctly. check for a new ATL API
        self._reprate = self.get_reprate()

        v = 55
        self.set_stabilization("energy", v)
        return r

    def set_stabilization(self, mode, v):
        """
        0   0  0  0  0  0  0  0  0  0  0
        b10 b9 b8 b7 b6 b5 b4 b3 b2 b1 b0
        --------  gastype
                  ------- stab mode 000 HV, 001 Energy
                           -- burst mode
                              -------- trigger mode
                                       -- disable on low energy
        """
        MODES = {"energy": "001", "hv": "000", "energy_w_pge": "011"}
        mode = MODES.get(mode, "000")

        with self._lock:
            p = "000 {} 1 000 0".format(mode).replace(" ", "")
            cmd = self._build_command(1000, int(p, 2))
            self._send_command(cmd, lock=False)

            # v=make_bitarray(v, width=16)
            cmd = self._build_command(1003, v)
            self._send_command(cmd, lock=False)

    def get_mean_energy(self):
        return self.energies.mean()

    def is_enabled(self):
        return self.status_readback == "Laser On"

    def set_reprate(self, n, save=True):
        lh = self._make_integer_pair(n)
        if lh:
            with self._lock:
                cmd = self._build_command(1001, lh)
                self._send_command(cmd, lock=False)
                if save:
                    self._save_eeprom()
                self._reprate = int(n)

    def _make_integer_pair(self, n):
        try:
            n = int(n)
        except (ValueError, TypeError):
            return

        v = make_bitarray(n, width=32)
        h, l = int(v[:16], 2), int(v[16:], 2)
        return l, h

    def set_nburst(self, n, save=True):
        if int(n) != int(self._burst_shot):
            self.debug(
                "setting nburst n={} current_value={}".format(n, self._burst_shot)
            )
            lh = self._make_integer_pair(n)
            if lh:
                with self._lock:
                    cmd = self._build_command(22, lh)
                    self._send_command(cmd, lock=False)

                    cmd = self._build_command(1004, lh)
                    self._send_command(cmd, lock=False)

                    self._burst_shot = int(n)
                    if save:
                        self._save_eeprom()

    def _save_eeprom(self, lock=False):
        cmd = self._build_command(37, 1)
        self._send_command(cmd, lock=lock)

    def get_reprate(self, verbose=True):
        self.debug("get reprate")
        resp = self._send_query(1001, 1, verbose=verbose)
        v = -1
        if resp is not None:  # and len(resp) == 4:
            print(resp, len(resp))
            v = int(resp, 16)

        #    high = resp[4:]
        #    low = resp[:4]
        #    high = make_bitarray(int(high, 16), width=16)
        #    low = make_bitarray(int(low, 16), width=16)
        #    v = int(high + low, 2)

        return v

    def get_nburst(self, verbose=True):
        if verbose:
            self.debug("get nburst")

        v = 0
        resp = self._send_query(22, 2, verbose=verbose)
        if resp is not None and len(resp) == 8:
            high = resp[4:]
            low = resp[:4]
            high = make_bitarray(int(high, 16), width=16)
            low = make_bitarray(int(low, 16), width=16)
            v = int(high + low, 2)

        return v

    def is_burst_mode(self, ps=None):
        bit = 4
        if ps is None:
            ps = self.get_process_status()
            return int(ps[16 - (bit + 1)])

    def get_process_status(self):
        # ps = '0000000000000000'
        r = self._send_query(1000, 1)
        self.debug("get process status {}".format(r))
        if r is not None:
            r = int(r, 16)
            ps = make_bitarray(r, width=16)
            return ps

    def set_burst_mode(self, mode, ps=None):
        if not self.is_burst_mode(ps):
            if ps is None:
                ps = self.get_process_status()

            nps = ps[: 16 - 4] + str(int(mode)) + ps[-4:]
            print(mode, nps)

            cmd = self._build_command(1000, int(nps, 2))
            self._send_command(cmd)

    def laser_on(self):
        #        self.start_update_timer()
        cmd = self._build_command(11, 1)
        self._send_command(cmd)

    def laser_off(self):
        cmd = self._build_command(11, 0)
        self._send_command(cmd)
        self._enabled = False

    def laser_single_shot(self):
        cmd = self._build_command(11, 2)
        self._send_command(cmd)

    def laser_run(self):
        self.debug("run laser")
        self.firing = True
        self.energies = array([])

        cmd = self._build_command(11, 3)
        self._send_command(cmd)

    def laser_stop(self):
        self.debug("stop laser")
        cmd = self._build_command(11, 1)
        self._send_command(cmd)
        self.firing = False

    def get_laser_status(self, verbose=True):
        r = self._send_query(11, 1, verbose=verbose)
        return self._parse_response(r, 1)[0]

    # ===============================================================================
    # gas handling
    # ===============================================================================
    def do_auto_vac(self):
        #        self.start_auto_vac()
        # wait until idle
        self.wait_for_idle()

    #        self.wait_for_gwr()

    def do_auto_gas_exchange(self):
        #        self.start_auto_gas_exchange()
        self.wait_for_idle()

    #        self.wait_for_gwr()

    def wait_for_idle(self):
        while 1:
            time.sleep(0.75)
            if self.is_idle():
                break

    def wait_for_gwr(self):
        while 1:
            time.sleep(0.75)
            if self.waiting_for_gas_request():
                break

    def start_auto_vac(self):
        cmd = self._build_command(14, 11)
        self._send_command(cmd)

    def start_auto_gas_exchange(self):
        cmd = self._build_command(14, 11)
        self._send_command(cmd)

    def set_to_idle(self):
        cmd = self._build_command(14, 11)
        self._send_command(cmd)

    def waiting_for_gas_request(self, verbose=False):
        rq = self.get_gas_wait_request(verbose=verbose)
        print(rq)
        if rq is not None:
            return rq[0] == 1

    def is_idle(self):
        status = self.get_gas_status()
        if status is not None:
            istatus = int(status, 16)
            return istatus == 0

    def get_pressure(self, verbose=False):
        vs = self._send_query(9, 1, verbose=verbose)
        if vs is not None:
            vs = self._parse_response(vs, 1)
            if vs is not None:
                self.pressure_readback = vs[0] / 1000.0

    def get_gas_status(self):
        r = self._send_query(13, 1)
        return r

    def get_gas_wait_request(self, verbose=True):
        r = self._send_query(27, 1, verbose=verbose)
        return self._parse_response(r, 1)

    def open_valve(self, addr):
        self.info("open valve {}".format(addr))

    def close_valve(self, addr):
        self.info("close valve {}".format(addr))

    def update_parameters(self):
        # energy, pressure, status, action
        vs = self._send_query(8, 4, verbose=False)

        if vs is not None:
            vs = self._parse_response(vs, 4)
            if vs is not None:
                self.energy_readback = vs[0] / 10.0
                self.energies = hstack((self.energies[:-5], [self.energy_readback]))

                self.pressure_readback = vs[1]
                self.status_readback = STATUS[vs[2]]
                self.action_readback = ACTION[vs[3]]

        b = self.get_nburst(verbose=False)
        if b is not None:
            self.burst_readback = b
            if self.firing:
                self.debug(
                    "readback={} burst={} fired={}".format(
                        b, self.burst_shot, self._was_fired
                    )
                )
                if not b or (self._was_fired and b == self.burst_shot):
                    self.debug("AUTO STOP LASER")
                    self.laser_stop()
                    self._was_fired = False

                self._was_fired = b != self.burst_shot

    def _set_answer_parameters(
        self,
        start_addr_value,
        answer_len,
        verbose=True,
    ):
        values = [start_addr_value, answer_len]
        cmd = self._build_command(ANSWER_ADDR, values)

        self._send_command(cmd, verbose=verbose)

    def _build_command(self, start_addr, values):
        if isinstance(start_addr, int):
            start_addr = "{:04X}".format(start_addr)

        if isinstance(values, int):
            values = (values,)
            #            values = ('{:04X}'.format(values),)

        values = list(map("{:04X}".format, values))

        cmd = start_addr + "".join(values)
        cmd += ETX
        BCC = computeBCC(cmd)

        cmd = STX + cmd + chr(BCC)

        return cmd

    def _send_query(self, s, l, verbose=True):
        self._set_answer_parameters(s, l, verbose=verbose)

        with self._lock:
            cmd = self._build_command(ANSWER_ADDR, (s, l))
            self._send_command(cmd, verbose=verbose, lock=False)

            # =self.ask('A'+ENQ, nchars=(l+1)*4+6)
            #        self._start_message()
            n = (l + 1) * 4 + 6
            cmd = "a" + ENQ
            r = self.ask(cmd, nchars=n, verbose=verbose)
            #        r = self.read(nchars=n)
            self.tell(DLE + "1", verbose=verbose)
            self._end_message(verbose=verbose)
            return self._clean_response(r)

    def _send_command(self, cmd, verbose=True, lock=True):
        if lock:
            self._lock.acquire()

        self._start_message(verbose=verbose)
        self.ask(cmd, read_terminator=DLE + "1", verbose=verbose)
        self._end_message(verbose=verbose)

        if lock:
            self._lock.release()

    def _start_message(self, verbose=True):
        cmd = "A" + ENQ
        self.ask(cmd, read_terminator=DLE + "0", verbose=verbose)

    def _end_message(self, verbose=True):
        cmd = EOT
        self.tell(cmd, verbose=verbose)

    def _clean_response(self, r):
        #        print len(r)
        handshake = r[:4]

        # print handshake,handshake=='a'+DLE+'0'+STX
        if handshake == "a" + DLE + "0" + STX:
            chksum = computeBCC(r[4:-1])

            # print 'a={} b={} c={} d={}'.format(chksum, ord(r[-1]), chr(chksum),chr(chksum) == r[-1])
            if chr(chksum) == r[-1]:
                return r[8:-2]

    def _parse_response(self, resp, l):
        #        print resp, l, len(resp),l*4
        if resp is not None and len(resp) == l * 4:
            return [int(resp[i : i + 4], 16) for i in range(0, len(resp) - 3, 4)]

    def _get_burst_shot(self):
        return self._burst_shot

    def _set_burst_shot(self, v):
        self.set_nburst(v)

    def _get_reprate(self):
        return self._reprate

    def _set_reprate(self, v):
        self.set_reprate(v)


#    def _parse_parameter_answers(self, resp, rstartaddr, answer_len):
#        '''
#        '''
#        #split at stx
#        rargs = resp.split(STX)
#        r, chk = rargs[1].split(ETX)
#
#        #verify checksum
#        bcc = computeBCC(r + ETX)
#        if int(bcc, 16) != int(chk, 16):
#            return
#
#        #r example
#        #0005006500000000
#        #startaddr, startaddrvalue, ... ,nstartaddr_value
#
#        #remove startaddr and make sure its the one we requested
#        startaddr = int(r[:4], 16)
#        if rstartaddr != startaddr:
#            return
#
#        #trim off start addr
#        r = r[4:]
#        #ensure len of answers correct
#        if answer_len != len(r) / 4:
#            return
#
#        args = ()
#        for i in range(0, len(r), 4):
#            val = r[i:i + 4]
#            args += (val,)
#
#        return args

#    def _update_parameter_list(self, names, s, l):
#        '''
#
#        '''
#        resp = self._send_query(s, l)
#        if resp is not None:
#            args = self._parse_parameter_answers(resp, s, l)
#    #        kw = dict()
#            for n, a in zip(names, args):
#                v = int(a, 16)
#                if isinstance(n, tuple):
#                    v = n[1](v)
#                    n = n[0]
#                self.trait_set(n=v)
#            kw[n] = v
#        self.trait_set(**kw)


if __name__ == "__main__":
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup("atl")
    a = ATLLaserControlUnit(
        name="ATLLaserControlUnit", configuration_dir_name="fusions_uv"
    )
    a.bootstrap()
    a.laser_off()
# ============= EOF ====================================
