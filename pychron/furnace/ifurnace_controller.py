# ===============================================================================
# Copyright 2016 Jake Ross
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

from traits.api import Interface


# ============= standard library imports ========================
# ============= local library imports  ==========================


class IFurnaceController(Interface):
    def read_setpoint(self):
        pass

    def set_setpoint(self, v):
        pass

    def test_connection(self):
        pass

    def get_process_value(self):
        pass

    def get_output(self):
        pass

    def set_pid(self, param_str):
        pass

    # def read_temperature(self, force=False, verbose=False):
    #     pass
    #
    # def read_output_percent(self, force=False, verbose=False):
    #     pass
# ============= EOF =============================================
