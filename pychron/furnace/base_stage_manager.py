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
from pychron.paths import paths
from pychron.stage.maps.furnace_map import FurnaceStageMap
from pychron.stage.stage_manager import BaseStageManager


class BaseFurnaceStageManager(BaseStageManager):
    stage_map_klass = FurnaceStageMap

    def __init__(self, *args, **kw):
        super(BaseFurnaceStageManager, self).__init__(*args, **kw)
        self.tray_calibration_manager.style = 'Linear'

    def get_sample_states(self):
        return [h.id for h in self.stage_map.sample_holes if h.analyzed]

    def _root_default(self):
        return paths.furnace_map_dir
# ============= EOF =============================================
