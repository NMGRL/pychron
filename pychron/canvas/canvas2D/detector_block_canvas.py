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
# ============= standard library imports ========================
# ============= local library imports  ==========================


# ============= EOF =============================================
from pychron.canvas.canvas2D.scene.detector_block_scene import \
    DetectorBlockScene
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas


class DetectorBlockCanvas(SceneCanvas):
    scene_klass = DetectorBlockScene
    show_axes = False
    show_grids = False
    use_zoom = False
    use_pan = False

    def load_canvas_file(self, path):
        self.scene.load(path)

    def set_detector_offset(self, det, v):
        self.scene.set_detector_offset(det, v)
        self.invalidate_and_redraw()
