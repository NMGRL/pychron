# ===============================================================================
# Copyright 2018 ross
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
from __future__ import absolute_import
from pychron.spectrometer.tasks.spectrometer_task import SpectrometerTask

import time


class IsotopxSpectrometerTask(SpectrometerTask):
    def _peak_center_start_hook(self):
        self.scan_manager.stop_scan()
        time.sleep(self.scan_manager.update_period)

    def _peak_center_stop_hook(self):
        self.scan_manager.setup_scan()

# ============= EOF =============================================
