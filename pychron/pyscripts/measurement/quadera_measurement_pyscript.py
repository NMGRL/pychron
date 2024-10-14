# ===============================================================================
# Copyright 2020 ross
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
from pychron.pyscripts.decorators import makeRegistry
from pychron.pyscripts.measurement_pyscript import MeasurementPyScript

command_register = makeRegistry()


class QuaderaMeasurementPyScript(MeasurementPyScript):
    def get_command_register(self):
        cs = super().get_command_register()
        return cs + list(command_register.commands.items())

    @command_register
    def opc_command(self, command, value):
        self._automated_run_call("opc_")

    @command_register
    def measure(self):
        """
        pass control to Quadera.

        poll for measurement completion
        """

        self._automated_run_call("py_controlless_measure")


# ============= EOF =============================================
