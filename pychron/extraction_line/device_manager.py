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
from threading import Thread
import time
from pychron.managers.manager import Manager
from traits.api import Float, Bool
from traitsui.api import View, UItem, Item, ListEditor, InstanceEditor


class DeviceManager(Manager):
    period = Float(5)
    is_alive = Bool
    device_view_name = "device_view"
    update_enabled = Bool

    _thread = None

    def finish_loading(self, *args, **kw):
        super().finish_loading(*args, **kw)
        for di in self.devices:
            di.load_from_device()

    def start_scans(self):
        if self.update_enabled:
            self._thread = Thread(target=self._scan)
            self._thread.start()
        else:
            self.warning(
                "Not starting device updates. Updates disabled. enable in Preferences/ExtractionLine"
            )

    def _scan(self):
        self.is_alive = True
        if self.devices:
            while self.is_alive:
                for h in self.devices:
                    if h.is_scanable and h.should_update():
                        if hasattr(h, "scan_func"):
                            func = h.scan_func
                        else:
                            func = "update"
                        if isinstance(func, str):
                            func = getattr(h, func)
                        with h.lock_scan():
                            func()
                time.sleep(self.period)

    def stop_scans(self):
        self.is_alive = False

    def traits_view(self):
        if self.devices:
            v = View(
                Item(
                    "devices",
                    style="custom",
                    show_label=False,
                    editor=ListEditor(
                        mutable=False,
                        style="custom",
                        editor=InstanceEditor(view=self.device_view_name),
                    ),
                ),
            )
        else:
            v = View()

        return v


# ============= EOF =============================================
