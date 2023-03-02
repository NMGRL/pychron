# ===============================================================================
# Copyright 2023 ross
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
import time

from pychron.core.yaml import yload
from pychron.hardware.actuators.gp_actuator import GPActuator
from pychron.paths import paths


class U2351A(GPActuator):
    """

    valve_actuation_config.yaml example

    A:
      open:
        curve:
        nsteps: 1000
        step_delay: 1
      close:
        curve:
        nsteps: 1
        step_delay: 0
    B:
      open:
        curve:
        nsteps: 1000
        step_delay: 1
      close:
        curve:
        nsteps: 1
        step_delay: 0
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._actuation_config_path = os.path.join(
            paths.device_dir, "valve_actuation_config.yaml"
        )

    def _actuate(self, obj, action):
        addr = obj.address
        state = action.lower() == "open"
        print("actuate. write digital out {} {}".format(addr, state))

        stepobj = self._get_actuation_steps(state)
        if stepobj:
            n = stepobj["nsteps"]
            step_delay = stepobj["step_delay"]
            steps = self._generate_voltage_steps(stepobj)

            self.debug(f"ramping voltage nsteps={n}, step_delay={step_delay}")
            for i, step in enumerate(steps):
                self.debug(f"step {i + 1}/{n} {step}")
                # self.communicator.a_out(addr, step)
                self.ask(f"SOUR:VOLT {step}, (@{addr})")
                time.sleep(step_delay)
        else:
            self.ask(f"SOUR:VOLT 5,(@{addr})")
        return True

    def _generate_voltage_steps(self, obj):
        return [1, 2, 3, 4, 5]

    def _get_actuation_config(self, name):
        if os.path.isfile(self._actuation_config_path):
            with open(self._actuation_config_path, "r") as wfile:
                obj = yload(wfile)
                return obj.get(name)


# ============= EOF =============================================
