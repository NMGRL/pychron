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
from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

HW_PACKAGE_MAP = {
    'CommandProcessor': 'pychron.messaging.command_processor',
    'RemoteCommandServer': 'pychron.messaging.remote_command_server',

    'DPi32TemperatureMonitor': 'pychron.hardware.temperature_monitor',
    'SwitchController': 'pychron.hardware.actuators.switch_controller',
    'AnalogPowerMeter': 'pychron.hardware.analog_power_meter',
    'ADC': 'pychron.hardware.adc.adc_device',
    'AgilentADC': 'pychron.hardware.adc.analog_digital_converter',
    'Eurotherm': 'pychron.hardware.eurotherm',
    'ThermoRack': 'pychron.hardware.thermorack',
    'MicroIonController': 'pychron.hardware.gauges.granville_phillips.micro_ion_controller',
    'PychronMicroIonController': 'pychron.hardware.gauges.granville_phillips.pychron_micro_ion_controller',
    'QtegraMicroIonController': 'pychron.hardware.gauges.granville_phillips.pychron_micro_ion_controller',
    'ArgusController': 'pychron.hardware.argus_controller',
    'FerrupsUPS': 'pychron.hardware.FerrupsUPS',
    'QtegraDevice': 'pychron.hardware.qtegra_device',
    'PidController': 'pychron.hardware.pid_controller',
    'PychronLaser': 'pychron.hardware.pychron_laser',
    'AgilentMultiplexer': 'pychron.hardware.agilent.agilent_multiplexer',
    'Transducer': 'pychron.hardware.transducer',
    'ApisController': 'pychron.hardware.apis_controller',

    'Pneumatics': 'pychron.hardware.pneumatics',
    'PychronPneumatics': 'pychron.hardware.pneumatics',
    'PychronChiller': 'pychron.hardware.pychron_chiller',

    # 'RemoteThermoRack': 'pychron.hardware.remote.thermorack',
    'RemoteNewportMotionController': 'pychron.hardware.remote.newport_motion_controller',

    'TempHumMicroServer': 'pychron.hardware.environmental_probe',
    'AirTransducer': 'pychron.hardware.transducer',
    'NMGRLMagnetDumper': 'pychron.furnace.magnet_dumper'
    # 'ControlModule': 'pychron.hardware.fusions.vue_diode_control_module'
}


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
