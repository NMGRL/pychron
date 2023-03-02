# ===============================================================================
# Copyright 2018 ross
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

from traits.api import Enum, Float, Property, List, Int, Bool
from traitsui.api import Item, UItem, HGroup, VGroup, Spring

from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.lcd_editor import LCDEditor
from pychron.graph.plot_record import PlotRecord
from pychron.graph.stream_graph import StreamStackedGraph
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice
import re
import time
import string

IDN_RE = re.compile(r"\w{4},\w{8},\w{7}\/[\w\#]{7},\d.\d")

PRED_RE = re.compile(r"(?P<name>[A-Za-z])")


class RangeTest:
    def __init__(self, r, test):
        self._r = int(r)
        self._test = test
        self._attr = None
        match = PRED_RE.search(test)
        if match:
            self._attr = match.group("name")

    def test(self, v):
        if self._attr and eval(self._test, {self._attr: float(v)}):
            return self._r


class Protocol:
    def __init__(self, controller):
        self._controller = controller

    def test_connection(self):
        pass

    def read_setpoint(self, *args, **kw):
        pass

    def set_setpoint(self, *args, **kw):
        pass

    def set_range(self, *args, **kw):
        pass

    def read_input(self, *args, **kw):
        pass

    def tell(self, *args, **kw):
        self._controller.tell(*args, **kw)

    def ask(self, *args, **kw):
        return self._controller.ask(*args, **kw)


class GPIBProtocol(Protocol):
    def test_connection(self):
        self.tell("*CLS")
        return self.ask("*IDN?")

    def read_setpoint(self, output, verbose=True):
        return self.ask(f"SETP? {output}", verbose=verbose)

    def set_setpoint(self, output, v):
        self.tell(f"SETP {output},{v}")

    def set_range(self, output, ra):
        self.tell(f"RANGE {output},{ra}")

    def read_input(self, tag, mode, verbose):
        return self.ask(f"{mode}RDG? {tag}", verbose=verbose)


class SCPIProtocol(Protocol):
    def test_connection(self):
        return self.ask("*IDN?")

    def read_setpoint(self, output, verbose=True):
        return self.ask(f"SOURCE:TEMPERATURE:SETPOINT? {output}", verbose=verbose)

    def set_setpoint(self, output, v):
        return self.ask(f"SOURCE:TEMPERATURE:SETPOINT {v},{output}")

    def read_input(self, tag, mode, verbose):
        return self.ask(f"FETCH:TEMPERATURE? {tag}", verbose=verbose)


class BaseLakeShoreController(CoreDevice):
    units = Enum("C", "K")
    scan_func = "update"

    input_a_enabled = Bool
    input_b_enabled = Bool

    input_a = Float
    input_b = Float
    setpoint1 = Float(auto_set=False, enter_set=True)
    setpoint1_readback = Float
    setpoint2 = Float(auto_set=False, enter_set=True)
    setpoint2_readback = Float
    range_tests = List
    num_inputs = Int
    ionames = List
    iolist = List
    iomap = List

    graph_klass = StreamStackedGraph

    verify_setpoint = Bool

    protocol_kind = Enum("GPIB", "SCPI")
    protocol = None

    def load_additional_args(self, config):
        self.set_attribute(config, "units", "General", "units", default="K")
        self.set_attribute(
            config,
            "input_a_enabled",
            "General",
            "input_a_enabled",
            default=True,
            cast="boolean",
        )
        self.set_attribute(
            config,
            "input_b_enabled",
            "General",
            "input_b_enabled",
            default=True,
            cast="boolean",
        )

        self.set_attribute(
            config, "protocol_kind", "Communications", "protocol", default="GPIB"
        )
        self.set_attribute(
            config,
            "verify_setpoint",
            "General",
            "verify_setpoint",
            cast="boolean",
            default=True,
        )
        # [Range]
        # 1=v<10
        # 2=10<v<30
        # 3=v>30

        if config.has_section("Range"):
            items = config.items("Range")

        else:
            items = [(1, "v<10"), (2, "10<v<30"), (3, "v>30")]

        if items:
            self.range_tests = [RangeTest(*i) for i in items]

        if config.has_section("IOConfig"):
            iodict = dict(config.items("IOConfig"))
            self.num_inputs = int(iodict["num_inputs"])
            for i, tag in enumerate(string.ascii_lowercase[: self.num_inputs]):
                try:
                    self.ionames.append(iodict["input_{}_name".format(tag)])
                except ValueError:
                    self.ionames.append("input_{}".format(tag))
                self.iolist.append("input_{}".format(tag))
                mapsetpoint = iodict["input_{}".format(tag)]
                if mapsetpoint.lower() == "none":
                    self.iomap.append(None)
                else:
                    self.iomap.append(mapsetpoint)
        else:
            self.num_inputs = 2
            self.iolist = ["input_a", "input_b"]
            self.ionames = ["", "", "", ""]
            self.iomap = ["setpoint1", "setpoint2", "setpoint3", "setpoint4"]

        return True

    def initialize(self, *args, **kw):
        self.communicator.write_terminator = chr(10)  # line feed \n

        klass = GPIBProtocol if self.protocol_kind == "GPIB" else SCPIProtocol
        self.protocol = klass(self)

        return super(BaseLakeShoreController, self).initialize(*args, **kw)

    def test_connection(self):
        resp = self.protocol.test_connection()
        return bool(IDN_RE.match(resp))

    def update(self, **kw):
        for tag in self.iolist:
            func = getattr(self, "read_{}".format(tag))
            v = func(**kw)
            setattr(self, tag, v)

        for tag in self.iomap:
            v = self.read_setpoint(tag)
            setattr(self, "{}_readback".format(tag), v)
        return self._update_hook()

    def setpoints_achieved(self, setpoints, tol=1):
        for i, (setpoint, tag, key) in enumerate(
            zip(setpoints, self.iomap, string.ascii_lowercase)
        ):
            if setpoint is None:
                continue

            idx = i + 1
            v = self._read_input(key, self.units)
            if tag is not None:
                try:
                    # setpoint = getattr(self, tag)
                    self.debug("{}={}, v={}".format(tag, setpoint, v))
                    if abs(v - setpoint) > tol:
                        return
                    else:
                        self.debug("setpoint {} achieved".format(idx))
                except AttributeError:
                    pass
        return True

    @get_float(default=0)
    def read_setpoint(self, output, verbose=False):
        if output is not None:
            if isinstance(output, str):
                output = re.sub("[^0-9]", "", output)

            return self.protocol.read_setpoint(output, verbose)

    def set_setpoints(self, *setpoints, block=False, delay=1):
        for i, v in enumerate(setpoints):
            if v is not None:
                idx = i + 1
                setattr(self, "setpoint{}".format(idx), v)

        if block:
            delay = max(0.5, delay)
            tol = 1
            if isinstance(block, (int, float)):
                tol = block

            while 1:
                if self.setpoints_achieved(setpoints, tol):
                    break
                time.sleep(delay)

    def set_setpoint(self, v, output=1, retries=3):
        self.set_range(v, output)
        for i in range(retries):
            self.protocol.set_setpoint(output, v)
            # self.tell("SETP {},{}".format(output, v))

            if not self.verify_setpoint:
                break

            time.sleep(2)
            sp = self.read_setpoint(output, verbose=True)
            self.debug("setpoint set to={} target={}".format(sp, v))
            if sp == v:
                break
            time.sleep(1)

        else:
            self.warning_dialog("Failed setting setpoint to {}. Got={}".format(v, sp))

    def set_range(self, v, output):
        # if v <= 10:
        #     self.tell('RANGE {},{}'.format(output, 1))
        # elif 10 < v <= 30:
        #     self.tell('RANGE {},{}'.format(output, 2))
        # else:
        #     self.tell('RANGE {},{}'.format(output, 3))

        for r in self.range_tests:
            ra = r.test(v)
            if ra:
                self.protocol.set_range(output, ra)
                break

        time.sleep(1)

    def read_input(self, v, **kw):
        if isinstance(v, int):
            v = string.ascii_lowercase[v - 1]
        return self._read_input(v, self.units, **kw)

    def read_input_a(self, **kw):
        return self._read_input("a", self.units, **kw)

    def read_input_b(self, **kw):
        return self._read_input("b", self.units, **kw)

    @get_float(default=0)
    def _read_input(self, tag, mode="C", verbose=False):
        return self.protocol.read_input(tag, mode, verbose)
        # return self.ask("{}RDG? {}".format(mode, tag), verbose=verbose)

    def _setpoint1_changed(self):
        self.set_setpoint(self.setpoint1, 1)

    def _setpoint2_changed(self):
        self.set_setpoint(self.setpoint2, 2)

    def _update_hook(self):
        r = PlotRecord((self.input_a, self.input_b), (0, 1), ("a", "b"))
        return r

    def get_control_group(self):
        grp = BorderVGroup(
            Spring(height=10, springy=False),
            HGroup(
                Item(
                    "input_a",
                    style="readonly",
                    editor=LCDEditor(width=120, ndigits=6, height=30),
                ),
                Item("setpoint1"),
                UItem(
                    "setpoint1_readback",
                    editor=LCDEditor(width=120, height=30),
                    style="readonly",
                ),
                Spring(width=10, springy=False),
                defined_when="input_a_enabled",
            ),
            HGroup(
                Item(
                    "input_b",
                    style="readonly",
                    editor=LCDEditor(width=120, ndigits=6, height=30),
                ),
                Item("setpoint2"),
                UItem(
                    "setpoint2_readback",
                    editor=LCDEditor(width=120, height=30),
                    style="readonly",
                ),
                Spring(width=10, springy=False),
                defined_when="input_b_enabled",
            ),
            label=self.name,
        )
        return grp

    def graph_builder(self, g, **kw):
        g.plotcontainer.spacing = 10
        g.new_plot(xtitle="Time f(s)", ytitle="InputA", padding=[100, 10, 0, 60])
        g.new_series()

        g.new_plot(ytitle="InputB", padding=[100, 10, 60, 0])
        g.new_series(plotid=1)


# ============= EOF =============================================
