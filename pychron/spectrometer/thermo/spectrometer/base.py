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
from __future__ import absolute_import

import os
import time

from numpy import array, argmin
from traits.api import Int, Property, List, Str, DelegatesTo, Bool, Float

from pychron.core.helpers.strtools import csv_to_floats
from pychron.core.progress import open_progress
from pychron.core.ramper import StepRamper
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.pychron_constants import (
    QTEGRA_INTEGRATION_TIMES,
    QTEGRA_DEFAULT_INTEGRATION_TIME,
)
from pychron.spectrometer import get_spectrometer_config_path
from pychron.spectrometer.base_spectrometer import BaseSpectrometer


def normalize_integration_time(it):
    """
    find the integration time closest to "it"
    """
    try:
        x = array(QTEGRA_INTEGRATION_TIMES)
        return x[argmin(abs(x - it))]
    except TypeError:
        return 1.0


def calculate_radius(m_e, hv, mfield):
    """
    m_e= mass/charge
    hv= accelerating voltage (V)
    mfield= magnet field (H)
    """
    r = ((2 * m_e * hv) / mfield**2) ** 0.5

    return r


class ThermoSpectrometer(BaseSpectrometer):
    integration_time = Float
    integration_times = List(QTEGRA_INTEGRATION_TIMES)
    magnet_dac = DelegatesTo("magnet", prefix="dac")

    magnet_dacmin = DelegatesTo("magnet", prefix="dacmin")
    magnet_dacmax = DelegatesTo("magnet", prefix="dacmin")

    current_hv = DelegatesTo("source")

    sub_cup_configurations = List
    sub_cup_configuration = Property(depends_on="_sub_cup_configuration")
    _sub_cup_configuration = Str

    dc_start = Int(0)
    dc_stop = Int(500)
    dc_step = Int(50)
    dc_stepmin = Int(1)
    dc_stepmax = Int(1000)
    dc_threshold = Int(3)
    dc_npeak_centers = Int(3)

    send_config_on_startup = Bool

    max_deflection = Int(500)

    _debug_values = None

    _test_connect_command = "GetIntegrationTime"

    def hardware_names(self):
        return {
            "ion_repeller": "Ion Repeller Set",
            "electron_energy": "Electron Energy Set",
            "y_symmetry": "Y-Symmetry Set",
            "z_symmetry": "Z-Symmetry Set",
            "extraction_lens": "Extraction Lens Set",
            "z_focus": "Z-Focus Set",
            "hv": "HV",
            "trap.voltage": "Trap Voltage Readback",
            "trap.current": "Trap Current Readback",
        }

    def make_deflection_dict(self):
        names = self.detector_names
        values = self.read_deflection_word(names)
        return dict(list(zip(names, values)))

    def make_configuration_dict(self):
        keys = list(self.hardware_names().values())
        values = self.get_parameter_word(keys)
        d = dict(list(zip(keys, values)))

        key = "Electron Energy Set"
        if key in d:
            d[key] = float("{:0.2f}".format(d[key]))

    def make_gains_dict(self):
        return {di.name: di.get_gain() for di in self.detectors}

    def get_detector_active(self, dname):
        """
        return True if dname in the list of intensity keys
        e.g.

        keys, signals = get_intensities
        return dname in keys

        :param dname:
        :return:
        """
        keys, prev, _ = self.get_intensities()
        return dname in keys

    def test_intensity(self):
        """
        test if intensity is changing. make 2 measurements if exactlly the same for all
        detectors make third measurement if same as 1,2 make fourth measurement if same
        all four measurements same then test fails
        :return:
        """
        ret, err = True, ""
        keys, one, _, _ = self.get_intensities()
        it = 0.1 if self.simulation else self.integration_time

        pv = None
        for i in range(4):
            time.sleep(it)
            _, v, _, _ = self.get_intensities()
            if pv is None or all(pv == v):
                pv = v
            else:
                break
        else:
            ret = False
        # time.sleep(it)
        # keys, two, _, _ = self.get_intensities()
        # if all(one == two):
        #     time.sleep(it)
        #     keys, three, _, _ = self.get_intensities()
        #     if all(two == three):
        #         time.sleep(it)
        #         keys, four, _, _ = self.get_intensities()
        #         if all(three == four):
        #             ret = False
        return ret, err

    def set_gains(self, history=None):
        """

        :param history:
        :return: list
        """
        if history:
            self.debug(
                "setting gains to {}, user={}".format(
                    history.create_date, history.username
                )
            )
        for di in self.detectors:
            di.set_gain()

        return {di.name: di.gain for di in self.detectors}

    def load_current_detector_gains(self):
        """
        load the detector gains from the spectrometer
        """
        for di in self.detectors:
            di.get_gain()

    def read_integration_time(self):
        return self.ask("GetIntegrationTime")

    def set_integration_time(self, it, force=False):
        """

        :param it: float, integration time
        :param force: set integration even if "it" is not different than self.integration_time
        :return: float, integration time
        """
        it = normalize_integration_time(it)
        if self.integration_time != it or force:
            self.debug("setting integration time = {}".format(it))
            name = "SetIntegrationTime"
            self.set_parameter(name, it)
            self.trait_setq(integration_time=it)

            # this is a hail mary to potential make qtegra happier post setting integration time
            self.debug("sleeping 2 seconds after setting integration time")
            time.sleep(2)

        return it

    def set_parameter(self, name, v, post_delay=None):
        if not name.startswith("Set"):
            mk = self.hardware_names()
            cmd = "SetParameter {},{}".format(mk.get(name, name), v)
        elif name == "HV":
            cmd = "SetHV {}".format(v)
        else:
            cmd = "{} {}".format(name, v)

        self.ask(cmd)
        if post_delay:
            time.sleep(post_delay)

    def get_hardware_name(self, k):
        d = self.hardware_names()
        return d.get(k)

    def get_parameter(self, cmd):
        if hasattr(self.source, "read_{}".format(cmd.lower())):
            return getattr(self.source, "read_{}".format(cmd.lower()))()
        else:
            return self.ask("GetParameter {}".format(cmd))

    def set_deflection(self, name, value):
        det = self.get_detector(name)
        if det:
            det.deflection = value
        else:
            self.warning(
                'Could not find detector "{}". Deflection Not Possible'.format(name)
            )

    def get_deflection(self, name, current=False):
        """
        get deflection by detector name

        :param name: str, detector name
        :param current: bool, if True query qtegra
        :return: float
        """
        deflection = 0
        det = self.get_detector(name)
        if det:
            if current:
                det.read_deflection()
            deflection = det.deflection
        else:
            self.warning('Failed getting deflection for detector ="{}"'.format(name))

        return deflection

    def read_deflection_word(self, keys):
        x = self.ask(
            "GetDeflections {}".format(",".join(keys)), verbose=False, quiet=True
        )
        x = self._parse_word(x)
        return x

    def read_parameter_word(self, keys):
        x = self.ask(
            "GetParameters {}".format(",".join(keys)), verbose=True, quiet=False
        )
        x = self._parse_word(x)
        return x

    def get_configuration_value(self, key):
        config = self._get_cached_config()
        ret = 0
        if config is not None:
            if "." in key:
                section, key = key.split(".")
                try:
                    opt = config[section]
                    ret = opt.get(key, opt.get(key.lower(), 0))
                except KeyError:
                    pass

            else:
                for d in config.values():
                    try:
                        ret = d[key]
                    except KeyError:
                        try:
                            ret = d[key.lower()]
                        except KeyError:
                            pass
        return ret

    def set_debug_configuration_values(self):
        if self.simulation:
            config = self._get_cached_config()
            if config is not None:
                d = config["source"]
                keys = (
                    "ElectronEnergy",
                    "YSymmetry",
                    "ZSymmetry",
                    "ZFocus",
                    "IonRepeller",
                    "ExtractionLens",
                )
                ds = [0] + [d[k.lower()] for k in keys]
                self._debug_values = ds

    # ===============================================================================
    # load
    # ===============================================================================
    def load_configurations(self):
        """
        load configurations from Qtegra
        :return:
        """
        # self.sub_cup_configurations = ['A', 'B', 'C']
        # self._sub_cup_configuration = 'B'
        #
        # scc = self.ask('GetSubCupConfigurationList Argon', verbose=False)
        # if scc:
        #     if 'ERROR' not in scc:
        #         self.sub_cup_configurations = scc.split('\r')
        #
        # n = self.ask('GetActiveSubCupConfiguration')
        # if n:
        #     if 'ERROR' not in n:
        #         self._sub_cup_configuration = n

        self.molecular_weight = "Ar40"

    def load(self):
        """
        load detectors
        load setupfiles/spectrometer/config.cfg file
        load magnet
        load deflections coefficients

        :return:
        """
        config = super(ThermoSpectrometer, self).load()

        pd = "Protection"
        if config.has_section(pd):

            self.magnet.use_beam_blank = self.config_get(
                config, pd, "use_beam_blank", cast="boolean", default=False
            )
            self.magnet.use_detector_protection = self.config_get(
                config, pd, "use_detector_protection", cast="boolean", default=False
            )
            self.magnet.beam_blank_threshold = self.config_get(
                config, pd, "beam_blank_threshold", cast="float", default=0.1
            )

            # self.magnet.detector_protection_threshold = self.config_get(config, pd,
            # 'detector_protection_threshold',
            # cast='float', default=0.1)
            ds = self.config_get(config, pd, "detectors")
            if ds:
                ds = ds.split(",")
                self.magnet.protected_detectors = ds
                for di in ds:
                    self.info(
                        'Making protection available for detector "{}"'.format(di)
                    )

        if config.has_section("Deflections"):
            if config.has_option("Deflections", "max"):
                v = config.getint("Deflections", "max")
                if v:
                    self.max_deflection = v

        self.debug("Detectors {}".format(self.detectors))
        for d in self.detectors:
            d.load_deflection_coefficients()

    def start(self):
        self.debug(
            "********** Spectrometer start. send configuration: {}".format(
                self.send_config_on_startup
            )
        )
        if self.send_config_on_startup:
            self.send_configuration(use_ramp=True, ramp_confirm=True)

    def settle(self):
        time.sleep(self.integration_time * 2)

    # ===============================================================================
    # signals
    # ===============================================================================
    def read_intensities(self, tagged=True, *args, **kw):
        keys = []
        signals = []

        datastr = self.ask("GetData", verbose=False, quiet=True, use_error_mode=False)
        if datastr:
            if "ERROR" not in datastr:
                data = datastr.split(",")
                if tagged:
                    keys = data[::2]
                    signals = data[1::2]
                else:
                    keys = ["H2", "H1", "AX", "L1", "L2", "CDD"]
                    signals = data

            signals = [float(s) for s in signals]

        return keys, signals, None, True

    def get_intensity(self, dkeys):
        """
        dkeys: str or tuple of strs

        """
        data = self.get_intensities()
        if data is not None:

            keys, signals, _, _ = data

            def func(k):
                return signals[keys.index(k)] if k in keys else 0

            if isinstance(dkeys, (tuple, list)):
                return [func(key) for key in dkeys]
            else:
                return func(dkeys)
                # return signals[keys.index(dkeys)] if dkeys in keys else 0

    def update_config(self, **kw):
        # p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        p = get_spectrometer_config_path()
        config = self.get_configuration_writer(p)
        for k, v in kw.items():
            if not config.has_section(k):
                config.add_section(k)

            for option, value in v:
                config.set(k, option, value)

        with open(p, "w") as wfile:
            config.write(wfile)

        self.clear_cached_config()

    def _get_source_parameter_value(self, k, hardware_name):
        self.debug("get source parameter k={}, hw={}".format(k, hardware_name))
        try:
            ret = getattr(self.source, "read_{}".format(k.lower()))()
        except AttributeError:
            ret = self.get_parameter(hardware_name)
        return ret

    def verify_configuration(self, **kw):
        self.debug("========= Verifying configuration =========")
        readout_comp, defl_comp = self._load_configuration_comparisons()
        mismatch = False
        if self.microcontroller:
            hardware_names = self.hardware_names()
            config = self._get_cached_config()
            if config is not None:
                # specparams, defl, trap, magnet = args
                for k, v in config["deflection"].items():
                    comp = defl_comp.get(k, {})
                    if comp.get("compare", True):
                        current = self.get_deflection(k, current=True)
                        dev = self._get_config_dev(current, v, comp)
                        if dev:
                            self.warning(
                                "verify failed {}. current={}, config={}".format(
                                    k, current, v
                                )
                            )
                            mismatch = True

                for k, v in config["source"].items():
                    try:
                        mk = hardware_names[k]
                    except KeyError:
                        self.debug(
                            "--- Not checking {}. Not in hardware_names".format(k)
                        )
                        self.debug("hardware names: {}".format(hardware_names))

                        continue

                    comp = readout_comp.get(k, {})
                    if comp.get("compare", True):
                        current = self._get_source_parameter_value(k, mk)
                        try:
                            current = float(current)
                        except ValueError:
                            self.warning(
                                "invalid float value {}, {}".format(mk, current)
                            )
                            continue

                        dev = self._get_config_dev(current, v, comp)
                        if dev:
                            self.warning(
                                "verify failed {}. current={}, config={}".format(
                                    mk, current, v
                                )
                            )
                            mismatch = True

                trap = config["trap"]
                for tag in ("voltage", "current"):
                    v = trap.get(tag)
                    if v is not None:
                        comp = readout_comp.get("Trap{}".format(tag.capitalize()), {})
                        if comp.get("compare", True):
                            current = getattr(self.source, "trap_{}".format(tag))
                            dev = self._get_config_dev(current, v, comp)
                            if dev:
                                self.warning(
                                    "verify failed trap {}. current={}, config={}".format(
                                        tag, current, v
                                    )
                                )
                                mismatch = True

        self.debug("========= Verify complete ===========")
        return not mismatch

    # ===============================================================================
    # private
    # ===============================================================================
    def _parse_word(self, word):
        try:
            x = csv_to_floats(word)
        except (AttributeError, ValueError):
            x = []
        return x

    def _get_simulation_data(self):
        signals = [1, 100, 3, 0.01, 0.01, 0.01, 38, 38.5]  # + random(6)
        keys = ["H2", "H1", "AX", "L1", "L2", "CDD", "L2(CDD)", "AX(CDD)"]
        return keys, signals, None

    def _get_config_dev(self, current, v, comp):
        dev = False
        if comp.get("compare", True):

            tol = comp.get("percent_tol")
            if not tol:
                tol = comp.get("tolerance", 0.01)
                delta = abs(current - v)
                dev = delta > tol
                self.debug("abs tolerance={}, delta={}".format(tol, delta))
            else:
                try:
                    delta = abs(current - v) / float(v)
                    dev = delta > tol
                    self.debug("percent tolerance={}, delta={}".format(tol, delta))
                except ZeroDivisionError:
                    self.warning("zero division exception")
                    tol = comp.get("tolerance", 0.01)
                    delta = abs(current - v)
                    dev = delta > tol
                    self.debug("abs tolerance={}, delta={}".format(tol, delta))

        return dev

    def _load_configuration_comparisons(self):
        path = os.path.join(paths.spectrometer_dir, "readout.yaml")
        readouts = {}
        deflections = {}
        yt = yload(path)
        if yt:
            readouts, deflections = yt
            readouts = {r["name"]: r for r in readouts}
            deflections = {r["name"]: r for r in deflections}

        return readouts, deflections

    def _send_configuration(self, use_ramp=True, ramp_confirm=False):
        self.debug("======== Sending configuration ========")

        if self.force_send_configuration:
            readout_comp, defl_comp = {}, {}
        else:
            readout_comp, defl_comp = self._load_configuration_comparisons()

        def not_setting(k, c, v):
            self.debug("Not setting {:<20s} current={}, config={}".format(k, c, v))

        if self.microcontroller:
            hardware_names = self.hardware_names()
            config = self._get_cached_config()
            if config is not None:
                # specparams, defl, trap, magnet = ret
                for k, v in config["deflection"].items():
                    if not self.force_send_configuration:
                        comp = defl_comp.get(k, {})
                        if comp.get("compare", True):
                            current = self.get_deflection(k, current=True)
                            dev = self._get_config_dev(current, v, comp)
                            if not dev:
                                not_setting(k, current, v)
                                continue

                    cmd = "SetDeflection"
                    v = "{},{}".format(k, v)
                    self.set_parameter(cmd, v, post_delay=0.05)

                for k, v in config["source"].items():
                    try:
                        mk = hardware_names[k]
                    except KeyError:
                        self.debug(
                            "--- Not setting {}. Not in hardware_names".format(k)
                        )
                        self.debug("hardware names: {}".format(hardware_names))
                        continue

                    if not self.force_send_configuration:
                        comp = readout_comp.get(k, {})
                        if comp.get("compare", True):

                            current = self._get_source_parameter_value(k, mk)
                            try:
                                current = float(current)
                            except (ValueError, TypeError):
                                self.warning("invalid value {}, {}".format(k, current))
                                continue

                            dev = self._get_config_dev(current, v, comp)
                            if not dev:
                                not_setting(mk, current, v)
                                continue

                    self.set_parameter(mk, v, post_delay=0.05)

                trap = config["trap"]
                for tag, func in (
                    ("voltage", self.source.read_trap_voltage),
                    ("current", self.source.read_trap_current),
                ):
                    # set trap voltage
                    v = trap.get(tag)
                    ttag = "Trap{}".format(tag.capitalize())
                    self.debug("send trap {} {}".format(tag, v))
                    if v is not None:
                        if not self.force_send_configuration:
                            comp = readout_comp.get(ttag, {})
                            if comp.get("compare", True):
                                current = func()
                                try:
                                    current = float(current)
                                    dev = self._get_config_dev(current, v, comp)
                                    if not dev:
                                        not_setting(ttag, current, v)
                                        v = None
                                except (ValueError, TypeError):
                                    self.warning(
                                        "invalid value {}, {}".format(ttag, current)
                                    )
                            else:
                                v = None

                        if v is not None:
                            if tag == "current":
                                step = trap.get("ramp_step", 1)
                                period = trap.get("ramp_period", 1)
                                tol = trap.get("ramp_tolerance", 10)
                                use_ramp = use_ramp and trap.get("use_ramp", True)
                                self._ramp_trap_current(
                                    v, step, period, use_ramp, tol, ramp_confirm
                                )
                            else:
                                setattr(self.source, "trap_{}".format(tag), v)

                # set the mftable
                magnet = config["magnet"]
                mftable_name = magnet.get("mftable")
                if mftable_name:
                    self.debug("updating mftable name {}".format(mftable_name))

                    self.magnet.field_table.path = mftable_name
                    self.magnet.field_table.load_table(load_items=True)

                self.debug("======== Configuration Finished ========")
                self.source.sync_parameters()

    def _ramp_trap_current(
        self, v, step, period, use_ramp=False, tol=10, confirm=False
    ):
        if use_ramp:
            self.debug("ramping trap current")
            current = self.source.read_trap_current()
            if current is None:
                self.debug("could not read current trap. skipping ramp")
                return

            if abs(v - current) >= tol:
                ok = True
                show_progress = False

                if confirm:
                    ok = self.confirmation_dialog(
                        "Would you like to ramp up the "
                        "Trap current from {} to {}".format(current, v)
                    )
                    show_progress = True

                if ok:

                    r = StepRamper()
                    steps = abs(v - current) / step
                    if show_progress:
                        prog = open_progress(int(steps))

                    def func(x):
                        self.source.trap_current = x
                        if show_progress:
                            invoke_in_main_thread(
                                prog.change_message, "Set Trap Current {}".format(x)
                            )
                            if not prog.accepted and not prog.canceled:
                                return True
                        else:
                            return True

                    self.debug(
                        "current={}, target={}, step={}, period={}".format(
                            current, v, step, period
                        )
                    )
                    r.ramp(func, current, v, step, period)
                    if show_progress:
                        prog.close()
                    return True
            else:
                self.debug("trap current is up-to-date")
                return True

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _integration_time_default(self):
        self.default_integration_time = QTEGRA_DEFAULT_INTEGRATION_TIME
        return QTEGRA_DEFAULT_INTEGRATION_TIME

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_sub_cup_configuration(self):
        return self._sub_cup_configuration

    def _set_sub_cup_configuration(self, v):
        self._sub_cup_configuration = v
        self.ask("SetSubCupConfiguration {}".format(v))


# if __name__ == '__main__':
# s = Spectrometer()
# ss = ArgusSource()
# ss.current_hv = 4505
# s.source = ss
# corrected = s.get_hv_correction(100,current=False)
# uncorrected = s.get_hv_correction(corrected, uncorrect=True, current=False)
#
# print corrected, uncorrected

# ============= EOF =============================================
