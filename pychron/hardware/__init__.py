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
# from pint import UnitRegistry
#
# ureg = UnitRegistry()
# Q_ = ureg.Quantity
from pychron.core.helpers.binpack import format_blob


def hardware_pkg(k):
    return "pychron.hardware.{}".format(k)


def gauge_pkg(k):
    return hardware_pkg("gauges.{}".format(k))


HW_PACKAGE_MAP = {
    "CommandProcessor": "pychron.messaging.command_processor",
    "RemoteCommandServer": "pychron.messaging.remote_command_server",
    "DPi32TemperatureMonitor": hardware_pkg("temperature_monitor"),
    "SwitchController": hardware_pkg("actuators.switch_controller"),
    "DummyController": hardware_pkg("actuators.dummy_controller"),
    "AnalogPowerMeter": hardware_pkg("analog_power_meter"),
    "ADC": hardware_pkg("adc.adc_device"),
    "AgilentADC": hardware_pkg("adc.analog_digital_converter"),
    "Eurotherm": hardware_pkg("eurotherm.eurotherm"),
    "ThermoRack": hardware_pkg("thermorack"),
    "MicroIonController": gauge_pkg("granville_phillips.micro_ion_controller"),
    "PychronMicroIonController": gauge_pkg(
        "granville_phillips.pychron_micro_ion_controller"
    ),
    # QtegraMicroIonController is deprecated use QtegraGaugeController instead
    "QtegraMicroIonController": gauge_pkg(
        "granville_phillips.pychron_micro_ion_controller"
    ),
    "QtegraGaugeController": gauge_pkg("qtegra.qtegra_gauge_controller"),
    "MKSController": gauge_pkg("mks.controller"),
    "PfeifferMaxiGaugeController": gauge_pkg("pfeiffer.maxi_gauge_controller"),
    "XGS600GaugeController": gauge_pkg("varian.varian_gauge_controller"),
    "ArgusController": hardware_pkg("thermo_spectrometer_controller"),
    "HelixController": hardware_pkg("thermo_spectrometer_controller"),
    "FerrupsUPS": hardware_pkg("FerrupsUPS"),
    "QtegraDevice": hardware_pkg("qtegra_device"),
    "PidController": hardware_pkg("pid_controller"),
    "PychronLaser": hardware_pkg("pychron_laser"),
    "AgilentMultiplexer": hardware_pkg("agilent.agilent_multiplexer"),
    "Transducer": hardware_pkg("transducer"),
    "ApisController": hardware_pkg("apis_controller"),
    "Pneumatics": hardware_pkg("pneumatics"),
    "PychronPneumatics": hardware_pkg("pneumatics"),
    "PychronChiller": hardware_pkg("pychron_chiller"),
    # "RemoteNewportMotionController": hardware_pkg("remote.newport_motion_controller"),
    "TempHumMicroServer": hardware_pkg("environmental_probe"),
    "AirTransducer": hardware_pkg("transducer"),
    "NMGRLMagnetDumper": "pychron.furnace.magnet_dumper",
    "LamontFurnaceControl": hardware_pkg("labjack.ldeo_furnace"),
    "Model330TemperatureController": hardware_pkg("lakeshore.model330"),
    "Model335TemperatureController": hardware_pkg("lakeshore.model335"),
    "Model336TemperatureController": hardware_pkg("lakeshore.model336"),
    "MKSSRG": gauge_pkg("mks.srg"),
    "GenericDevice": hardware_pkg("generic_device"),
    "PLC2000Heater": hardware_pkg("heater"),
    "PLC2000GaugeController": gauge_pkg("plc2000.plc2000_gauge_controller"),
    "T4Actuator": hardware_pkg("actuators.t4_actuator"),
    "U3Actuator": hardware_pkg("actuators.u3_actuator"),
    "ProXRActuator": hardware_pkg("actuators.proxr_actuator"),
    "U3GaugeController": hardware_pkg("labjack.u3_gauge_controller"),
    "SPCIonPumpController": hardware_pkg("ionpump.spc_ion_pump_controller"),
    "HiPace": hardware_pkg("turbo.hipace"),
    "ADCGaugeController": gauge_pkg("adc_gauge_controller"),
    "WatlowEZZone": hardware_pkg("watlow.watlow_ezzone"),
}


def get_int(default=None):
    def dec(func):
        def wrapper(*args, **kw):
            t = func(*args, **kw)
            try:
                return int(t)
            except (TypeError, ValueError):
                return default

        return wrapper

    return dec


def get_float(default=None):
    def dec(func):
        def wrapper(*args, **kw):
            t = func(*args, **kw)
            try:
                return float(t)
            except (TypeError, ValueError):
                return default

        return wrapper

    return dec


def get_boolean(default=False):
    def dec(func):
        def wrapper(*args, **kw):
            t = func(*args, **kw)
            try:
                return bool(t)
            except (TypeError, ValueError):
                return default

        return wrapper

    return dec


def get_blob(default=b""):
    def dec(func):
        def wrapper(*args, **kw):
            t = func(*args, **kw)
            if t:
                try:
                    return format_blob(t)
                except BaseException:
                    return default
            else:
                return default

        return wrapper

    return dec
