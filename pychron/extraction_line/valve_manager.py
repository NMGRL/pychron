# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
import binascii

from traits.api import Any, Dict, List, Bool, Event

# =============standard library imports ========================
from pickle import PickleError
from itertools import groupby
from socket import gethostname, gethostbyname
import os
import pickle
import time
# =============local library imports  ==========================
from pychron.core.helpers.filetools import to_bool
from pychron.globals import globalv
from pychron.hardware.core.checksum_helper import computeCRC
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.hardware.switch import Switch
from pychron.managers.manager import Manager
from pychron.extraction_line.explanation.explanable_item import ExplanableValve
from pychron.hardware.valve import HardwareValve
from pychron.paths import paths
from pychron.extraction_line.pipettes.tracking import PipetteTracker
from valve_parser import ValveParser


def add_checksum(func):
    def wrapper(*args, **kw):
        d = func(*args, **kw)
        return '{}{}'.format(d, computeCRC(d))

    return wrapper


class ValveGroup(object):
    owner = None
    valves = None


class ValveManager(Manager):
    """
    Manager to interface with the UHV and HV pneumatic valves

    """

    valves = Dict
    explanable_items = List
    extraction_line_manager = Any
    pipette_trackers = List(PipetteTracker)

    actuators = List

    query_valve_state = Bool(True)

    use_explanation = True

    refresh_state = Event
    refresh_lock_state = Event
    refresh_canvas_needed = Event
    refresh_owned_state = Event
    console_message = Event
    mode = None

    _prev_keys = None

    def actuate_children(self, name, action, mode):
        """
            actuate all switches that have ``name`` defined as their parent
        """
        for v in self.valves.values():
            if v.parent == name:
                self.debug('actuating child, {}, {}'.format(v.display_name, action))
                if v.parent_inverted:
                    func = self.open_by_name if action == 'close' else self.close_by_name
                else:
                    func = self.open_by_name if action == 'open' else self.close_by_name

                func(v.display_name, mode)

    def show_valve_properties(self, name):
        v = self.get_valve_by_name(name)
        if v is not None:
            v.edit_traits()

    def kill(self):
        super(ValveManager, self).kill()
        self._save_soft_lock_states()

    def create_device(self, name, *args, **kw):
        """
        """
        dev = super(ValveManager, self).create_device(name, *args, **kw)
        if 'actuator' in name or 'controller' in name:
            if dev is not None:
                self.actuators.append(dev)

            return dev

    def finish_loading(self, update=False):
        """
        """
        if self.actuators:
            for a in self.actuators:
                self.info('setting actuator {}'.format(a.name))
                self.info('comm. device = {} '.format(a.com_device_name))

        # open config file
        setup_file = os.path.join(paths.extraction_line_dir, 'valves.xml')
        self._load_valves_from_file(setup_file)

        if globalv.load_valve_states:
            self._load_states()
        if globalv.load_soft_locks:
            self._load_soft_lock_states()

    def set_child_state(self, name, state):
        self.debug('set states for children of {}. state={}'.format(name, state))
        # elm = self.extraction_line_manager
        for k, v in self.valves.iteritems():
            if v.parent == name:
                v.set_state(state)
                self.refresh_state = (k, state)
                # elm.update_valve_state(k, state)

    @property
    def state_checksum(self):
        """

        :return: True if local checksum matches remote checksum. Returns True if mode not "client".
        """
        if self.mode != 'client':
            return True

        valves = self.valves
        vkeys = valves.keys()
        local = self.calculate_checksum(vkeys)

        remote = self.get_state_checksum(vkeys)
        if local == remote:
            return True
        else:
            self.warning('State checksums do not match. Local:{} Remote:{}'.format(local, remote))
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
                    s1, s2, s3 = int(v.state), int(rvstate), int(state_word.get(vi, -1))
                    state = '{}{}'.format(s1, s2)
                    statew = '{}{}'.format(s1, s3)

                    rvlock = act.get_lock_state(v)
                    l1, l2, l3 = int(v.software_lock), int(rvlock), int(lock_word.get(vi, -1))
                    lock = '{}{}'.format(l1, l2)
                    lockw = '{}{}'.format(l1, l3)

                    fail = 'X' if s1 != s2 or l1 != l2 else ''
                    failw = 'X' if s1 != s3 or l1 != l3 else ''

                    self.debug(tmpl.format(vi, state, lock, fail, statew, lockw, failw))
                self.debug('===============================================================')

    def calculate_checksum(self, vkeys):
        vs = self.valves
        return binascii.crc32(''.join((vs[k].state_str() for k in vkeys)))

    def get_state_checksum(self, vkeys):
        if self.actuators:
            actuator = self.actuators[0]
            word = actuator.get_state_checksum(vkeys)
            self.debug('Get Checksum: {}'.format(word))
            return word

    def load_valve_states(self, refresh=True, force_network_change=False):
        self.debug('Load valve states')
        # elm = self.extraction_line_manager
        word = self.get_state_word()
        changed = False
        if word:
            for k, v in self.valves.iteritems():
                try:
                    s = word[k]
                    if s != v.state or force_network_change:
                        changed = True
                        v.set_state(s)
                        self.refresh_state = (k, s)
                        # elm.update_valve_state(k, s)
                        self.set_child_state(k, s)

                except KeyError:
                    pass

        elif force_network_change:
            changed = True
            for k, v in self.valves.iteritems():
                self.refresh_state = (k, v.state)
                # elm.update_valve_state(k, v.state)

        if refresh and changed:
            self.refresh_canvas_needed = True
            # elm.refresh_canvas()

    def load_valve_lock_states(self, refresh=True):
        # elm = self.extraction_line_manager
        word = self.get_lock_word()

        changed = False
        if word is not None:
            for k in self.valves:
                if k in word:
                    v = self.get_valve_by_name(k)
                    s = word[k]
                    if v.software_lock != s:
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
                    v = self.get_valve_by_name(k)
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
            if self._validate_checksum(word):
                d = self._parse_word(word[:-4])

                self.debug('Get Lock Word: {}'.format(word))
                self.debug('Parsed Lock Word: {}'.format(d))

        return d

    def get_valve_names(self):
        return self.valves.keys()

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

    @add_checksum
    def get_owners(self):
        """
            eg.
                1. 129.128.12.141-A,B,C:D,E,F
                   A,B,C owned by 141
                   D,E,F free
                2. A,B,C,D,E,F
                   All free
                3. 129.128.12.141-A,B,C:129.138.12.150-D,E:F
                    A,B,C owned by 141,
                    D,E owned by 150
                    F free
        """
        # self.valves['C'].owner = '129.138.12.135'
        # self.valves['X'].owner = '129.138.12.135'

        vs = [(v.name.split('-')[1], v.owner) for v in self.valves.itervalues()]
        key = lambda x: x[1]
        vs = sorted(vs, key=key)

        owners = []
        for owner, valves in groupby(vs, key=key):
            valves, _ = zip(*valves)
            v = ','.join(valves)
            if owner:
                t = '{}-{}'.format(owner, v)
            else:
                t = v
            owners.append(t)

        return ':'.join(owners)

    @add_checksum
    def get_software_locks(self):
        return ','.join(['{}{}'.format(k, int(v.software_lock))
                         for k, v in self.valves.iteritems()])

    @add_checksum
    def get_states(self, timeout=1):
        """
            get as many valves states before time expires
            remember last set of valves returned.

            if last set of valves less than total return
            states for the remainder valves

        """
        st = time.time()
        states = []
        keys = []
        prev_keys = []
        clear_prev_keys = False
        if self._prev_keys:
            clear_prev_keys = True
            prev_keys = self._prev_keys

        for k, v in self.valves.iteritems():
            '''
                querying a lot of valves can add up hence timeout.
                
                most valves are not queried by default which also helps shorten
                execution time for get_states. 
                
            '''
            if k in prev_keys:
                continue

            keys.append(k)
            state = '{}{}'.format(k, int(self._get_state_by(v)))
            states.append(state)
            if time.time() - st > timeout:
                break
        else:
            # if loop completes before timeout dont save keys
            clear_prev_keys = True

        if clear_prev_keys:
            keys = None

        self._prev_keys = keys
        return ','.join(states)

    def get_valve_by_address(self, a):
        """
        """
        return self._get_valve_by(a, 'address')

    def get_valve_by_description(self, a):
        """
        """
        return self._get_valve_by(a, 'description')

    def get_valve_by_name(self, n):
        """
        """
        if n in self.valves:
            return self.valves[n]

    def get_name_by_address(self, k):
        """
        """
        v = self.get_valve_by_address(k)
        if v is not None:
            return v.name

    def get_name_by_description(self, d):
        v = self.get_valve_by_description(d)
        if v is not None:
            return v.name.split('-')[-1]

    def get_evalve_by_name(self, n):
        """
        """
        return next((item for item in self.explanable_items if item.name == n), None)

    def get_state_by_name(self, n):
        """
        """
        v = self.get_valve_by_name(n)
        state = None
        if v is not None:
            state = self._get_state_by(v)

        return state

    def get_state_by_description(self, n):
        """
        """
        v = self.get_valve_by_description(n)
        state = None
        if v is not None:
            state = self._get_state_by(v)

        return state

    def get_actuator_by_name(self, name):
        act = None
        if self.actuators:
            act = next((a for a in self.actuators
                        if a.name == name), None)
        if not act:
            if self.application:
                act = self.application.get_service_by_name(ICoreDevice, name)

        return act

    def get_software_lock(self, name, description=None, **kw):
        if description:
            v = self.get_valve_by_description(description)
        else:
            v = self.get_valve_by_name(name)

        if v is not None:
            return v.software_lock

    def _check_soft_interlocks(self, name):
        """
        """
        cv = self.get_valve_by_name(name)
        self.debug('check software interlocks {}'.format(name))
        if cv is not None:
            interlocks = cv.interlocks
            valves = self.valves
            for interlock in interlocks:
                if interlock in valves:
                    v = valves[interlock]
                    if v.state:
                        self.debug('interlocked {}'.format(interlock))
                        return v

    def open_by_name(self, name, mode='normal'):
        """
        """
        return self._open_(name, mode)

    def close_by_name(self, name, mode='normal'):
        """
        """
        return self._close_(name, mode)

    def sample(self, name, period):
        v = self.get_valve_by_name(name)
        if v and not v.state:
            self.info('start sample')
            self.open_by_name(name)

            time.sleep(period)

            self.info('end sample')
            self.close_by_name(name)

    def lock(self, name, save=True):
        """
        """
        v = self.get_valve_by_name(name)
        if v is not None:
            v.lock()
            if save:
                self._save_soft_lock_states()

    def unlock(self, name, save=True):
        """
        """
        v = self.get_valve_by_name(name)
        if v is not None:
            v.unlock()
            if save:
                self._save_soft_lock_states()

    def set_valve_owner(self, name, owner):
        v = self.get_valve_by_name(name)
        if v is not None:
            v.owner = owner

    def validate(self, v):
        """
        return false if v's interlock valve(s) is(are) open
        else return true
        """

        return next((False for vi in v.interlocks if self.get_valve_by_name(vi).state), True)

    # private
    def _get_state_by(self, v):
        """
        """
        state = None
        if self.query_valve_state and v.query_state:
            state = v.get_hardware_state()

        if state is None:
            state = v.state
        else:
            v.state = state

        return state

    def _get_valve_by(self, a, attr):
        return next((valve for valve in self.valves.itervalues() \
                     if getattr(valve, attr) == a), None)

    def _validate_checksum(self, word):
        # return True
        if word is not None:
            checksum = word[-4:]
            data = word[:-4]
            self.debug('{} {}'.format(data, checksum))
            expected = computeCRC(data)
            if expected != checksum:
                self.warning('The checksum is not correct for this message. Expected: {}, Actual: {}'.format(expected,
                                                                                                             checksum))
            else:
                return True

    def _parse_word(self, word):
        d = {}
        if word is not None:
            try:
                if ',' in word:
                    packets = word.split(',')
                    n, nn = len(packets), len(self.valves)
                    if n < nn:
                        self.warning('Valve word length is too short. All valve states will not be updated!'
                                     ' Word:{}, Num Valves: {}'.format(n, nn))

                    for packet in packets:
                        key = packet[:-1]
                        state = packet[-1:].strip()
                        d[key] = bool(int(state))

                else:
                    for i in xrange(0, len(word), 2):
                        packet = word[i:i + 2]
                        try:
                            key, state = packet[0], packet[1]
                            d[key] = bool(int(state))
                        except IndexError:
                            return d
                            # if key.upper() in ALPHAS:
                            # if state in ('0', '1'):
            except ValueError:
                pass

        return d

    def _load_states(self):
        if self.mode == 'client':
            self.load_valve_states(refresh=False)
        else:
            for k, v in self.valves.iteritems():
                s = v.get_hardware_state()
                self.refresh_state = (k, s, False)

                # # elm = self.extraction_line_manager
                # for k, v in self.valves.iteritems():
                # s = v.get_hardware_state()
                # self.refresh_state = (k, s, False)
                # # elm.update_valve_state(k, s, refresh=False)
                # # time.sleep(0.025)

    def _load_soft_lock_states(self):
        if self.mode == 'client':
            self.load_valve_lock_states()

            # for k, v in self.valves.iteritems():
            # s = v.get_lock_state()
            # func = self.lock if s else self.unlock
            # func(k, save=False)
            # time.sleep(0.025)

        else:
            p = os.path.join(paths.hidden_dir, '{}_soft_lock_state'.format(self.name))
            if os.path.isfile(p):
                self.info('loading soft lock state from {}'.format(p))

                with open(p, 'rb') as f:
                    try:
                        sls = pickle.load(f)
                    except PickleError:
                        pass

                    for v in self.valves:

                        if v in sls and sls[v]:
                            self.lock(v, save=False)
                        else:
                            self.unlock(v, save=False)

    def _save_soft_lock_states(self):
        if self.mode != 'client':
            p = os.path.join(paths.hidden_dir, '{}_soft_lock_state'.format(self.name))
            self.info('saving soft lock state to {}'.format(p))
            with open(p, 'wb') as f:
                obj = dict([(k, v.software_lock) for k, v in self.valves.iteritems()])

                pickle.dump(obj, f)
        else:
            self.debug('Client Mode. Not saving lock states')

    def _open_(self, name, mode):
        """
        """
        action = 'set_open'
        # check software interlocks and return None if True
        interlocked_valve = self._check_soft_interlocks(name)
        if interlocked_valve:
            msg = 'Software Interlock. {} is OPEN!. Will not open {}'.format(interlocked_valve.name, name)
            self.console_message = (msg, 'red')
            self.warning(msg)
            return

        r, c = self._actuate_(name, action, mode)
        if r and c:
            for pip in self.pipette_trackers:
                '''
                    a single valve can increment at most one pipette
                '''
                if pip.check_shot(name):
                    break

        return r, c

    def _close_(self, name, mode):
        """
        """
        action = 'set_closed'
        # if self._check_soft_interlocks(name):
        # self.warning('Software Interlock')
        # return
        return self._actuate_(name, action, mode)

    def _actuate_(self, name, action, mode, address=None):
        """
        """
        changed = False
        if address is None:
            v = self.get_valve_by_name(name)
            vid = name
        else:
            v = self.get_valve_by_address(address)
            vid = address

        result = None
        if v is not None:
            if not v.enabled:
                msg = '{} {} not enabled'.format(v.name, v.description)
                self.console_message = (msg, 'red')
                self.warning_dialog(msg)
            else:
                act = getattr(v, action)
                result, changed = act(mode='{}-{}'.format(self.mode, mode))

        else:
            msg = 'Valve {} not available'.format(vid)
            self.console_message = msg, 'red'
            self.warning(msg)
            # result = 'Valve %s not available' % id

        return result, changed

    def _load_valves_from_file(self, path):
        """
        """
        self.info('loading valve definitions file  {}'.format(path))

        def factory(v):
            name, hv = self._switch_factory(v)
            if self.use_explanation:
                self._load_explanation_valve(hv)
            self.valves[name] = hv
            return hv

        parser = ValveParser()
        if not parser.load(path):
            self.warning_dialog('No valves.xml file located in "{}"'.format(os.path.dirname(path)))
        else:
            for g in parser.get_groups():
                for v in parser.get_valves(group=g):
                    factory(v)

            for v in parser.get_valves():
                factory(v)

            for s in parser.get_switches():
                name, sw = self._switch_factory(s, klass=Switch)
                self.valves[name] = sw

            ps = []
            for p in parser.get_pipettes():
                pip = self._pipette_factory(p)
                if pip:
                    ps.append(pip)

            self.pipette_trackers = ps

    def _pipette_factory(self, p):
        inner = p.find('inner')
        outer = p.find('outer')
        if inner is not None and outer is not None:
            innerk = inner.text.strip()
            outerk = outer.text.strip()
            if innerk in self.valves \
                    and outerk in self.valves:
                return PipetteTracker(
                    name=p.text.strip(),
                    inner=innerk,
                    outer=outerk)

    def _switch_factory(self, v_elem, klass=None):
        if klass is None:
            klass = HardwareValve

        name = v_elem.text.strip()
        address = v_elem.find('address')
        act_elem = v_elem.find('actuator')
        description = v_elem.find('description')

        interlocks = [i.text.strip() for i in v_elem.findall('interlock')]
        if description is not None:
            description = description.text.strip()

        actname = act_elem.text.strip() if act_elem is not None else 'valve_controller'
        actuator = self.get_actuator_by_name(actname)
        if actuator is None:
            if not globalv.ignore_initialization_warnings:
                self.warning_dialog(
                    'No actuator for {}. Valve will not operate. Check setupfiles/extractionline/valves.xml'.format(
                        name))

        qs = True
        vqs = v_elem.get('query_state')
        if vqs:
            qs = vqs == 'true'

        parent = v_elem.find('parent')

        parent_name = ''
        parent_inverted = False
        if parent is not None:
            parent_name = parent.text.strip()
            inverted = parent.find('inverted')
            if inverted is not None:
                parent_inverted = to_bool(inverted.text.strip())

        check_actuation_enabled = True
        cae = v_elem.find('check_actuation_enabled')
        if cae is not None:
            check_actuation_enabled = to_bool(cae.text.strip())

        check_actuation_delay = 0
        cad = v_elem.find('check_actuation_delay')
        if cad is not None:
            check_actuation_delay = float(cad.text.strip())

        st = v_elem.find('settling_time')
        if st is not None:
            st = float(st.txt.strip())

        hv = klass(name,
                   address=address.text.strip() if address is not None else '',
                   parent=parent_name,
                   parent_inverted=parent_inverted,
                   check_actuation_enabled=check_actuation_enabled,
                   check_actuation_delay=check_actuation_delay,
                   actuator=actuator,
                   description=description,
                   query_state=qs,
                   interlocks=interlocks,
                   settling_time=st or 0)
        return name, hv

    def _load_explanation_valve(self, v):
        name = v.name.split('-')[1]
        ev = ExplanableValve(name=name,
                             address=v.address,
                             description=v.description)

        v.evalve = ev
        self.explanable_items.append(ev)

    def _get_simulation(self):
        return any([act.simulation for act in self.actuators])

        #
        # if __name__ == '__main__':
        # from pychron.loggable import Loggable
        # from threading import Timer, Thread, Event
        # from Queue import Queue
        # import random
        # class Foo(Loggable):
        # def get_state_by_name(self, m):
        # b = random.randint(1, 5) / 50.0
        # r = 0.1 + b
        # #        r = 3
        # self.info('sleep {}'.format(r))
        #             time.sleep(r)
        #             return True
        #
        #         def _get_states(self, times_up_event, sq):
        #             #        self.states = []
        #             for k in ['A', 'B', 'Ca', 'Dn', 'Es', 'F', 'G', 'H', 'I']:
        #                 if times_up_event.isSet():
        #                     break
        #
        #                 sq.put(k)
        #                 #            self.info('geting state for {}'.format(k))
        #                 s = self.get_state_by_name(k)
        #                 #            self.info('got {} for {}'.format(s, k))
        #                 if times_up_event.isSet():
        #                     break
        #                 sq.put('1' if s else '0')
        #
        #                 # return ''.join(states)
        #
        #         def get_states(self):
        #             """
        #                 with this method you need to ensure the communicators timeout
        #                 is sufficiently low. the communicator will block until a response
        #                 or a timeout. the times up event only breaks between state queries.
        #
        #             """
        #             states_queue = Queue()
        #             times_up_event = Event()
        #             t = Timer(1, lambda: times_up_event.set())
        #             t.start()
        #             #        states = self._get_states(times_up_event)
        #             #        return states
        #             t = Thread(target=self._get_states, args=(times_up_event, states_queue))
        #             t.start()
        #             t.join(timeout=1.1)
        #             s = ''
        #
        #             n = states_queue.qsize()
        #             if n % 2 != 0:
        #                 c = n / 2 * 2
        #             else:
        #                 c = n
        #
        #             i = 0
        #             while not states_queue.empty() and i < c:
        #                 s += states_queue.get_nowait()
        #                 i += 1
        #
        #                 #        n = len(s)
        #                 #        if n % 2 != 0:
        #                 #            sn = s[:n / 2 * 2]
        #                 #        else:
        #                 #            sn = s
        #                 #        s = ''.join(self.states)
        #             self.info('states = {}'.format(s))
        #             return s
        #
        #             #    v = ValveManager()
        #             #    p = os.path.join(paths.extraction_line_dir, 'valves.xml')
        #             #    v._load_valves_from_file(p)
        #
        #     from pychron.core.helpers.logger_setup import logging_setup
        #
        #     logging_setup('foo')
        #     f = Foo()
        #     for i in range(10):
        #         r = f.get_states()
        #         time.sleep(2)
        #         # print r, len(r)

        # ==================== EOF ==================================

        # ===============================================================================
        # deprecated
        # ===============================================================================
        # def claim_section(self, section, addr=None, name=None):

# try:
# vg = self.valve_groups[section]
# except KeyError:
# return True
#
# if addr is None:
# addr = self._get_system_address(name)
#
# vg.owner = addr
#
# def release_section(self, section):
#         try:
#             vg = self.valve_groups[section]
#         except KeyError:
#             return True
#
#         vg.owner = None
#     def get_system(self, addr):
#         return next((k for k, v in self.systems.iteritems() if v == addr), None)
#     def check_group_ownership(self, name, claimer):
#         grp = None
#         for g in self.valve_groups.itervalues():
#             for vi in g.valves:
#                 if vi.is_name(name):
#                     grp = g
#                     break
#         r = False
#         if grp is not None:
#             r = grp.owner == claimer
#
# #        print name, claimer,grp, r
#         return r

# def get_owners_word(self):
#         """
#          eg.
#                 1. 129.128.12.141-A,B,C:D,E,F
#                 2. A,B,C,D,E,F
#                 3. 129.128.12.141-A,B,C:129.138.12.150-D,E:F
#                     A,B,C owned by 141,
#                     D,E owned by 150
#                     F free
#         """
#         if self.actuators:
#             rs = []
#             actuator = self.actuators[0]
#             word = actuator.get_owners_word()
#             if word:
#                 groups = word.split(':')
#                 if len(groups) > 1:
#                     for gi in groups:
#                         if '-' in gi:
#                             owner, vs = gi.split('-')
#                         else:
#                             owner, vs = '', gi
#
#                         rs.append((owner, vs.split(',')))
#
#                 else:
#                     rs = [('', groups[0].split(',')), ]
#             return rs

#     def _get_system_address(self, name):
#         return next((h for k, h in self.systems.iteritems() if k == name), None)
#
#     def _load_system_dict(self):
# #        config = self.configparser_factory()
#
#         from pychron.core.helpers.parsers.initialization_parser import InitializationParser
# #        ip = InitializationParser(os.path.join(setup_dir, 'initialization.xml'))
#         ip = InitializationParser()
#
#         self.systems = dict()
#         for name, host in ip.get_systems():
#             self.systems[name] = host

#        config.read(os.path.join(setup_dir, 'system_locks.cfg'))
#
#        for sect in config.sections():
#            name = config.get(sect, 'name')
#            host = config.get(sect, 'host')
# #            names.append(name)
#            self.systems[name] = host
#
#     def _load_sections_from_file(self, path):
#         '''
#         '''
#         self.sections = []
#         config = self.get_configuration(path=path)
#         if config is not None:
#             for s in config.sections():
#                 section = Section()
#                 comps = config.get(s, 'components')
#                 for c in comps.split(','):
#                     section.add_component(c)
#
#                 for option in config.options(s):
#                     if 'test' in option:
#                         test = config.get(s, option)
#                         tkey, prec, teststr = test.split(',')
#                         t = (int(prec), teststr)
#                         section.add_test(tkey, t)
#
#                 self.sections.append(section)

#    def _get_states(self, times_up_event, sq):
#
#        def _gstate(ki):
#            sq.put(ki)
#            s = self.get_state_by_name(ki)
#            sq.put('1' if s else '0')
#
#        dv = []
#        for k, v in self.valves.iteritems():
# #        for k, _ in self.valves.items():
#            if v.query_state:
#                dv.append(k)
#                continue
#
#            if times_up_event.isSet():
#                break
#
#            _gstate(k)
#
#        if times_up_event.isSet():
#            return
#
#        for k in dv:
#            if times_up_event.isSet():
#                break
#            _gstate(k)
#    def get_states2(self, timeout=1):
#        '''
#            use event and timer to allow for partial responses
#            the timer t will set the event in timeout seconds
#
#            after the timer is started _get_states is called
#            _get_states loops thru the valves querying their state
#
#            each iteration the times_up_event is checked to see it
#            has fired if it has the the loop breaks and returns the
#            states word
#
#            to prevent the communicator from blocking longer then the times up event
#            the _gs_thread is joined and timeouts out after 1.01s
#        '''
#
#        states_queue = Queue()
#        times_up_event = Event()
#        t = Timer(1, lambda: times_up_event.set())
#        t.start()
#        try:
#
#            _gs_thread = Thread(name='valves.get_states',
#                                target=self._get_states, args=(times_up_event, states_queue))
#            _gs_thread.start()
#            _gs_thread.join(timeout=1.01)
#        except (Exception,), e:
#            pass
#
#        # ensure word has even number of elements
#        s = ''
#        i = 0
#        n = states_queue.qsize()
#        if n % 2 != 0:
#            c = n / 2 * 2
#        else:
#            c = n
#
#        while not states_queue.empty() and i < c:
#            s += states_queue.get_nowait()
#            i += 1
#
#        return s
# def _load_valves_from_filetxt(self, path):
#        '''
#
#        '''
#        c = parse_setupfile(path)
#
#        self.sector_inlet_valve = c[0][0]
#        self.quad_inlet_valve = c[0][1]
#
#        actid = 6
#        curgrp = None
#        self.valve_groups = dict()
#
#        for a in c[1:]:
#            act = 'valve_controller'
#            if len(a) == actid + 1:
#                act = a[actid]
#
#            name = a[0]
#            actuator = self.get_actuator_by_name(act)
#            warn_no_act = True
#            if warn_no_act:
#                if actuator is None:
#                    self.warning_dialog('No actuator for {}. Valve will not operate. Check setupfiles/extractionline/valves.txt'.format(name))
#            print a
#            v = HardwareValve(name,
#                     address=a[1],
#                     actuator=self.get_actuator_by_name(act),
#                     interlocks=a[2].split(','),
#                     query_valve_state=a[4] in ['True', 'true']
# #                     group=a[4]
#                     )
#            try:
#                if a[5] and a[5] != curgrp:
#                    curgrp = a[5]
#                    if curgrp in self.valve_groups:
#                        self.valve_groups[curgrp].valves.append(v)
#                    else:
#                        vg = ValveGroup()
#                        vg.valves = [v]
#                        self.valve_groups[curgrp] = vg
#                else:
#                    self.valve_groups[curgrp].valves.append(v)
#
#            except IndexError:
#
#                #there is no group specified
#                pass
#
#            s = v.get_hardware_state()
#
#            #update the extraction line managers canvas
# #            self.extraction_line_manager.canvas.update_valve_state(v.name[-1], s)
#            self.extraction_line_manager.update_valve_state(v.name[-1], s)
#            args = dict(name=a[0],
#                        address=a[1],
#                        description=a[3],
#                        canvas=self.extraction_line_manager.canvas,
#
#                        )
#            ev = ExplanableValve(**args)
#            ev.state = s if s is not None else False
#
#            self.valves[name] = v
#            self.explanable_items.append(ev)

#        for k,g in self.valve_groups.iteritems():
#
#            for v in g.valves:
#                print k,v.name
