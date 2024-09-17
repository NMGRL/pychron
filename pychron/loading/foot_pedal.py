# ===============================================================================
# Copyright 2022 ross
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
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.loggable import Loggable
from traits.api import Int
from traitsui.api import UItem, Item


class FootPedal(Loggable):
    max_count = Int
    count = Int(0)
    active_idx = Int

    def traits_view(self):
        return okcancel_view(
            Item("active_idx", label="Starting Hole"), title="Set Starting hole"
        )

    def increment(self):
        self.active_idx += 1
        self.count += 1
        if self.max_count:
            if self.count >= self.max_count:
                self.count = 0
                return True


# ============= EOF =============================================
