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
import re

from pychron.pyscripts.decorators import (
    verbose_skip,
    makeRegistry,
    calculate_duration,
    device_verbose_skip,
)

from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript

COMPRE = re.compile(r"[A-Za-z]*")

# make a registry to hold all the commands exposed by ExtractionPyScript
# used when building the context
# see PyScript.get_context and get_command_register
command_register = makeRegistry()


class PostMeasurementPyScript(ExtractionPyScript):

    def get_command_register(self):
        cm = super(ExtractionPyScript, self).get_command_register()
        return list(command_register.commands.items()) + cm

    @verbose_skip
    @command_register
    def get_intensity(self, name):
        v = self._automated_run_call("py_get_intensity", detector=name)

        # ensure the script always gets a number
        return 0 or v


# ============= EOF ====================================
