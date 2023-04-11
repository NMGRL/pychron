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
import os
import pickle
import time
from operator import itemgetter
from pickle import PickleError
from string import digits
import json
import yaml

from traits.api import Any, Dict, List, Bool, Event, Str

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.strtools import to_bool, streq
from pychron.core.yaml import yload
from pychron.extraction_line import VERBOSE_DEBUG, VERBOSE
from pychron.extraction_line.pipettes.tracking import PipetteTracker
from pychron.globals import globalv
from pychron.hardware.core.checksum_helper import computeCRC
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.hardware.switch import Switch, ManualSwitch
from pychron.hardware.valve import HardwareValve, DoubleActuationValve
from pychron.managers.manager import Manager
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from .switch_parser import SwitchParser


def parse_interlocks(vobj, tag):
    vs = []
    if tag in vobj:
        vs = vobj[tag]
    elif "{}s".format(tag) in vobj:
        vs = vobj.get("{}s".format(tag))

    if isinstance(vs, (tuple, list)):
        interlocks = [str(i).strip() for i in vs]
    else:
        interlocks = [str(vs).strip()]

    return interlocks


def add_checksum(func):
    def wrapper(*args, **kw):
        d = func(*args, **kw)
        return "{}{}".format(d, computeCRC(d))

    return wrapper


class ValveGroup(object):
    owner = None
    valves = None


class SwitchManager(Manager):
    """
    Manager to interface with the UHV and HV pneumatic valves

    """

    switches = Dict
    explanable_items = List
    extraction_line_manager = Any
    pipette_trackers = List(PipetteTracker)
    valves_path = Str

    actuators = List

    query_valve_state = Bool(True)

    use_explanation = True

    refresh_explanation = Event
    refresh_state = Event
    refresh_lock_state = Event
    refresh_canvas_needed = Event
    refresh_owned_state = Event
    console_message = Event
    mode = None

    setup_name = Str("valves")

    _prev_keys = None

    def set_logger_level_hook(self, level):
        for v in self.switches.values():
            v.logger.setLevel(level)

        for act in self.actuators:
            act.logger.setLevel(level)

    def actuate_children(self, name, action, mode):
        """
        actuate all switches that have ``name`` defined as their parent
        """
        for v in self.switches.values():
            if v.parent == name:
                self.debug("actuating child, {}, {}".format(v.display_name, action))
                if v.parent_inverted:
                    func = (
                        self.open_by_name if action == "close" else self.close_by_name
                    )
                else:
                    func = self.open_by_name if action == "open" else self.close_by_name

                func(v.display_name, mode)

    def show_valve_properties(self, name):
        v = self.get_switch_by_name(name)
        if v is not None:
            v.edit_traits()

    def kill(self):
        super(SwitchManager, self).kill()
        self._save_states()

    def create_device(self, name, *args, **kw):
        """ """

        dev = super(SwitchManager, self).create_device(name, *args, **kw)
        dev.configuration_dir_name = self.configuration_dir_name

        if "actuator" in name or "controller" in name:
            if dev is not None:
                self.actuators.append(dev)

        return dev

    def finish_loading(self, update=False):
        """ """
        if self.actuators:
            for a in self.actuators:
                self.info("setting actuator {}".format(a.name))
                if hasattr(a, "com_device_name"):
                    self.info("comm. device = {} ".format(a.com_device_name))

        # open config file
        # setup_file = os.path.join(paths.extraction_line_dir, add_extension(self.setup_name, '.xml'))
        self._load_valves_from_file(self.valves_path)

        if globalv.load_valve_states:
            self._load_states()

        if globalv.load_soft_locks:
            self._load_soft_lock_states()

        if globalv.load_manual_states:
            self._load_manual_states()

    def set_child_state(self, name, state):
        self.debug("set states for children of {}. state={}".format(name, state))
        # elm = self.extraction_line_manager
        for k, v in self.switches.items():
            if v.parent == name:
                v.set_state(state)
                self.refresh_state = (k, state)
                # elm.update_valve_state(k, state)

    def calculate_checksum(self, vkeys):
        vs = self.switches

        val = b"".join((vs[k].state_str().encode("utf-8") for k in vkeys if k in vs))
        return binascii.crc32(val)

    def get_valve_names(self):
        return list(self.switches.keys())

    def refresh_network(self):
        self.debug("refresh network")
        for k, v in self.switches.items():
            self.refresh_state = (k, v.state, False)

        self.refresh_canvas_needed = True

    def get_indicator_state(self, name):
        v = self.get_switch_by_name(name)
        if v is not None:
            return v.get_hardware_indicator_state()

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

        vs = [(v.name.split("-")[1], v.owner) for v in self.switches.values()]

        owners = []
        for owner, valves in groupby_key(vs, itemgetter(1)):
            valves, _ = list(zip(*valves))
            v = ",".join(valves)
            if owner:
                t = "{}-{}".format(owner, v)
            else:
                t = v
            owners.append(t)

        return ":".join(owners)

    def get_locked(self):
        return [
            v.name
            for v in self.switches.values()
            if v.software_lock and not v.ignore_lock_warning
        ]

    @add_checksum
    def get_software_locks(self, version=0):
        return self._make_word("software_lock", version=version)
        # return ','.join(['{}{}'.format(k, int(v.software_lock)) for k, v in self.switches.items()])

    def _make_word(self, attr, timeout=0.25, version=0):
        word = 0x00
        keys = []

        if timeout:
            prev_keys = []
            st = time.time()
            clear_prev_keys = False
            if self._prev_keys:
                clear_prev_keys = True
                prev_keys = self._prev_keys

        for k, v in self.switches.items():
            """
            querying a lot of valves can add up hence timeout.

            most valves are not queried by default which also helps shorten
            execution time for get_states.

            """
            if timeout and k in prev_keys:
                continue

            s = bool(getattr(v, attr))
            if version:
                keys.append(k)
                word = word << 0x01 | s
            else:
                keys.append("{}{}".format(k, int(s)))

            if timeout and time.time() - st > timeout:
                self.debug("get states timeout. timeout={}".format(timeout))
                break
        else:
            # if loop completes before timeout dont save keys
            clear_prev_keys = True

        if version:
            if any((i in digits for k in keys for i in k)):
                skeys = [k if len(k) == 1 else "<{}>".format(k) for k in keys]
            else:
                skeys = [k if len(k) == 1 else "{}{}".format(len(k), k)]

        if timeout:
            if clear_prev_keys and len(keys) == len(self.switches):
                self._prev_keys = []
            else:
                self._prev_keys = keys

        if version:
            r = "{}:{:X}".format(",".join(skeys), word)
        else:
            r = ",".join(keys)
        return r

    @add_checksum
    def get_states(self, query=False, timeout=0.25, version=0):
        """
        get as many valves states before time expires
        remember last set of valves returned.

        if last set of valves less than total return
        states for the remainder valves

        """
        return self._make_word("state", timeout=timeout, version=version)

    def get_valve_by_address(self, a):
        """ """
        return self._get_valve_by(a, "address")

    def get_valve_by_description(self, a, name=None):
        """ """
        if name and name != NULL_STR:
            v = self._get_valve_by((a, name), ("description", "display_name"))
        else:
            v = self._get_valve_by(a, "description")
        return v

    def get_switch_by_name(self, n):
        """ """
        if n in self.switches:
            return self.switches[n]
        elif globalv.valve_debug:
            self.debug("Invalid switch name {}".format(n))
            self.debug(",".join(list(self.switches.keys())))

    def get_name_by_address(self, k):
        """ """
        v = self.get_valve_by_address(k)
        if v is not None:
            return v.name

    def get_name_by_description(self, d, name=None):
        v = self.get_valve_by_description(d, name=name)
        if v is not None:
            valve_name = v.name.split("-")[-1]
            return valve_name

    # def get_evalve_by_name(self, n):
    #     """
    #     """
    #     return next((item for item in self.explanable_items if item.name == n), None)

    def get_indicator_state_by_name(self, n, force=False):
        v = self.get_switch_by_name(n)
        state = None
        if v is not None:
            state = self._get_indicator_state_by(v, force=force)

        return state

    def get_indicator_state_by_description(self, n):
        """ """
        v = self.get_valve_by_description(n)
        state = None
        if v is not None:
            state = self._get_indicator_state_by(v)

        return state

    def get_state_by_name(self, n, force=False):
        """ """
        v = self.get_switch_by_name(n)
        state = None
        if v is not None:
            state = self._get_state_by(v, force=force)

        return state

    def get_state_by_description(self, n):
        """ """
        v = self.get_valve_by_description(n)
        state = None
        if v is not None:
            state = self._get_state_by(v)

        return state

    def get_actuators(self):
        act = self.actuators
        if not act:
            act = self.application.get_services(ICoreDevice)
        return act

    def get_pipette_counts(self):
        return [p.to_dict() for p in self.pipette_trackers]

    def get_pipette_count(self, name):
        for p in self.pipette_trackers:
            if streq(name, p.name):
                return p.counts
        else:
            return 0

    def get_actuator_by_name(self, name):
        act = None
        if self.actuators:
            act = next((a for a in self.actuators if a.name == name), None)
        if not act:
            if self.application:
                act = self.application.get_service_by_name(ICoreDevice, name)

        return act

    def get_software_lock(self, name, description=None, **kw):
        if description:
            v = self.get_valve_by_description(description)
        else:
            v = self.get_switch_by_name(name)

        if v is not None:
            return v.software_lock
        else:
            self.critical(
                'failed to located valve name="{}", description="{}"'.format(
                    name, description
                )
            )

    def open_switch(self, *args, **kw):
        return self.open_by_name(*args, **kw)

    def close_switch(self, *args, **kw):
        return self.close_by_name(*args, **kw)

    def open_by_name(self, name, mode="normal", force=False):
        """ """
        return self._open_(name, mode, force=force)

    def close_by_name(self, name, mode="normal", force=False):
        """ """
        return self._close_(name, mode, force=force)

    def sample(self, name, period):
        v = self.get_switch_by_name(name)
        if v and not v.state:
            self.info("start sample")
            self.open_by_name(name)

            time.sleep(period)

            self.info("end sample")
            self.close_by_name(name)

    def lock(self, name, save=True):
        """ """
        v = self.get_switch_by_name(name)
        if v is not None:
            v.lock()
            if save:
                self._save_soft_lock_states()
        else:
            self.warning("**************** Unable to lock {}".format(name))

    def unlock(self, name, save=True):
        """ """
        v = self.get_switch_by_name(name)
        if v is not None:
            v.unlock()
            if save:
                self._save_soft_lock_states()
        else:
            self.warning("*************** Unable to unlock {}".format(name))

    def set_valve_owner(self, name, owner):
        v = self.get_switch_by_name(name)
        if v is not None:
            v.owner = owner

    def validate(self, v):
        """
        return false if v's interlock valve(s) is(are) open
        else return true
        """

        return next(
            (False for vi in v.interlocks if self.get_switch_by_name(vi).state), True
        )

    def load_valve_states(self):
        self.load_indicator_states()

    def load_valve_lock_states(self, *args, **kw):
        self._load_soft_lock_states()

    def load_valve_owners(self, verbose=False, refresh_canvas=True, **kw):
        """

        :return:
        """
        # self.debug('load owners')
        update = False

        for k, v in self.switches.items():
            if not isinstance(v, HardwareValve):
                continue

            ostate = v.owner
            s = v.get_owner(verbose=verbose)
            if not isinstance(s, bool):
                s = None

            if ostate != s:
                self.refresh_owned_state = (k, s, False)
                # states.append((k, s, False))
                update = True

        if update:
            if refresh_canvas:
                self.refresh_canvas_needed = True
            return True

    def _verbose(self, msg):
        self.log(msg, VERBOSE)

    def _verbose_debug(self, msg):
        self.log(msg, VERBOSE_DEBUG)

    def load_hardware_states(self, force=False, verbose=False, refresh_canvas=True):
        """ """
        states = []
        words = {}
        for k, v in self.switches.items():
            a = (k, v.address, v.state)
            print(a, v, v.use_state_word)
            if v.use_state_word:
                if v.actuator not in words:
                    words[v.actuator] = [a]
                else:
                    words[v.actuator].append(a)

            elif v.query_state or force:
                ostate = v.state
                s = v.get_hardware_indicator_state(verbose=verbose)
                if not isinstance(s, bool):
                    s = None

                if ostate != s:
                    states.append((k, s, False))

        for actuator, items in words.items():
            stateword = actuator.get_state_word()
            print("statword", stateword)
            if stateword:
                for k, address, ostate in items:
                    try:
                        s = stateword[address]
                        if s != ostate:
                            states.append((k, s, False))
                        self.switches[k].set_state(s)
                    except KeyError:
                        self.warning(
                            "Failed getting state from valve word={}, "
                            "valve={}({})".format(stateword, k, address)
                        )
            else:
                self.warning("Actuator failed to return state word")

        if states:
            self.refresh_state = states
            if refresh_canvas:
                self.refresh_canvas_needed = True

            return True

    def load_hardware_states_old(self, force=False, verbose=False):
        self._verbose("load hardware states")
        # update = False
        states = []
        for k, v in self.switches.items():
            if v.query_state or force:
                ostate = v.state

                s = v.get_hardware_indicator_state(verbose=verbose)
                if not isinstance(s, bool):
                    s = None

                if ostate != s:
                    states.append((k, s, False))
                    # update = True

        if states:
            self.refresh_state = states
            self.refresh_canvas_needed = True

    def load_indicator_states(self):
        self._verbose("load indicator states")
        self.load_hardware_states()

    # private
    def _save_states(self):
        self._save_soft_lock_states()
        self._save_manual_states()

    def _check_positive_interlocks(self, name):
        interlocks = []
        cv = self.get_switch_by_name(name)
        if cv is not None:
            switches = self.switches
            pinterlocks = cv.positive_interlocks
            for pp in pinterlocks:
                if pp in switches:
                    v = switches[pp]
                    if not v.state:
                        interlocks.append(pp)
        return interlocks

    def _check_soft_interlocks(self, name):
        """ """
        cv = self.get_switch_by_name(name)
        self._verbose_debug("check software interlocks {}".format(name))
        if cv is not None:
            interlocks = cv.interlocks
            self._verbose_debug("interlocks {}".format(interlocks))
            switches = self.switches
            for interlock in interlocks:
                if interlock in switches:
                    v = switches[interlock]
                    if v.state:
                        self._verbose_debug("interlocked {}".format(interlock))
                        return v

    def _get_indicator_state_by(self, v, force=False):
        state = None
        if (self.query_valve_state and v.query_state) or force:
            state = v.get_hardware_indicator_state(verbose=False)
            if not v.actuator or v.actuator.simulation:
                state = None

        if state is None:
            state = v.state

        return state

    def _get_state_by(self, v, force=False):
        """ """
        state = None
        if (self.query_valve_state and v.query_state) or force:
            state = v.get_hardware_state(verbose=False)
            if not v.actuator or v.actuator.simulation:
                state = None

        if state is None:
            state = v.state
        else:
            v.state = state

        return state

    def _get_valve_by(self, a, attr):
        if isinstance(a, tuple):
            for vi in self.switches.values():
                if all((getattr(vi, attri) == ai for ai, attri in zip(a, attr))):
                    return vi
        else:
            return next(
                (
                    valve
                    for valve in self.switches.values()
                    if getattr(valve, attr) == a
                ),
                None,
            )

    def _validate_checksum(self, word):
        if word is not None:
            checksum = word[-4:]
            data = word[:-4]
            # self.debug('{} {}'.format(data, checksum))
            expected = computeCRC(data)
            if expected != checksum:
                self.warning(
                    "The checksum is not correct for this message. Expected: {}, Actual: {}".format(
                        expected, checksum
                    )
                )
            else:
                return True

    def _parse_word(self, word):
        """
        ABC<EA>D<FA>:ff

        :param word:
        :return:
        """

        # def tokenize(keys):
        #     buf = ""
        #     add = False
        #     if "<" in keys:
        #
        #         for k in keys:
        #             if add:
        #                 if k == ">":
        #                     add = False
        #                     yield buf
        #                     buf = ""
        #                     continue
        #
        #                 buf += k
        #                 continue
        #
        #             if "<" == k:
        #                 add = True
        #                 continue
        #
        #             yield k
        #     else:
        #         cnt = 0
        #         c = 0
        #         for k in keys:
        #             if add:
        #                 cnt += 1
        #                 if cnt > c:
        #                     yield buf
        #
        #                     buf = ""
        #                     cnt = 0
        #                     if k in digits:
        #                         c = int(k)
        #                     else:
        #                         add = False
        #                         yield k
        #
        #                     continue
        #
        #                 buf += k
        #                 continue
        #
        #             if k in digits:
        #                 c = int(k)
        #                 add = True
        #                 continue
        #             yield k
        #
        #         if buf:
        #             yield buf

        d = {}
        if word is not None:
            try:
                if "|" in word:
                    keys, states = word.split("|")
                    states = int(states, 16)

                    for k in keys.split(",")[::-1]:
                        if k.startswith("<") and k.endswith(">"):
                            k = k[1:-1]
                        d[k] = bool(states & 1)
                        states = states >> 1

                elif "," in word:
                    packets = word.split(",")
                    n, nn = len(packets), len(self.switches)
                    if n < nn:
                        self.warning(
                            "Valve word length is too short. All valve states will not be updated!"
                            " Word:{}, Num Valves: {}".format(n, nn)
                        )

                    for packet in packets:
                        key = packet[:-1]
                        state = packet[-1:].strip()
                        d[key] = bool(int(state))
                else:
                    for i in range(0, len(word), 2):
                        packet = word[i : i + 2]
                        try:
                            key, state = packet[0], packet[1]
                            d[key] = bool(int(state))
                        except IndexError:
                            return d
            except ValueError as v:
                self.critical("switch_manager._parse_word exception. {}".format(v))
        return d

    def _load_states(self):
        self._verbose_debug("$$$$$$$$$$$$$$$$$$$$$ Load states")
        self.load_hardware_states(force=True)

    def _load_manual_states(self):
        p = os.path.join(paths.hidden_dir, "{}_manual_states".format(self.name))
        if os.path.isfile(p):
            self.info("loading manual states from {}".format(p))

            with open(p, "rb") as f:
                try:
                    ms = pickle.load(f)
                except PickleError:
                    return

                for k, s in self.switches.items():
                    if k in ms:
                        s.state = ms[k]

    def _load_soft_lock_states(self):
        p = os.path.join(paths.hidden_dir, "{}_soft_lock_state".format(self.name))
        if os.path.isfile(p):
            self.info("loading soft lock states from {}".format(p))

            with open(p, "rb") as f:
                try:
                    sls = pickle.load(f)
                except PickleError:
                    return

                for v in self.switches:
                    if v in sls and sls[v]:
                        self.lock(v, save=False)
                    else:
                        self.unlock(v, save=False)

    def _save_manual_states(self):
        p = os.path.join(paths.hidden_dir, "{}_manual_states".format(self.name))
        self.info("saving manual states to {}".format(p))
        with open(p, "wb") as f:
            obj = {
                k: v.state
                for k, v in self.switches.items()
                if isinstance(v, ManualSwitch)
            }
            pickle.dump(obj, f)

    def _save_soft_lock_states(self):
        p = os.path.join(paths.hidden_dir, "{}_soft_lock_state".format(self.name))
        self.info("saving soft lock states to {}".format(p))
        with open(p, "wb") as f:
            obj = {k: v.software_lock for k, v in self.switches.items()}
            # obj = dict([(k, v.software_lock) for k, v in self.switches.iteritems()])

            pickle.dump(obj, f)

    def _open_(self, name, mode, force):
        """ """
        action = "set_open"
        # check software interlocks and return None if True
        interlocked_valve = self._check_soft_interlocks(name)
        if interlocked_valve:
            msg = "Software Interlock. {} is OPEN!. Will not open {}".format(
                interlocked_valve.name, name
            )
            self.console_message = (msg, "red")
            self.warning(msg)
            return False, False

        positive_interlocks = self._check_positive_interlocks(name)
        if positive_interlocks:
            msg = "Positive Interlocks not all enabled. {} not opened".format(
                ",".join(positive_interlocks)
            )
            self.console_message = (msg, "red")
            self.warning(msg)
            return False, False

        r, c = self._actuate_(name, action, mode, force=force)
        if r and c:
            for pip in self.pipette_trackers:
                """
                a single valve can increment at most one pipette
                """
                if pip.check_shot(name):
                    break

        return r, c

    def _close_(self, name, mode, force):
        action = "set_closed"
        interlocked_valve = self._check_soft_interlocks(name)
        if interlocked_valve:
            s = self.get_switch_by_name(name)
            ret = False

            iname = interlocked_valve.name
            if s and not s.state:
                self.warning(
                    "Software Interlock. {} is OPEN. But {} is already closed".format(
                        iname, name
                    )
                )
                ret = True
            else:
                msg = "Software Interlock. {} is OPEN!. Will not close {}".format(
                    iname, name
                )
                self.console_message = (msg, "red")
                self.warning(msg)

            return ret, False

        return self._actuate_(name, action, mode, force=force)

    def _actuate_(self, name, action, mode, address=None, force=None):
        changed = False
        if address is None:
            v = self.get_switch_by_name(name)
            vid = name
        else:
            v = self.get_valve_by_address(address)
            vid = address

        result = None
        if v is not None:
            if not v.enabled:
                msg = "{} {} not enabled".format(v.name, v.description)
                self.console_message = (msg, "red")
                self.warning_dialog(msg)
            else:
                act = getattr(v, action)
                result, changed = act(mode="{}-{}".format(self.mode, mode), force=force)
                if isinstance(v, ManualSwitch):
                    self._save_manual_states()
        else:
            msg = "Valve {} not available".format(vid)
            self.console_message = msg, "red"
            self.warning(msg)

        # update actuation tracker
        if changed:
            self.refresh_explanation = True
            if v.track_actuation:
                self._update_actuation_tracker(v)

        if result is None and (
            globalv.communication_simulation or globalv.experiment_debug
        ):
            result = True
            changed = True

        return result, changed

    def _update_actuation_tracker(self, v):
        obj = self._load_actuation_tracker()

        vobj = obj.get(v.name, {})
        if "start" not in vobj:
            vobj["start"] = v.last_actuation
            vobj["start_count"] = vobj.get("count", 1)

        vobj["count"] = a = vobj.get("count", 0) + 1

        v.actuations = a

        vobj["timestamp"] = v.last_actuation
        obj[v.name] = vobj

        p = paths.actuation_tracker_file

        with open(p, "w") as wfile:
            json.dump(obj, wfile)

    def _load_actuation_tracker(self):
        p = paths.actuation_tracker_file
        obj = {}
        if p:
            if os.path.isfile(p):
                with open(p, "r") as rfile:
                    obj = json.load(rfile)
            else:
                p = paths.actuation_tracker_file_yaml
                if p and os.path.isfile(p):
                    obj = yload(p)

        return obj or {}

    def _load_valves_from_file(self, path):
        self.info("loading valve definitions file  {}".format(path))

        actuations = self._load_actuation_tracker()
        parser = SwitchParser()

        def factory(v, use_explanation=True, klass=HardwareValve):
            if parser.is_yaml:
                ff = self._switch_factory_yaml
            else:
                ff = self._switch_factory_xml

            aa = ff(v, actuations, klass=klass)
            if aa:
                n, hv = aa
                if use_explanation:
                    if self.use_explanation:
                        hv.explain_enabled = True
                self.switches[n] = hv
                return hv

        if not parser.load(path):
            self.warning_dialog('Invalid valve file. "{}"'.format(path))
        else:
            for g in parser.get_groups():
                for v in parser.get_valves(group=g):
                    factory(v)

            for v in parser.get_valves():
                factory(v)

            for klass, func in (
                (Switch, parser.get_switches),
                (ManualSwitch, parser.get_manual_valves),
                (DoubleActuationValve, parser.get_double_actuation_valves),
            ):
                for s in func():
                    print(s, klass)
                    factory(s, use_explanation=False, klass=klass)

            ps = []
            for p in parser.get_pipettes():
                if parser.is_yaml:
                    func = self._pipette_factory_yaml
                else:
                    func = self._pipette_factory_xml
                pip = func(p)
                if pip:
                    ps.append(pip)

            self.pipette_trackers = ps
            self._report_valves()

    def _report_valves(self):
        self.debug(
            "========================== Switch Report =========================="
        )

        widths = []
        keys = [
            "name",
            "address",
            "state_address",
            "actuator_name",
            "actuator_obj",
            "state_device_name",
            "state_device_obj",
            "state_invert",
            "query_state",
        ]
        for k in keys:
            vs = [
                getattr(v, k) if hasattr(v, k) else "---"
                for v in self.switches.values()
            ]
            vs = [len(str(vi) if vi else k) for vi in vs]
            vs = max(len(k), max(vs)) + 3

            widths.append(vs)
        # widths =[32,40,40,20,20]
        header = ["{{:<{}s}}".format(w).format(v) for w, v in zip(widths, keys)]
        self.debug("".join(header))
        for klass, vs in groupby_key(
            self.switches.values(), key=lambda v: str(type(v))
        ):
            for v in vs:
                self.debug(v.summary(widths, keys))
        self.debug(
            "===================================================================="
        )

    def _pipette_factory_yaml(self, pobj):
        inner = pobj.get("inner")
        outer = pobj.get("outer")
        if inner in self.switches and outer in self.switches:
            return PipetteTracker(
                name=pobj.get("name", "Pipette"), inner=str(inner), outer=str(outer)
            )

    def _pipette_factory_xml(self, p):
        inner = p.find("inner")
        outer = p.find("outer")
        if inner is not None and outer is not None:
            innerk = inner.text.strip()
            outerk = outer.text.strip()
            if innerk in self.switches and outerk in self.switches:
                return PipetteTracker(name=p.text.strip(), inner=innerk, outer=outerk)

    def _switch_factory_yaml(self, vobj, actuations, klass=HardwareValve):
        ctx = self._make_switch_yaml_ctx(vobj, klass)
        return self._switch_factory(ctx, actuations, klass, "yaml")

    def _switch_factory_xml(self, vobj, actuations, klass=HardwareValve):
        ctx = self._make_switch_xml_ctx(vobj, klass)
        return self._switch_factory(ctx, actuations, klass, "xml")

    def _switch_factory(self, ctx, actuations, klass, ext):
        if ctx:
            for b in ("actuator", "state_device"):
                key = "{}_name".format(b)
                actuator = ctx.get(key)
                if b == "state_device" and not actuator:
                    continue

                actuator = self.get_actuator_by_name(actuator)
                if actuator is None and klass != ManualSwitch:
                    if not globalv.ignore_initialization_warnings:
                        available_actnames = [a.name for a in self.get_actuators()]
                        self.debug(
                            'Configured actuator="{}". Available="{}"'.format(
                                key, available_actnames
                            )
                        )
                        self.warning_dialog(
                            'No actuator for "{}". Valve will not operate. '
                            "Check setupfiles/extractionline/valves.{}".format(
                                b, ctx["name"], ext
                            )
                        )

                ctx[b] = actuator

            name = ctx.pop("name")
            hv = klass(name, **ctx)
            ad = actuations.get(hv.name)
            if ad is not None:
                hv.actuations = ad.get("count", 0)
                hv.last_actuation = ad.get("timestamp", "")

            return name, hv

    def _make_switch_yaml_ctx(self, vobj, klass):
        name = str(vobj.get("name"))
        if not name:
            self.warning("Must specify a name for all switches.")
            return

        address = vobj.get("address", "")
        actuator_name = vobj.get("actuator", "switch_controller")
        state_dev_obj = vobj.get("state_device", None)

        if not address:
            if isinstance(klass, Switch):
                self.warning_dialog('No Address set for "{}"'.format(name))
                return

        state_dev_name = ""
        state_address = ""
        state_invert = False
        if klass != ManualSwitch:
            if state_dev_obj is not None:
                state_dev_name = state_dev_obj.get("name", "")
                state_address = state_dev_obj.get("address", "")
                state_invert = to_bool(state_dev_obj.get("inverted", False))
            else:
                state_address = vobj.get("state_address", "")

        parent = vobj.get("parent")
        parent_name = ""
        parent_inverted = False
        if parent is not None:
            parent_name = parent.get("name", "")
            parent_inverted = to_bool(parent.get("inverted"))

        ctx = dict(
            name=str(name),
            inverted_logic=to_bool(vobj.get("inverted_logic", False)),
            track_actuation=to_bool(vobj.get("track", True)),
            address=str(address),
            parent=parent_name,
            parent_inverted=parent_inverted,
            check_actuation_enabled=to_bool(vobj.get("check_actuation_enabled", True)),
            check_actuation_delay=float(vobj.get("check_actuation_delay", 0)),
            actuator_name=actuator_name,
            state_device_name=state_dev_name,
            state_address=str(state_address),
            state_invert=state_invert,
            description=str(vobj.get("description", "")),
            query_state=to_bool(vobj.get("query_state", True)),
            ignore_lock_warning=to_bool(vobj.get("ignore_lock_warning", False)),
            positive_interlocks=parse_interlocks(vobj, "positive_interlock"),
            interlocks=parse_interlocks(vobj, "interlock"),
            settling_time=float(vobj.get("settling_time", 0)),
        )
        return ctx

    def _make_switch_xml_ctx(self, v_elem, klass):
        if not v_elem.text:
            self.warning(
                "Must specify a name for all switches. i.e. must provide text in <valve></valve> tags"
            )
            return
        name = v_elem.text.strip()

        address = v_elem.find("address")
        act_elem = v_elem.find("actuator")
        state_elem = v_elem.find("state_device")
        description = v_elem.find("description")

        positive_interlocks = [
            i.text.strip() for i in v_elem.findall("positive_interlock")
        ]
        interlocks = [i.text.strip() for i in v_elem.findall("interlock")]
        if description is not None:
            description = description.text.strip()
        else:
            description = ""

        if address is not None:
            address = address.text.strip()
        else:
            address = ""
            if isinstance(klass, Switch):
                self.warning_dialog('No Address set for "{}"'.format(name))
                return

        actname = ""
        state_device_name = ""
        state_address = ""
        state_invert = False
        if klass != ManualSwitch:
            actname = (
                act_elem.text.strip() if act_elem is not None else "switch_controller"
            )
            if state_elem is not None:
                state_device_name = state_elem.text.strip()
                state_address = v_elem.find("state_address")
                if state_address is not None:
                    state_address = state_address.text.strip()
                else:
                    state_address = address

                si = v_elem.find("state_invert")
                if si is not None:
                    state_invert = to_bool(si.text.strip())

        qs = True
        vqs = v_elem.find("query_state")
        if vqs is None:
            vqs = v_elem.get("query_state")
        else:
            vqs = vqs.text

        if vqs is not None:
            qs = to_bool(vqs.strip())

        parent = v_elem.find("parent")

        parent_name = ""
        parent_inverted = False
        if parent is not None:
            parent_name = parent.text.strip()
            inverted = parent.find("inverted")
            if inverted is not None:
                parent_inverted = to_bool(inverted.text.strip())

        check_actuation_enabled = True
        cae = v_elem.find("check_actuation_enabled")
        if cae is not None:
            check_actuation_enabled = to_bool(cae.text.strip())

        ignore_lock_warning = False
        ilw = v_elem.find("ignore_lock_warning")
        if ilw is not None:
            ignore_lock_warning = to_bool(ilw.text.strip())

        check_actuation_delay = 0
        cad = v_elem.find("check_actuation_delay")
        if cad is not None:
            check_actuation_delay = float(cad.text.strip())

        st = v_elem.find("settling_time")
        if st is not None:
            st = float(st.txt.strip())

        track = v_elem.find("track")
        if track is None:
            track = True
        else:
            track = to_bool(track.text.strip())

        use_state_word = v_elem.find("use_state_word")

        if use_state_word is not None:
            use_state_word = to_bool(use_state_word.text.strip())

        ctx = dict(
            name=name,
            track_actuation=track,
            address=address,
            parent=parent_name,
            parent_inverted=parent_inverted,
            check_actuation_enabled=check_actuation_enabled,
            check_actuation_delay=check_actuation_delay,
            actuator_name=actname,
            state_device_name=state_device_name or "",
            state_address=state_address,
            state_invert=state_invert,
            description=description,
            query_state=qs,
            ignore_lock_warning=ignore_lock_warning,
            positive_interlocks=positive_interlocks,
            interlocks=interlocks,
            settling_time=st or 0,
            use_state_word=bool(use_state_word),
        )

        return ctx

    def _get_simulation(self):
        return any([act.simulation for act in self.actuators])


# ==================== EOF ==================================
