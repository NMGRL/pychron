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
from pychron.hardware.core.core_device import CoreDevice


class MCCTemp(CoreDevice):
    def initialize(self):
        self.scan_func = "update_scan"
        return True

    def update_scan(self):
        pass

    def graph_builder(self, g, **kw):
        g.new_plot(padding_left=40, padding_right=5, zoom=True, pan=True, **kw)
        # g.new_plot(padding_left=40, padding_right=5, zoom=True, pan=True, **kw)

        g.new_series()
        # g.new_series(plotid=1)

        g.set_y_title("Temp (C)")
        # g.set_y_title("Heat Power (%)", plotid=1)
# ============= EOF =============================================
