# ===============================================================================
# Copyright 2023 Jake Ross
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
import time

from pychron.hardware.core.core_device import CoreDevice


class LasconController(CoreDevice):
    def initialize(self, *args, **kw):
        self.communicator.write_terminator = "\r\n"
        self.communicator.read_terminator = "\r\n"
        return True

    def load_and_execute_script(self, script_number, block=True):
        self.ask(f"PScriptLoad {script_number}")
        self.ask(f"PScriptSet {script_number}")

        if block:
            if isinstance(block, bool):
                block = 5

            while 1:
                resp = self.ask("PScriptGet")
                if resp == "0":
                    break
                time.sleep(block)


# ============= EOF =============================================
