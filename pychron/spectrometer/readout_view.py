# ===============================================================================
# Copyright 2012 Jake Ross
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

import os

# ============= standard library imports ========================
import time

import six.moves.configparser

# ============= enthought library imports =======================
from pyface.timer.do_later import do_after
from six.moves import zip
from traits.api import (
    HasTraits,
    Str,
    List,
    Any,
    Event,
    Button,
    Int,
    Bool,
    Float,
    Either,
)
from traitsui.api import UItem, VGroup, Item, HGroup, View, TableEditor, Tabbed
from traitsui.api import spring
from traitsui.handler import Handler
from traitsui.table_column import ObjectColumn

# ============= local library imports  ==========================
from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceLoggable
from pychron.pychron_constants import NULL_STR

DEFAULT_CONFIG = """-
  - name: HighVoltage
    min: 0
    max: 5
    compare: False
  - name: ElectronEnergy
    min: 53
    max: 153
    compare: False
  - name: YSymmetry
    min: -100
    max: 100
    compare: True
  - name: ZSymmetry
    min: -100
    max: 100
    compare: True
  - name: ZFocus
    min: 0
    max: 100
    compare: True
  - name: IonRepeller
    min: -22.5
    max: 53.4
    compare: True
  - name: ExtractionLens
    min: 0
    max: 100
    compare: True

-
  - name: H2
    compare: True
  - name: H1
    compare: True
  - name: AX
    compare: True
  - name: L1
    compare: True
  - name: L2
    compare: True
  - name: CDD
    compare: True
"""


class BaseReadout(HasTraits):
    name = Str
    id = Str
    value = Either(Str, Float)
    spectrometer = Any
    compare = Bool(True)
    config_value = Float
    tolerance = Float
    percent_tol = Float
    display_tolerance = Str

    # use_word = Bool(True)

    @property
    def dev(self):
        try:
            return self.value - self.config_value
        except ValueError:
            return NULL_STR

    @property
    def percent_dev(self):
        try:
            return abs(self.dev / self.config_value * 100)
        except ZeroDivisionError:
            return NULL_STR

    def set_value(self, v):
        try:
            self.value = float(v)
        except (AttributeError, ValueError, TypeError):
            if v is not None:
                self.value = v

    def config_compare(self):
        tolerance = self.percent_tol
        if tolerance:
            try:
                self.display_tolerance = "{:0.2f}%".format(tolerance * 100)
                try:
                    if (
                        abs(self.value - self.config_value) / self.config_value
                        > tolerance
                    ):
                        return self.name, self.value, self.config_value
                except TypeError:
                    pass
            except ZeroDivisionError:
                pass
        else:
            try:
                self.display_tolerance = "{:0.2f}".format(self.tolerance)
                if abs(self.value - self.config_value) > self.tolerance:
                    return self.name, self.value, self.config_value
            except TypeError:
                pass

    def compare_message(self):
        return "{} does not match. Current:{:0.3f}, Config: {:0.3f}, tol.: {}".format(
            self.name, self.value, self.config_value, self.display_tolerance
        )


class Readout(BaseReadout):
    min_value = Float(0)
    max_value = Float(100)
    tolerance = Float(0.01)
    query_timeout = 3
    _last_query = 0

    def traits_view(self):
        v = View(HGroup(Item("value", style="readonly", label=self.name)))
        return v

    def query_value(self):
        if self.query_needed and self.compare:
            parameter = self.spectrometer.get_hardware_name(self.id)
            if parameter:
                v = self.spectrometer.get_parameter(parameter)
                self.set_value(v)
                self._last_query = time.time()

    def get_percent_value(self):
        try:
            return (self.value - self.min_value) / (self.max_value - self.min_value)
        except (TypeError, ZeroDivisionError, ValueError):
            return 0

    @property
    def query_needed(self):
        return (
            not self._last_query
            or (time.time() - self._last_query) > self.query_timeout
        )


class DeflectionReadout(BaseReadout):
    pass


class ReadoutHandler(Handler):
    def closed(self, info, is_ok):
        info.object.stop()


class ReadoutView(PersistenceLoggable):
    readouts = List(Readout)
    deflections = List(DeflectionReadout)
    spectrometer = Any
    refresh = Button

    refresh_needed = Event
    refresh_period = Int(10, enter_set=True, auto_set=False)  # seconds
    compare_to_config_enabled = Bool(True)

    _alive = False
    pattributes = ("compare_to_config_enabled", "refresh_period")
    persistence_name = "readout"

    def __init__(self, *args, **kw):
        super(ReadoutView, self).__init__(*args, **kw)

        #  peristence_mixin load
        self.load()

        self._load_configuration()

    def _load_configuration(self):
        ypath = os.path.join(paths.spectrometer_dir, "readout.yaml")
        if not os.path.isfile(ypath):
            path = os.path.join(paths.spectrometer_dir, "readout.cfg")
            if os.path.isfile(path):
                self._load_cfg(path)
            else:
                if self.confirmation_dialog(
                    "no readout configuration file. \n"
                    "Would you like to write a default file at {}".format(ypath)
                ):
                    self._write_default(ypath)
                    self._load_yaml(ypath)

        else:
            self._load_yaml(ypath)

    def _load_cfg(self, path):
        self.warning_dialog(
            "Using readout.cfg is deprecated. Please consider migrating to readout.yaml"
        )
        config = six.moves.configparser.ConfigParser()
        config.read(path)
        for section in config.sections():
            rd = Readout(name=section, spectrometer=self.spectrometer)
            self.readouts.append(rd)

    def _load_yaml(self, path):
        yt = yload(path)
        if yt:
            try:
                yl, yd = yt
            except ValueError:
                yl = yt
                yd = []

            for rd in yl:
                rr = Readout(
                    spectrometer=self.spectrometer,
                    name=rd["name"],
                    id=rd.get("id", rd["name"]),
                    hardware_name=rd.get("hardware_name"),
                    min_value=rd.get("min", 0),
                    max_value=rd.get("max", 1),
                    tolerance=rd.get("tolerance", 0.01),
                    percent_tol=rd.get("percent_tolerance", 0.0),
                    compare=rd.get("compare", True),
                    query_timeout=self.refresh_period,
                )
                self.readouts.append(rr)

            for rd in yd:
                rr = DeflectionReadout(
                    spectrometer=self.spectrometer,
                    name=rd["name"],
                    id=rd.get("id", rd["name"]),
                    tolerance=rd.get("tolerance", 1),
                    compare=rd.get("compare", True),
                )
                self.deflections.append(rr)

    def _write_default(self, ypath):
        with open(ypath, "w") as wfile:
            wfile.write(DEFAULT_CONFIG)

    @property
    def ms_period(self):
        return self.refresh_period * 1000

    def start(self):
        if not self._alive:
            self._alive = True
            self._refresh_loop()

    def stop(self):
        self._alive = False

    def _refresh_loop(self):
        self._refresh()
        if self._alive:
            do_after(self.ms_period, self._refresh_loop)

    def _refresh_fired(self):
        self._refresh()

    def _refresh_period_changed(self):
        for r in self.readouts:
            r.query_timeout = self.refresh_period

    def _refresh(self):
        spec = self.spectrometer

        deflections = [r for r in self.deflections if r.compare]
        keys = [r.name for r in deflections]
        if keys:
            ds = spec.read_deflection_word(keys)
            for d, r in zip(ds, deflections):
                r.set_value(d)

        st = time.time()
        timeout = self.refresh_period * 0.95
        for rd in self.readouts:
            if time.time() - st > timeout:
                break
            rd.query_value()

        self.refresh_needed = True

        # compare to configuration values
        ne = []
        nd = []

        if not spec.simulation and self.compare_to_config_enabled:
            for nn, rs in ((ne, self.readouts), (nd, self.deflections)):
                for r in rs:
                    cv = spec.get_configuration_value(r.id)
                    if cv is None:
                        continue
                    r.config_value = cv
                    if r.compare:
                        args = r.config_compare()
                        if args:
                            nn.append(args)
                            self.debug(r.compare_message())
                    else:
                        r.set_value(NULL_STR)

            ns = ""
            if ne:
                ns = "\n".join(["{:<16s}\t{:0.3f}\t{:0.3f}".format(*n) for n in ne])

            if nd:
                nnn = "\n".join(["{:<16s}\t\t{:0.0f}\t{:0.0f}".format(*n) for n in nd])
                ns = "{}\n{}".format(ns, nnn)

            if ns:
                msg = (
                    "There is a mismatch between the current spectrometer values and the configuration.\n"
                    "Would you like to set the spectrometer to the configuration values?\n\n"
                    "Name\t\tCurrent\tConfig\n{}".format(ns)
                )
                if self.confirmation_dialog(msg, size=(725, 300)):
                    spec.send_configuration()
                    spec.set_debug_configuration_values()

    def traits_view(self):
        def ff(x):
            return "{:0.3f}".format(x) if isinstance(x, float) else x

        cols = [
            ObjectColumn(name="name", label="Name"),
            ObjectColumn(name="value", format_func=ff, label="Value", width=50),
            ObjectColumn(
                name="config_value", format="%0.3f", label="Config. Value", width=50
            ),
            ObjectColumn(name="dev", format_func=ff, label="Dev.", width=50),
            ObjectColumn(name="percent_dev", format_func=ff, label="%Dev.", width=50),
            ObjectColumn(name="display_tolerance", label="Tol."),
        ]

        dcols = [
            ObjectColumn(name="name", label="Name", width=100),
            ObjectColumn(name="value", format_func=ff, label="Value", width=100),
            ObjectColumn(name="dev", format_func=ff, label="Dev."),
            ObjectColumn(name="percent_dev", format_func=ff, label="%Dev."),
            ObjectColumn(name="display_tolerance", label="Tol."),
        ]

        b = VGroup(
            UItem("readouts", editor=TableEditor(columns=cols, editable=False)),
            label="General",
        )
        c = VGroup(
            UItem(
                "deflections",
                editor=TableEditor(columns=dcols, sortable=False, editable=False),
            ),
            label="Deflections",
        )

        v = View(
            VGroup(
                Tabbed(b, c),
                HGroup(
                    Item(
                        "compare_to_config_enabled",
                        label="Comp. Config",
                        tooltip="If checked, compare the current values to the values in the "
                        "configuration file. "
                        "Warn user if there is a mismatch",
                    ),
                    spring,
                    Item("refresh", show_label=False),
                ),
            )
        )
        return v


def new_readout_view(rv):
    rv.start()

    from pychron.processing.analyses.view.magnitude_editor import MagnitudeColumn

    cols = [
        ObjectColumn(name="name", label="Name"),
        ObjectColumn(
            name="value",
            format_func=lambda x: "{:0.3f}".format(x) if isinstance(x, float) else x,
            label="Value",
        ),
        MagnitudeColumn(name="value", label="", width=200),
    ]
    dcols = [
        ObjectColumn(name="name", label="Name", width=100),
        ObjectColumn(name="value", label="Value", width=100),
    ]

    a = HGroup(Item("refresh_period", label="Period (s)"))
    b = VGroup(
        UItem("readouts", editor=TableEditor(columns=cols, editable=False)),
        label="General",
    )
    c = VGroup(
        UItem(
            "deflections",
            editor=TableEditor(columns=dcols, sortable=False, editable=False),
        ),
        label="Deflections",
    )
    v = View(
        VGroup(a, Tabbed(b, c)),
        handler=ReadoutHandler(),
        title="Spectrometer Readout",
        width=500,
        resizable=True,
    )
    return v


# ============= EOF =============================================
