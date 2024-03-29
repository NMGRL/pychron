# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Bool, Property, Float, CInt, List, Str, Any
from traitsui.api import View, Item, HGroup, spring

# ============= standard library imports ========================
from threading import Timer as OneShotTimer, Thread, Event
import time

# ============= local library imports  ==========================
from pychron.core.helpers.timer import Timer as PTimer
from pychron.loggable import Loggable


def convert_to_bool(v):
    try:
        v = float(v)
        return bool(v)
    except:
        return v.lower().strip() in ["t", "true", "on"]


class Flag(Loggable):
    _set = Bool(False)
    display_state = Property(Bool, depends_on="_set")
    owner = Str

    def __init__(self, name, *args, **kw):
        self.name = name

        self.timeout = 60
        self._pinged = None
        self._monitor_thread = None
        self._monitor_evt = None

        super(Flag, self).__init__(*args, **kw)

    def set_owner(self, owner):
        self.owner = owner

    def traits_view(self):
        v = View(
            HGroup(
                Item("name", show_label=False, style="readonly"),
                spring,
                Item("display_state", show_label=False),
            )
        )
        return v

    def _get_display_state(self):
        return self._set

    def _set_display_state(self, v):
        self.set(v)

    def ping(self):
        self._pinged = time.time()
        return self._pinged

    def get(self, *args, **kw):
        return int(self._set)

    def set(self, value):
        ovalue = value
        if isinstance(value, str):
            value = convert_to_bool(value)
        else:
            value = bool(value)
        self.info("setting flag state to {} ({})".format(value, ovalue))

        if value:
            self._monitor_evt = Event()
            self._monitor_thread = Thread(target=self._monitor)
            self._monitor_thread.setDaemon(1)
            self._monitor_thread.start()
        else:
            if self._monitor_evt:
                self._monitor_evt.set()

        self._set = value
        return True

    def clear(self):
        self.info("clearing flag")
        self._set = False
        if self._monitor_evt:
            self._monitor_evt.set()

    def isSet(self):
        return self._set

    def _monitor(self):
        evt = self._monitor_evt
        timeout = self.timeout
        self._pinged = time.time()
        while not evt.is_set():
            if time.time() - self._pinged > timeout:
                if self._set:
                    self.info("auto canceling flag")
                    self.clear()
                break

            time.sleep(5)


class TimedFlag(Flag):
    duration = Float(1)

    display_time = Property(depends_on="_time_remaining")
    _time_remaining = CInt(0)

    def __init__(self, *args, **kw):
        super(TimedFlag, self).__init__(*args, **kw)
        self._start_time = None
        self._uperiod = 1000
        self._ping_result = None
        self._update_timer = None

    def clear(self):
        super(TimedFlag, self).clear()
        self._update_timer.Stop()
        self._ping_result = "Complete"

    def ping(self):
        ret = super(TimedFlag, self).ping()
        if self._ping_result == "Complete":
            ret = "Complete"
        return ret

    def _get_display_time(self):
        return self._time_remaining

    def traits_view(self):
        v = View(
            HGroup(
                Item("name", style="readonly"),
                spring,
                Item("display_time", format_str="%03i", style="readonly"),
                Item("display_state"),
                show_labels=False,
            )
        )
        return v

    def set(self, value):
        self._ping_result = None
        set_duration = True
        if isinstance(value, bool):
            set_duration = False

        try:
            value = float(value)
        except ValueError:
            return "Invalid flag value"

        super(TimedFlag, self).set(value)
        if self.isSet():
            if set_duration:
                self.duration = value
                self._time_remaining = value
            else:
                self._time_remaining = self.duration

            self._start_time = time.time()
            self._update_timer = PTimer(self._uperiod, self._update_time)

            t = OneShotTimer(self.duration, self.clear)
            t.start()

        return True

    def isStarted(self):
        return self._start_time is not None

    def get(self, *args, **kw):
        t = 0
        if self.isSet() and self.isStarted():
            t = max(0, self.duration - (time.time() - self._start_time))

        return t

    def _update_time(self):
        self._time_remaining = round(self.get())


class ValveFlag(Flag):
    """
    a ValveFlag holds a list of valves keys (A, B, ...)

    if the flag is set then the these valves should be locked out
    from being actuated by ip addresses other than the owner of this
    flag

    valves should (can) not occur in multiple ValveFlags
    """

    valves = List
    owner = Str
    valves_str = Property(depends_on="valves")
    manager = Any

    def set(self):
        super(ValveFlag, self).set()

        owner = self.owner if self._set else None
        for vi in self.valves:
            self.manager.set_valve_owner(vi, owner)

    def traits_view(self):
        v = View(
            HGroup(
                Item("name", show_label=False, style="readonly"),
                Item("valves_str", style="readonly", label="Valves"),
            )
        )
        return v

    def _get_valves_str(self):
        return ",".join(self.valves)


# ============= EOF =============================================
