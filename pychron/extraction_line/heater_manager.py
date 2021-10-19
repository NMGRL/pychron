# ===============================================================================
# Copyright 2021 ross
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
from threading import Thread
from traits.api import List, Float, Event, Bool, Property
from traitsui.api import View, Item, UItem, ButtonEditor, InstanceEditor, ListEditor

from pychron.managers.manager import Manager


class HeaterManager(Manager):
    period = Float(5)
    is_alive = Bool

    def finish_loading(self, *args, **kw):
        super().finish_loading(*args, **kw)
        for di in self.devices:
            di.load_from_device()

    def start_scans(self):
        self._thread = Thread(target=self._scan)
        self._thread.start()

    def _scan(self):
        self.is_alive = True
        if self.devices:
            while self.is_alive:
                for h in self.devices:
                    h.update()
                time.sleep(self.period)

    def stop_scans(self):
        self.is_alive = False

    def traits_view(self):
        v = View(
            Item(
                "devices",
                style="custom",
                show_label=False,
                editor=ListEditor(
                    mutable=False,
                    style="custom",
                    editor=InstanceEditor(view="heater_view"),
                ),
            ),
        )

        return v


# ============= EOF =============================================
