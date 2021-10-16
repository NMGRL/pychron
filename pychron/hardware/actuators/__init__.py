# ===============================================================================
# Copyright 2011 Jake Ross
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
from pychron.globals import globalv


def get_switch_address(obj):
    if isinstance(obj, (str, int)):
        addr = obj
    else:
        addr = obj.address
    return addr


def get_valve_name(obj):
    if isinstance(obj, (str, int)):
        name = obj
    else:
        name = obj.name.split("-")[1]
    return name


def sim(func):
    def wrapper(*args, **kw):
        r = func(*args, **kw)
        if r is None and globalv.communication_simulation:
            r = True
        return r

    return wrapper


def word(func):
    def wrapper(*args, **kw):
        r = func(*args, **kw)
        d = {}
        if not isinstance(r, bool):
            args = r.split(",")
            d = {args[i]: args[i + 1] for i in range(0, len(args), 2)}

        return d

    return wrapper


def trim_affirmative(func):
    def wrapper(obj, *args, **kw):
        r = func(obj, *args, **kw)
        if r is None and globalv.communication_simulation:
            r = True
        else:
            cmd = None
            if isinstance(r, tuple):
                r, cmd = r

            r = r.strip()
            if callable(obj.affirmative):
                r = obj.affirmative(r, cmd)
            else:
                r = r == obj.affirmative

        return r

    return wrapper


base = "pychron.hardware"
abase = "{}.actuators".format(base)

PACKAGES = dict(
    AgilentGPActuator="{}.agilent.agilent_gp_actuator".format(base),
    AgilentMultifunction="{}.agilent.agilent_multifunction".format(base),
    ArduinoGPActuator="{}.arduino.arduino_gp_actuator".format(base),
    QtegraGPActuator="{}.qtegra_gp_actuator".format(abase),
    PychronGPActuator="{}.pychron_gp_actuator".format(abase),
    NGXGPActuator="{}.ngx_gp_actuator".format(abase),
    WiscArGPActuator="{}.wiscar_actuator".format(abase),
    NMGRLFurnaceActuator="{}.nmgrl_furnace_actuator".format(abase),
    DummyGPActuator="{}.dummy_gp_actuator".format(abase),
    RPiGPIO="{}.rpi_gpio".format(base),
    T4Actuator="{}.t4_actuator".format(abase),
)
