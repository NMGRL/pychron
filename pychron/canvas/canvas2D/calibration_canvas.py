# ===============================================================================
# Copyright 2011 Jake Ross
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

# ===============================================================================
# Copyright 2013 Jake Ross
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
from enable.abstract_overlay import AbstractOverlay
from kiva import Font
from kiva.fonttools import str_to_font
from traits.api import Any, Event, Enum
import time
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.loading_canvas import LoadingCanvas
from pychron.canvas.canvas2D.scene.loading_scene import LoadingScene
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas


class CalibrationCanvas(LoadingCanvas):
    mode_overlay_enabled = False

    def update_hole(self, hole, unmapped_corrected_position):
        item = self.scene.get_item(hole.id)
        item.corrected_position = unmapped_corrected_position
        self.request_redraw()

# ============= EOF =============================================
