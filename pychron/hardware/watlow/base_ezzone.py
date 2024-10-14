# ===============================================================================
# Copyright 2016 Jake Ross
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

# =============enthought library imports========================
from __future__ import absolute_import
from __future__ import print_function
from traits.api import (
    HasTraits,
    Enum,
    Float,
    Event,
    Property,
    Int,
    Button,
    Bool,
    Str,
    Any,
    on_trait_change,
    String,
)

# =============standard library imports ========================
# =============local library imports  ==========================
import os
import time

from pychron.graph.plot_record import PlotRecord
from pychron.hardware.meter_calibration import MeterCalibration
from pychron.core.helpers.filetools import parse_file
from pychron.hardware.watlow import (
    sensor_map,
    tc_map,
    itc_map,
    isensor_map,
    heat_algorithm_map,
    truefalse_map,
    yesno_map,
    autotune_aggressive_map,
    baudmap,
    ibaudmap,
)
from six.moves import zip


class Protocol:
    def get_register(self, key):
        return self.mapping[key]

    def read(self, *args, **kw):
        pass

    def write(self, *args, **kw):
        pass

    def fromtemp(self, t):
        return t

    def totemp(self, t):
        return t

    def ctof(self, c):
        try:
            return c * 9 / 5.0 + 32
        except (ValueError, TypeError):
            pass

    def ftoc(self, f):
        try:
            return (f - 32) * 5 / 9.0
        except (ValueError, TypeError):
            return


class StandardProtocol(Protocol):
    mapping = {
        "baud_rate": [17002, 17002],
        "csp": 7001,
        "osp": 7002,
        "cm": 8001,
        "hag": 8003,
        "hpb": 8009,
        "cpb": 8012,
        "ti": 8006,
        "td": 8007,
        "db": 8008,
        "sen1": 4005,
        "sen2": 4005,  # sen1 not defined in docs
        "tc1": 4006,
        "tc2": 4006,
        "hhy": 8010,
        "atsp": 8025,
        "tagr": 8024,
        "ttun": 8022,
        "tbnd": 8034,
        "tgn": 8035,
        "aut": 8026,
        "fn": 18002,
        "shi": 18010,
        "slo": 18009,
        "ishi": 4016,
        "islo": 4015,
        "ain1": 4001,
        "ain2": 4001,
        "hpr": 8011,
        "pva1": 8031,
        "pva2": 8031,
        "ica": 4012,
        "ier": 4002,
    }

    def fromtemp(self, t):
        """
        standard protocol temp also in f

        """
        return self.ftoc(t)

    def totemp(self, t):
        return self.ctof(t)


class ModbusProtocol(Protocol):
    mapping = {
        "baud_rate": [2484, 2504],
        "csp": 2160,
        "osp": 2162,
        "cm": 1880,
        "hag": 1884,
        "hpb": 1890,
        "cpb": 1892,
        "ti": 1894,
        "td": 1896,
        "db": 1898,
        "sen1": 368,
        "sen2": 448,
        "tc1": 370,
        "tc2": 450,
        "hhy": 1900,
        "atsp": 1918,
        "tagr": 1916,
        "ttun": 1910,
        "tbnd": 1912,
        "tgn": 1914,
        "aut": 1920,
        "fn": 722,
        "shi": 738,
        "slo": 736,
        "ishi": 390,
        "islo": 388,
        "ain1": 360,
        "ain2": 440,
        "hpr": 1904,
        "pva1": 402,
        "pva2": 402,
        "ica": 382,
        "ier": 362,
    }


class BaseWatlowEZZone(HasTraits):
    """
    WatlowEZZone represents a WatlowEZZone PM PID controller.
    this class provides human readable methods for setting the modbus registers
    """

    Ph = Property(Float(enter_set=True, auto_set=False), depends_on="_Ph_")
    _Ph_ = Float(50)
    Pc = Property(Float(enter_set=True, auto_set=False), depends_on="_Pc_")
    _Pc_ = Float(4)
    I = Property(Float(enter_set=True, auto_set=False), depends_on="_I_")
    _I_ = Float(32)
    D = Property(Float(enter_set=True, auto_set=False), depends_on="_D_")
    _D_ = Float(33)

    dead_band = Property(Float(enter_set=True, auto_set=False), depends_on="_dead_band")
    _dead_band = Float

    stablization_time = Float(3.0)
    sample_time = Float(0.25)
    nsamples = Int(5)
    tune_setpoint = Float(500.0)
    delay = Int(1)

    closed_loop_setpoint = Property(
        Float(0, auto_set=False, enter_set=True), depends_on="_clsetpoint"
    )
    calibrated_setpoint = Float

    _clsetpoint = Float(0.0)
    setpointmin = Float(0.0)
    setpointmax = Float(100.0)

    open_loop_setpoint = Property(
        Float(0, auto_set=False, enter_set=True), depends_on="_olsetpoint"
    )
    _olsetpoint = Float(0.0)
    olsmin = Float(0.0)
    olsmax = Float(100.0)

    max_output = Property(
        Float(enter_set=True, auto_set=False), depends_on="_max_output"
    )
    _max_output = Float(100)

    input_scale_low = Property(
        Float(auto_set=False, enter_set=True), depends_on="_input_scale_low"
    )
    _input_scale_low = Float(0)

    input_scale_high = Property(
        Float(auto_set=False, enter_set=True), depends_on="_input_scale_high"
    )
    _input_scale_high = Float(1)

    output_scale_low = Property(
        Float(auto_set=False, enter_set=True), depends_on="_output_scale_low"
    )
    _output_scale_low = Float(0)

    output_scale_high = Property(
        Float(auto_set=False, enter_set=True), depends_on="_output_scale_high"
    )
    _output_scale_high = Float(1)

    control_mode = Property(depends_on="_control_mode")
    _control_mode = String("closed")

    autotuning_additional_recording = 15
    acount = 0

    autotune_setpoint = Property(
        Float(auto_set=False, enter_set=True), depends_on="_autotune_setpoint"
    )
    _autotune_setpoint = Float(0)

    autotune_aggressiveness = Property(
        Enum("under", "critical", "over"), depends_on="_autotune_aggressiveness"
    )
    _autotune_aggressiveness = Str

    enable_tru_tune = Property(Bool, depends_on="_enable_tru_tune")
    _enable_tru_tune = Bool

    tru_tune_band = Property(
        Int(auto_set=False, enter_set=True), depends_on="_tru_tune_band"
    )
    _tru_tune_band = Int(0)

    tru_tune_gain = Property(
        Enum(("1", "2", "3", "4", "5", "6")), depends_on="_tru_tune_gain"
    )
    _tru_tune_gain = Str

    heat_algorithm = Property(
        Enum("PID", "On-Off", "Off"), depends_on="_heat_algorithm"
    )
    _heat_algorithm = Str

    sensor1_type = Property(
        Enum(
            "off",
            "thermocouple",
            "volts dc",
            "milliamps",
            "rtd 100 ohm",
            "rtd 1000 ohm",
            "potentiometer",
            "thermistor",
        ),
        depends_on="_sensor1_type",
    )

    thermocouple1_type = Property(
        Enum("B", "K", "C", "N", "D", "R", "E", "S", "F", "T", "J"),
        depends_on="_thermocouple1_type",
    )

    _sensor1_type = Int
    _thermocouple1_type = Int

    process_value = Float

    heat_power_value = Float
    # scan_func = 'get_temperature'
    scan_func = "get_temp_and_power"

    memory_blocks_enabled = Bool(True)
    program_memory_blocks = Bool(True)

    _process_working_address = 200
    _process_memory_block = [360, 1904]
    _process_memory_len = 4

    calibration = Any
    use_calibrated_temperature = Bool(False)
    coeff_string = Property

    use_pid_bin = Bool(True)
    default_output = Int(1)
    advanced_values_button = Button
    min_output_scale = Float
    max_output_scale = Float

    use_modbus = Bool(True)

    # def _get_use_calibrated_temperature(self):
    #    return self._use_calibrated_temperature and self.calibration is not None

    # def _set_use_calibrated_temperature(self, v):
    #    self._use_calibrated_temperature = v
    # reciprocal_power=Bool(True)

    def _get_coeff_string(self):
        s = ""
        if self.calibration:
            s = self.calibration.coeff_string
        return s

    def _set_coeff_string(self, v):
        cal = self.calibration
        if cal is None:
            cal = MeterCalibration()
            self.calibration = cal

        cal.coeff_string = v

    @on_trait_change("calibration:coefficients")
    def _coeff_string_changed(self):
        config = self.get_configuration()
        if not config.has_section("Calibration"):
            config.add_section("Calibration")

        config.set("Calibration", "coefficients", self.calibration.dump_coeffs())
        with open(self.config_path, "w") as wfile:
            config.write(wfile)

    def get_setpoint(self):
        return getattr(self, "{}_loop_setpoint".format(self.control_mode))

    def map_temperature(self, te, verbose=True):
        if self.use_calibrated_temperature:
            if self.calibration:
                if verbose:
                    self.info(
                        "using temperature coefficients  (e.g. ax2+bx+c) {}".format(
                            self.calibration.print_string()
                        )
                    )
                if abs(te) < 1e-5:
                    te = 0
                else:
                    te = min(max(0, self.calibration.get_input(te)), self.setpointmax)

            else:
                self.info("no calibration set")

        return te

    def initialize(self, *args, **kw):
        if self.use_modbus:
            self.protocol = ModbusProtocol()
        else:
            self.protocol = StandardProtocol()

        if self.read_baudrate(port=1):
            # set open loop and closed loop to zero
            self.disable()
            if self.program_memory_blocks:
                self._program_memory_blocks()

            # p = self.read_high_power_scale()
            # p=self.read_out
            # if p:
            #     self._max_output = p

            self.initialization_hook()

            self._load_max_output()
            self.setup_consumer()

            # debugging
            of = self.read_output_function()
            self.debug("%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Output function: {}".format(of))

            self.disable()

            return True
        else:
            self.warning("Failed connecting to Temperature Controller")

    def is_programmed(self):
        r = self.get_temp_and_power()
        if r is not None:
            return r.data[0] > 1

    def _load_max_output(self):
        oh = self.output_scale_high
        ol = self.output_scale_low

        mo = self.max_output_scale
        mi = self.min_output_scale
        # print oh, ol, mo, mi
        self._max_output = (oh - ol) / (mo - mi) * 100

    def _program_memory_blocks(self):
        """
        see watlow ez zone pm communications rev b nov 07
        page 5
        User programmable memory blocks
        """
        self._process_memory_len = 0
        self.info("programming memory block")
        for i, ta in enumerate(self._process_memory_block):
            self.set_assembly_definition_address(
                self._process_working_address + 2 * i, ta
            )
            self._process_memory_len += 2

    def report_pid(self):
        self.info("read pid parameters")
        pid_attrs = ["_Ph_", "_Pc_", "_I_", "_D_"]

        if self.use_modbus:
            pid_vals = self.read(1890, nregisters=8, nbytes=21, response_type="float")
        else:
            ph = self.read_heat_proportional_band()
            pc = self.read_cool_proportional_band()
            i = self.read_time_integral()
            d = self.read_time_derivative()
            pid_vals = (ph, pc, i, d)

        if pid_vals:
            self.info("======================== PID =====================")
            for pa, pv in zip(pid_attrs, pid_vals):
                setattr(self, pa, pv)
                self.info("{} set to {}".format(pa, pv))

            ha = self.read_heat_algorithm()
            self.info("heat algorithm: {}".format(ha))

            h = self.read_heat_hystersis()
            self.info("hystersis: {}".format(h))

            hdb = self.read_heat_dead_band()
            self.info("heat dead band: {}".format(hdb))
            self.info("==================================================")

        return pid_vals

    def initialization_hook(self):
        self.info("read input sensor type")
        s = self.read_analog_input_sensor_type(1)
        if s is not None:
            self._sensor1_type = s

        if self._sensor1_type == 95:
            t = self.read_thermocouple_type(1)
            if t is not None:
                self._thermocouple1_type = t

        self.report_pid()

        e = self.read_analog_input_error()
        c = self.read_analog_input_calibration()
        self.debug("analog input error={}".format(e))
        self.debug("analog input cal={}".format(c))

        self.info("read input/output scaling")
        if not self.simulation:
            if isinstance(self.protocol, ModbusProtocol):
                try:
                    osl, osh = self.read(736, nregisters=4, nbytes=13)
                    isl, ish = self.read(388, nregisters=4, nbytes=13)

                    self._output_scale_low = osl
                    self._output_scale_high = osh
                    self._input_scale_low = isl
                    self._input_scale_high = ish
                except TypeError:
                    pass

        attrs = [
            ("read_autotune_setpoint", "_autotune_setpoint"),
            ("read_autotune_aggressiveness", "_autotune_aggressiveness"),
            ("read_tru_tune_enabled", "_enable_tru_tune"),
            ("read_tru_tune_band", "_tru_tune_band"),
            ("read_tru_tune_gain", "_tru_tune_gain"),
            ("read_control_mode", "_control_mode"),
        ]

        if not isinstance(self.protocol, ModbusProtocol):
            attrs += [
                ("read_output_scale_low", "_output_scale_low"),
                ("read_output_scale_high", "_output_scale_high"),
                ("read_input_scale_low", "_input_scale_low"),
                ("read_input_scale_high", "_input_scale_high"),
            ]

        for func, attr in attrs:
            v = getattr(self, func)()
            if v is not None:
                setattr(self, attr, v)

    # ResponseRecorder interface
    def get_output(self, force=False):
        if force:
            self.get_temp_and_power()
        return self.heat_power_value

    def get_response(self, force=False):
        if force:
            self.get_temp_and_power()
        return self.process_value

    def get_temp_and_power(self, verbose=True, **kw):
        #        if 'verbose' in kw and kw['verbose']:
        #            self.info('Read temperature and heat power')

        #        kww = kw.copy()
        #        kww['verbose'] = False
        if self.memory_blocks_enabled:
            args = self.read(
                self._process_working_address,
                nbytes=13,
                nregisters=self._process_memory_len,
                verbose=verbose,
                **kw
            )

            if not args or not isinstance(args, (tuple, list)):
                args = None, None

            t, p = args

        else:
            t = self.read_temperature()
            p = self.read_heat_power()

        if self.simulation:
            #            t = 4 + self.closed_loop_setpoint
            t = self.get_random_value() + self.closed_loop_setpoint
            p = self.get_random_value()

        t = self.process_value if t is None else min(t, 2000)
        p = self.heat_power_value if p is None else max(0, min(p, 100))

        self.trait_set(process_value=t, heat_power_value=p)
        if "verbose" in kw and kw["verbose"]:
            self.info("Temperature= {} Power= {}".format(t, p))

        return PlotRecord([t, p], (0, 1), ("Temp", "Power"))

    def get_temperature(self, **kw):
        if "verbose" in kw and kw["verbose"]:
            self.info("Read temperature")

        t = None
        if self.simulation:
            #            t = 4 + self.closed_loop_setpoint
            t = self.get_random_value() + self.closed_loop_setpoint
        else:
            if self.memory_blocks_enabled:
                args = self.read(
                    self._process_working_address,
                    nbytes=13,
                    nregisters=self._process_memory_len,
                    **kw
                )
                if args:
                    t, _ = args
                    #                if not args or not isinstance(args, (tuple, list)):
                    #                    args = None, None
                    #
                    #                t, _ = args

                    #            t = self.read_process_value(1, **kw)
                    # print t
        if t is not None:
            try:
                t = float(t)
                self.process_value = t
                #                self.process_value_flag = True
                return t
            except (ValueError, TypeError) as e:
                print("watlow gettemperature", e)

    def disable(self):
        self.info("disable")

        func = getattr(self, "set_{}_loop_setpoint".format(self.control_mode))
        func(0)

    #        self.set_control_mode('open')
    #        self.set_open_loop_setpoint(0)

    def load_additional_args(self, config):
        """ """

        self.set_attribute(
            config,
            "use_modbus",
            "Communications",
            "use_modbus",
            cast="boolean",
            default=True,
        )

        self.set_attribute(
            config,
            "use_pid_bin",
            "Output",
            "use_pid_bin",
            cast="boolean",
            default=False,
        )
        self.set_attribute(
            config, "min_output_scale", "Output", "scale_low", cast="float"
        )
        self.set_attribute(
            config, "max_output_scale", "Output", "scale_high", cast="float"
        )

        self.set_attribute(config, "setpointmin", "Setpoint", "min", cast="float")
        self.set_attribute(config, "setpointmax", "Setpoint", "max", cast="float")

        self.set_attribute(
            config, "memory_blocks_enabled", "MemoryBlock", "enabled", cast="boolean"
        )
        self.set_attribute(
            config, "program_memory_blocks", "MemoryBlock", "program", cast="boolean"
        )

        coeffs = self.config_get(config, "Calibration", "coefficients")
        if coeffs:
            self.calibration = MeterCalibration(coeffs)
            # self.use_calibrated_temperature = True
        return True

    def set_nonvolatile_save(self, yesno, **kw):
        v = 106 if yesno else 59
        self.write(2494, v, **kw)

    def read_nonvolative_save(self):
        r = self.read(2494, response_type="int")
        print("nonvolative save", r)

    def set_assembly_definition_address(self, working_address, target_address, **kw):
        ada = working_address - 160

        self.info("setting {} to {}".format(ada, target_address))
        #        self.write(ada, target_address, nregisters=2, **kw)

        self.write(ada, (target_address, target_address + 1), nregisters=2, **kw)
        #        self.info('setting {} to {}'.format(ada, target_address))
        check = False
        if check:
            r = self.read(ada, response_type="int")
            self.info("register {} pointing to {}".format(ada, r))
            r = self.read(ada + 1, response_type="int")
            self.info("register {} pointing to {}".format(ada + 1, r))

    def read_baudrate(self, port=1):
        """
        com port 2 is the modbus port
        """
        # register = 2484 if port == 1 else 2504
        register = self.protocol.get_register("baud_rate")

        r = self.read(register[port - 1], response_type="int")
        if r is not None:
            try:
                return ibaudmap[str(r)]
            except KeyError as e:
                self.debug("read_baudrate keyerror {}".format(e))

    def set_baudrate(self, v, port=1):
        """
        com port 2 is the modbus port
        """
        # register = 2484 if port == 1 else 2504
        register = self.protocol.get_register("baud_rate")
        try:
            value = baudmap[v]
            self.write(register, value)

        except KeyError as e:
            self.debug("set_baudrate keyerror {}".format(e))

    def set_closed_loop_setpoint(self, setpoint, set_pid=True, **kw):
        # if setpoint == 0:
        #     self._output_scale_low = 0
        #     self.set_output_scale_low(0)
        #
        #     self._output_scale_high = 0
        #     self.set_output_scale_high(0)
        #
        # else:
        #     _mi, _ma=self.min_output_scale, self.max_output_scale
        #     self._output_scale_low = _mi
        #     self.set_output_scale_low(_mi)
        #
        #     self._output_scale_high = _ma
        #     self.set_output_scale_high(_ma)

        # self.output_scale_low = self.min_output_scale
        # self.output_scale_high = self.max_output_scale

        self._clsetpoint = setpoint
        if self.use_calibrated_temperature and self.calibration:
            setpoint = self.map_temperature(setpoint)

        if set_pid:
            self.set_pid(setpoint)

        self.calibrated_setpoint = setpoint
        setpoint = self.protocol.totemp(setpoint)
        self.info("setting closed loop setpoint = {:0.3f}".format(setpoint))

        register = self.protocol.get_register("csp")
        self.write(register, setpoint, nregisters=2, **kw)
        #        time.sleep(0.025)
        sp = self.read_closed_loop_setpoint()
        try:
            e = abs(sp - setpoint) > 0.01
        except Exception as _ee:
            e = True

        time.sleep(0.025)
        if sp and e:
            self.warning("Set point not set. {} != {} retrying".format(sp, setpoint))
            self.write(register, setpoint, nregisters=2, **kw)

    def set_open_loop_setpoint(
        self, setpoint, use_calibration=None, verbose=True, set_pid=False, **kw
    ):
        if verbose:
            self.info("setting open loop setpoint = {:0.3f}".format(setpoint))
        self._olsetpoint = setpoint

        register = self.protocol.get_register("osp")
        self.write(register, setpoint, nregisters=2, verbose=verbose, **kw)

    def set_temperature_units(self, comms, units, **kw):
        register = 2490 if comms == 1 else 2510
        value = 15 if units == "C" else 30
        self.write(register, value)

    def set_calibration_offset(self, input_id, value, **kw):
        self.info("set calibration offset {}".format(value))
        register = 382 if input_id == 1 else 462
        self.write(register, value, nregisters=2, **kw)

    def set_control_mode(self, mode, **kw):
        """
        10=closed
        54=open
        """
        if mode == "open":
            self.output_scale_low = self.min_output_scale
            self.output_scale_high = self.max_output_scale
            self._load_max_output()

        self.info("setting control mode = {}".format(mode))
        self._control_mode = mode
        value = 10 if mode == "closed" else 54
        self.write(self.protocol.get_register("cm"), value, **kw)

    # ===============================================================================
    # Autotune
    # ===============================================================================
    def autotune_finished(self, verbose=False, **kw):
        register = self.protocol.get_register("aut")
        r = self.read(register, response_type="int", verbose=verbose, **kw)
        try:
            return not truefalse_map[str(r)]
        except KeyError:
            return True

    def start_autotune(self, **kw):
        self.info("start autotune")
        register = self.protocol.get_register("aut")
        self.write(register, 106, **kw)

    def stop_autotune(self, **kw):
        """ """
        self.info("stop autotune")
        register = self.protocol.get_register("aut")
        self.write(register, 59, **kw)

    def set_autotune_setpoint(self, value, **kw):
        """
        Set the set point that the autotune will use,
        as a percentage of the current set point.
        """
        self.info("setting autotune setpoint {:0.3f}".format(value))
        register = self.protocol.get_register("atsp")
        self.write(register, value, nregisters=2, **kw)

    def set_autotune_aggressiveness(self, key, **kw):
        """
        under damp - reach setpoint quickly
        critical damp - balance a rapid response with minimal overshoot
        over damp - reach setpoint with minimal overshoot
        """
        key = key.lower()
        if key in autotune_aggressive_map:
            value = autotune_aggressive_map[key]

            self.info("setting auto aggressiveness {} ({})".format(key, value))
            register = self.protocol.get_register("tagr")
            self.write(register, value, **kw)

    def set_tru_tune(self, onoff, **kw):
        if onoff:
            msg = "enable TRU-TUNE+"
            value = 106
        else:
            msg = "disable TRU-TUNE+"
            value = 59
        self.info(msg)
        register = self.protocol.get_register("ttun")
        self.write(register, value, **kw)

    def set_tru_tune_band(self, value, **kw):
        """
        0 -100 int

        only adjust this parameter is controller is unable to stabilize.
        only the case for processes with fast responses

        """
        self.info("setting TRU-TUNE+ band {}".format(value))
        register = self.protocol.get_register("tbnd")
        self.write(register, int(value), **kw)

    def set_tru_tune_gain(self, value, **kw):
        """
        1-6 int
        1= most aggressive response and potential for overshoot
        6=least "                                      "
        """
        self.info("setting TRU-TUNE+ gain {}".format(value))
        register = self.protocol.get_register("tgn")
        self.write(register, int(value), **kw)

    # ===============================================================================
    #  PID
    # ===============================================================================
    def set_pid(self, temp):
        """
        get pids from config
        find bin ``temp`` belongs to and get pid
        set temperature controllers pid
        """
        if self.use_pid_bin:
            pid_bin = self._get_pid_bin(temp)
            self.debug("pid bin for {}. {}".format(temp, pid_bin))
            if pid_bin:
                # clear I buffer
                # self.I = 0

                self.trait_set(Ph=pid_bin[0], I=pid_bin[2], D=pid_bin[3])

                self.report_pid()

                if len(pid_bin) == 5:
                    self.max_output = pid_bin[4]
                else:
                    self.max_output = 100

    def set_heat_algorithm(self, value, **kw):
        self.info("setting heat algorithm {}".format(value))
        self.write(self.protocol.get_register("hag"))

    def set_heat_proportional_band(self, value, **kw):
        self.info("setting heat proportional band ={:0.3f}".format(value))
        register = self.protocol.get_register("hpb")
        self.write(register, value, nregisters=2, **kw)

    def set_cool_proportional_band(self, value, **kw):
        self.info("setting cool proportional band = {:0.3f}".format(value))
        register = self.protocol.get_register("hpb")
        self.write(register, value, nregisters=2, **kw)

    def set_time_integral(self, value, **kw):
        self.info("setting time integral = {:0.3f}".format(value))
        register = self.protocol.get_register("ti")
        self.write(register, value, nregisters=2, **kw)

    def set_time_derivative(self, value, **kw):
        self.info("setting time derivative = {:0.3f}".format(value))
        register = self.protocol.get_register("td")
        self.write(register, value, nregisters=2, **kw)

    def set_dead_band(self, v, **kw):
        """
        Set the offset to the proportional band. With
        a negative value, both heating and cooling outputs are active
        when the process value is near the set point.
        A positive value keeps heating and cooling outputs from fighting each other.
        """
        self.info("setting dead_band = {:0.3f}".format(v))
        register = self.protocol.get_register("db")
        self.write(register, v, nregisters=2, **kw)

    # ===============================================================================
    # Output
    # ===============================================================================
    def set_output_function(self, value, **kw):
        inmap = {"heat": 36, "off": 62}
        if value in inmap:
            self.info("set output function {}".format(value))
            value = inmap[value]
            self.write(722, value, **kw)

    def set_input_scale_low(self, value, **kw):
        self.info("set input scale low {}".format(value))
        register = self.protocol.get_register("islo")
        self.write(register, value, nregisters=2, **kw)

    def set_input_scale_high(self, value, **kw):
        self.info("set input scale high {}".format(value))
        register = self.protocol.get_register("ishi")
        self.write(register, value, nregisters=2, **kw)

    def set_output_scale_low(self, value, **kw):
        self.info("set output scale low {}".format(value))
        register = self.protocol.get_register("slo")
        self.write(register, value, nregisters=2, **kw)

    def set_output_scale_high(self, value, **kw):
        self.info("set output scale high {}".format(value))
        register = self.protocol.get_register("shi")
        self.write(register, value, nregisters=2, **kw)

    def set_analog_input_sensor_type(self, input_id, value, **kw):
        self.info("set input sensor type {}".format(value))
        register = self.protocol.get_register("sen{}".format(input_id))
        v = value if isinstance(value, int) else isensor_map[value]
        self.write(register, v, **kw)
        if v == 95:
            tc = self.read_thermocouple_type(1)
            self._thermocouple1_type = tc

    def set_thermocouple_type(self, input_id, value, **kw):
        """ """
        self.info("set input thermocouple type {}".format(value))
        register = 370 if input_id == 1 else 450
        v = value if isinstance(value, int) else itc_map[value.upper()]

        self.write(register, v, **kw)

    def set_high_power_scale(self, value, output=None, **kw):
        if output is None:
            output = self.default_output

        self.info("set high power scale {}".format(value))
        # register = 898 if output == 1 else 928
        register = 746 if output == 1 else 866
        # register= 898 if output ==1 else 898
        v = max(0, min(100, value))
        self.write(register, v, nregisters=2, **kw)

    # ===============================================================================
    # readers
    # ===============================================================================
    def read_heat_dead_band(self, **kw):
        register = self.protocol.get_register("db")
        return self.read(register, nregisters=2, nbytes=9, **kw)

    def read_heat_hystersis(self, **kw):
        register = self.protocol.get_register("hhy")
        return self.read(register, nregisters=2, nbytes=9, **kw)

    def read_output_state(self, **kw):
        rid = str(self.read(1012, response_type="int", **kw))
        units_map = {"63": "On", "62": "Off"}
        return units_map[rid] if rid in units_map else None

    def read_heat_proportional_band(self, **kw):
        register = self.protocol.get_register("hpb")
        return self.read(register, nregisters=2, **kw)

    def read_cool_proportional_band(self, **kw):
        register = self.protocol.get_register("cpb")
        return self.read(register, nregisters=2, **kw)

    def read_time_integral(self, **kw):
        register = self.protocol.get_register("ti")
        return self.read(register, nregisters=2, **kw)

    def read_time_derivative(self, **kw):
        register = self.protocol.get_register("td")
        return self.read(register, nregisters=2, **kw)

    def read_calibration_offset(self, input_id, **kw):
        register = 382 if input_id == 1 else 462

        return self.read(register, nregisters=2, **kw)

    def read_closed_loop_setpoint(self, **kw):
        self.debug("read closed loop setpoint")
        register = self.protocol.get_register("csp")
        return self.read(register, nregisters=2, nbytes=9, **kw)

    def read_open_loop_setpoint(self, **kw):
        self.debug("read open loop setpoint")
        register = self.protocol.get_register("osp")
        return self.read(register, nregisters=2, **kw)

    def read_analog_input_error(self, **kw):
        register = self.protocol.get_register("ier")
        return self.read(register, nregisters=2, **kw)

    def read_analog_input_calibration(self, **kw):
        register = self.protocol.get_register("ica")
        return self.read(register, nregisters=2, **kw)

    def read_analog_input_sensor_type(self, input_id, **kw):
        register = self.protocol.get_register("sen{}".format(input_id))
        return self.read(register, response_type="int", **kw)

    def read_thermocouple_type(self, input_id, **kw):
        register = self.protocol.get_register("tc{}".format(input_id))
        rid = self.read(register, response_type="int", **kw)
        return rid

    def read_filtered_process_value(self, input_id, **kw):
        register = self.protocol.get_register("pva{}".format(input_id))
        return self.read(register, nregisters=2, **kw)

    def read_process_value(self, input_id, **kw):
        """
        unfiltered process value
        """
        register = self.protocol.get_register("ain{}".format(input_id))
        return self.read(register, nregisters=2, **kw)

    def read_error_status(self, input_id, **kw):
        register = 362 if input_id == 1 else 442
        return self.read(register, response_type="int", **kw)

    def read_temperature_units(self, comms):
        register = 2490 if comms == 1 else 2510
        rid = str(self.read(register, response_type="int"))
        units_map = {"15": "C", "30": "F"}
        return units_map[rid] if rid in units_map else None

    def read_control_mode(self, **kw):
        register = self.protocol.get_register("cm")
        rid = self.read(register, response_type="int", **kw)
        return "closed" if rid == 10 else "open"

    def read_heat_algorithm(self, **kw):
        register = self.protocol.get_register("hag")
        rid = str(self.read(register, response_type="int", **kw))
        return heat_algorithm_map[rid] if rid in heat_algorithm_map else None

    def read_open_loop_detect_enable(self, **kw):
        rid = str(self.read(1922, response_type="int"))
        return yesno_map[id] if rid in yesno_map else None

    def read_output_scale_low(self, **kw):
        register = self.protocol.get_register("slo")
        return self.read(register, nregisters=2, **kw)

    def read_output_scale_high(self, **kw):
        register = self.protocol.get_register("shi")
        return self.read(register, nregisters=2, **kw)

    def read_input_scale_low(self, **kw):
        register = self.protocol.get_register("islo")
        return self.read(register, nregisters=2, **kw)

    def read_input_scale_high(self, **kw):
        register = self.protocol.get_register("ishi")
        return self.read(register, nregisters=2, **kw)

    def read_output_type(self, **kw):
        r_map = {"104": "volts", "112": "milliamps"}
        rid = str(self.read(720, response_type="int", **kw))
        return r_map[rid] if rid in r_map else None

    def read_output_function(self, **kw):
        register = self.protocol.get_register("fn")
        rid = str(self.read(register, response_type="int", **kw))
        r_map = {"36": "heat", "62": "off"}

        return r_map[rid] if rid in r_map else None

    def read_temperature(self):
        t = self.read_process_value(1)
        return self.protocol.fromtemp(t)

    def read_heat_power(self, **kw):
        register = self.protocol.get_register("hpr")
        return self.read(register, nregisters=2, **kw)

    def read_autotune_setpoint(self, **kw):
        self.debug("read autotune setpoint")
        register = self.protocol.get_register("atsp")
        r = self.read(register, nregisters=2, nbytes=9, **kw)
        return r

    def read_autotune_aggressiveness(self, **kw):
        register = self.protocol.get_register("tagr")
        rid = str(self.read(register, response_type="int", **kw))
        return heat_algorithm_map[rid] if rid in heat_algorithm_map else None

    def read_tru_tune_enabled(self, **kw):
        register = self.protocol.get_register("ttun")
        r = self.read(register, response_type="int", **kw)
        r = str(r)

        try:
            return truefalse_map[r]
        except KeyError:
            pass

    def read_tru_tune_band(self, **kw):
        register = self.protocol.get_register("tbnd")
        return self.read(register, response_type="int", **kw)

    def read_tru_tune_gain(self, **kw):
        register = self.protocol.get_register("tgn")
        try:
            return str(self.read(register, response_type="int", **kw))
        except ValueError:
            pass

    def read_high_power_scale(self, output=None, **kw):
        if output is None:
            output = self.default_output
        self.info("read high power scale {}".format(output))
        register = 746 if output == 1 else 866
        # register = 898 if output == 1 else 898
        # register = 898 if output == 1 else 928
        # r = self.read(register, nregisters=2, nbytes=9, **kw)
        r = self.read(register, nregisters=2, nbytes=9, **kw)
        if self.reciprocal_power:
            r = 100 - r

        return r

    #    def read_cool_power(self,**kw):
    #        register=1906
    #        return self.read(register,**kw)
    #    def _scan_(self, *args, **kw):
    #        """
    #
    #        """
    #        p = self.get_temperature()
    #        record_id = self.name
    #        self.stream_manager.record(p, record_id)
    # ===============================================================================
    # setters
    # ===============================================================================
    def _set_sensor1_type(self, v):
        self._sensor1_type = isensor_map[v]
        self.set_analog_input_sensor_type(1, self._sensor1_type)

    def _set_thermocouple1_type(self, v):
        self._thermocouple1_type = itc_map[v]
        self.set_thermocouple_type(1, self._thermocouple1_type)

    def _set_closed_loop_setpoint(self, v):
        #         self.set_closed_loop_setpoint(v)
        self.add_consumable((self.set_closed_loop_setpoint, v))

    def _set_open_loop_setpoint(self, v):
        self.add_consumable((self.set_open_loop_setpoint, v))

    #         self.set_open_loop_setpoint(v)

    def _set_control_mode(self, mode):
        self.set_control_mode(mode)

    # def _validate_Pc(self, v):
    #     if self._validate_number(v):
    #         return self._validate_new(v, self._Pc_)
    #
    # def _validate_Ph(self, v):
    #     if self._validate_number(v):
    #         return self._validate_new(v, self._Ph_)
    #
    # def _validate_I(self, v):
    #     if self._validate_number(v):
    #         return self._validate_new(v, self._I_)
    #
    # def _validate_D(self, v):
    #     if self._validate_number(v):
    #         return self._validate_new(v, self._D_)

    def _set_Ph(self, v):
        if v is not None:
            self._Ph_ = v
            self.set_heat_proportional_band(v)

    def _set_Pc(self, v):
        if v is not None:
            self._Pc_ = v
            self.set_cool_proportional_band(v)

    def _set_I(self, v):
        if v is not None:
            self._I_ = v
            self.set_time_integral(v)

    def _set_D(self, v):
        if v is not None:
            self._D_ = v
            self.set_time_derivative(v)

    def _set_calibration_offset(self, v):
        self._calibration_offset = v
        self.set_calibration_offset(1, v)

    def _set_input_scale_low(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._input_scale_low):
                self._input_scale_low = v
                self.set_input_scale_low(v)

    def _set_input_scale_high(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._input_scale_high):
                self._input_scale_high = v
                self.set_input_scale_high(v)

    def _set_output_scale_low(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._output_scale_low):
                self._output_scale_low = v
                self.set_output_scale_low(v)

    def _set_output_scale_high(self, v):
        """ """
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._output_scale_high):
                self._output_scale_high = v
                self.set_output_scale_high(v)

    def _set_enable_tru_tune(self, v):
        self._enable_tru_tune = v
        self.set_tru_tune(v)

    def _set_tru_tune_band(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._tru_tune_band):
                self._tru_tune_band = v
                self.set_tru_tune_band(v)

    def _set_tru_tune_gain(self, v):
        self._tru_tune_gain = v
        self.set_tru_tune_gain(v)

    def _set_autotune_setpoint(self, v):
        if self._validate_number(v) is not None:
            if self._validate_new(v, self._autotune_setpoint):
                self._autotune_setpoint = v
                self.set_autotune_setpoint(v)

    def _set_autotune_aggressiveness(self, v):
        self._autotune_aggressiveness = v
        self.set_autotune_aggressiveness(v)

    def _set_heat_algorithm(self, v):
        self._heat_algorithm = v
        self.set_heat_algorithm(v)

    def _set_dead_band(self, v):
        self._dead_band = v
        self.set_dead_band(v)

    def _set_max_output(self, v):
        if v > 0:
            self.output_scale_low = self.min_output_scale

        v = (
            self.max_output_scale - self.min_output_scale
        ) * v / 100.0 + self.output_scale_low
        self.output_scale_high = v
        # self.set_output_scale_high(v)
        self._load_max_output()

    def _validate_max_output(self, v):
        return self._validate_number(v)

    def _validate_number(self, v):
        try:
            return float(v)
        except ValueError:
            pass

    def _validate_new(self, new, old, tol=0.001):
        if abs(new - old) > tol:
            return new

    # ===============================================================================
    # getters
    # ===============================================================================
    def _get_pid_bin(self, temp):
        """
        load pid_bins from file
        """
        if not self.configuration_dir_path:
            self.debug(
                "no configuration_dir_path. this device was not initialized. check initialization.xml"
            )
            return

        p = os.path.join(self.configuration_dir_path, "pid.csv")
        if not os.path.isfile(p):
            self.warning(
                "No pid.csv file in configuration dir. {}".format(
                    self.configuration_dir_path
                )
            )
            return

        lines = parse_file(p, delimiter=",", cast=float)
        for i, li in enumerate(lines):
            if li[0] > temp:
                i = max(0, i - 1)

                return lines[i][1:]
        else:
            t = lines[-1][0]
            self.warning(
                "could not find appropriate bin for in pid file. using pid for {} bin. temp={}".format(
                    t, temp
                )
            )
            return lines[-1][1:]

    def _get_autotune_label(self):
        return "Autotune" if not self.autotuning else "Stop"

    def _get_heat_algorithm(self):
        return self._heat_algorithm

    def _get_autotune_aggressiveness(self):
        return self._autotune_aggressiveness

    def _get_autotune_setpoint(self):
        return self._autotune_setpoint

    def _get_tru_tune_gain(self):
        return self._tru_tune_gain

    def _get_tru_tune_band(self):
        return self._tru_tune_band

    def _get_enable_tru_tune(self):
        return self._enable_tru_tune

    def _get_output_scale_high(self):
        return self._output_scale_high

    def _get_output_scale_low(self):
        return self._output_scale_low

    def _get_input_scale_high(self):
        return self._input_scale_high

    def _get_input_scale_low(self):
        return self._input_scale_low

    def _get_calibration_offset(self):
        return self._calibration_offset

    def _get_D(self):
        return self._D_

    def _get_I(self):
        return self._I_

    def _get_Pc(self):
        return self._Pc_

    def _get_Ph(self):
        return self._Ph_

    def _get_dead_band(self):
        return self._dead_band

    def _get_control_mode(self):
        return self._control_mode

    def _get_open_loop_setpoint(self):
        return self._olsetpoint

    def _get_closed_loop_setpoint(self):
        return self._clsetpoint

    def _get_thermocouple1_type(self):
        try:
            return tc_map[str(self._thermocouple1_type)]
        except KeyError:
            pass

    def _get_sensor1_type(self):
        try:
            return sensor_map[str(self._sensor1_type)]
        except KeyError:
            pass

    def _get_max_output(self):
        return self._max_output
