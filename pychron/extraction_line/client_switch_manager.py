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
from socket import gethostbyname, gethostname

from pychron.extraction_line.switch_manager import SwitchManager
from pychron.globals import globalv


class ClientSwitchManager(SwitchManager):
    def get_state_checksum(self, vkeys):
        if self.actuators:
            actuator = self.actuators[0]
            word = actuator.get_state_checksum(vkeys)
            self.debug('Get Checksum: {}'.format(word))
            try:
                return int(word)
            except BaseException:
                self.warning('invalid checksum "{}"'.format(word))

    def load_valve_states(self, refresh=True, force_network_change=False):
        # self.debug('Load valve states')
        word = self.get_state_word()
        # changed = False
        states = []
        if word:
            for k, v in self.switches.iteritems():
                try:
                    s = word[k]
                    if s != v.state or force_network_change:
                        # changed = True
                        v.set_state(s)
                        # self.refresh_state = (k, s)
                        self.set_child_state(k, s)
                        states.append((k, s))

                except KeyError:
                    pass

        elif force_network_change:
            # changed = True
            for k, v in self.switches.iteritems():
                states.append(k, v.state)
                # self.refresh_state = (k, v.state)
                # elm.update_valve_state(k, v.state)

        if refresh and states:
            self.refresh_state = states
            self.refresh_canvas_needed = True
            # elm.refresh_canvas()

    def load_valve_lock_states(self, refresh=True, force=False):
        word = self.get_lock_word()
        if globalv.valve_debug:
            self.debug('valve lock word={}'.format(word))

        changed = False
        if word is not None:
            for k in self.switches:
                if k in word:
                    v = self.get_switch_by_name(k)
                    s = word[k]
                    if v.software_lock != s or force:
                        changed = True

                        v.software_lock = s
                        self.refresh_lock_state = (k, s)
                        # elm.update_valve_lock_state(k, s)

        if refresh and changed:
            self.refresh_canvas_needed = True
            # elm.refresh_canvas()

    def load_valve_owners(self, refresh=True):
        """
            needs to return all valves
            not just ones that are owned
        """
        # elm = self.extraction_line_manager
        owners = self.get_owners_word()
        if not owners:
            return

        changed = False
        ip = gethostbyname(gethostname())
        for owner, valves in owners:
            if owner != ip:
                for k in valves:
                    v = self.get_switch_by_name(k)
                    if v is not None:
                        if v.owner != owner:
                            v.owner = owner
                            self.refresh_owned_state = (k, owner)
                            # elm.update_valve_owned_state(k, owner)
                            changed = True

        if refresh and changed:
            self.refresh_canvas_needed = True
            # elm.refresh_canvas()

    def get_state_word(self):
        d = {}
        if self.actuators:
            actuator = self.actuators[0]
            try:
                word = actuator.get_state_word()
                if self._validate_checksum(word):
                    d = self._parse_word(word[:-4])
                    if globalv.valve_debug:
                        self.debug('Get State Word: {}'.format(word.strip()))
                        self.debug('Parsed State Word: {}'.format(d))
            except BaseException:
                pass

        return d

    def get_lock_word(self):
        d = {}
        if self.actuators:
            actuator = self.actuators[0]
            word = actuator.get_lock_word()
            # self.debug('Read Lock word={}'.format(word))
            if self._validate_checksum(word):
                d = self._parse_word(word[:-4])
                if globalv.valve_debug:
                    self.debug('Get Lock Word: {}'.format(word))
                    self.debug('Parsed Lock Word: {}'.format(d))

        return d

    def get_owners_word(self):
        """
         eg.
                1. 129.128.12.141-A,B,C:D,E,F
                2. A,B,C,D,E,F
                3. 129.128.12.141-A,B,C:129.138.12.150-D,E:F
                    A,B,C owned by 141,
                    D,E owned by 150
                    F free
        """
        if self.actuators:
            rs = []
            actuator = self.actuators[0]
            word = actuator.get_owners_word()
            if word:
                groups = word.split(':')
                if len(groups) > 1:
                    for gi in groups:
                        if '-' in gi:
                            owner, vs = gi.split('-')
                        else:
                            owner, vs = '', gi

                        rs.append((owner, vs.split(',')))

                else:
                    rs = [('', groups[0].split(',')), ]
            return rs

    # private
    def _load_states(self):
        self.load_valve_states()

    def _load_soft_lock_states(self):
        self.load_valve_lock_states()

    def _save_soft_lock_states(self):
        self.debug('Client Mode. Not saving lock states')

    @property
    def state_checksum(self):
        """

        :return: True if local checksum matches remote checksum.
        """
        valves = self.switches
        vkeys = sorted(valves.keys())
        local = self.calculate_checksum(vkeys)

        remote = self.get_state_checksum(vkeys)
        if local == remote:
            return True
        else:
            self.warning('State checksums do not match. Local:{} Remote:{}'.format(local, remote))

            if remote is None:
                return

            if self.actuators:

                state_word = self.get_state_word()
                lock_word = self.get_lock_word()
                act = self.actuators[0]
                # report valves stats
                self.debug('========================= Valve Stats =========================')
                tmpl = '{:<8s}{:<8s}{:<8s}{:<8s}{:<10s}{:<10s}{:<10s}'
                self.debug(tmpl.format('Key', 'State', 'Lock', 'Failure', 'StateWord', 'LockWord', 'FailureWord'))
                for vi in vkeys:
                    v = valves[vi]
                    rvstate = act.get_channel_state(v)
                    if rvstate is not None:
                        rvstate = int(rvstate)

                    s1, s2, s3 = int(v.state), rvstate, int(state_word.get(vi, -1))
                    state = '{}{}'.format(s1, s2)
                    statew = '{}{}'.format(s1, s3)

                    rvlock = act.get_lock_state(v)
                    if rvlock is not None:
                        rvlock = int(rvlock)

                    l1, l2, l3 = int(v.software_lock), rvlock, int(lock_word.get(vi, -1))
                    lock = '{}{}'.format(l1, l2)
                    lockw = '{}{}'.format(l1, l3)

                    fail = 'X' if s1 != s2 or l1 != l2 else ''
                    failw = 'X' if s1 != s3 or l1 != l3 else ''

                    self.debug(tmpl.format(vi, state, lock, fail, statew, lockw, failw))
                self.debug('===============================================================')

# ============= EOF =============================================



