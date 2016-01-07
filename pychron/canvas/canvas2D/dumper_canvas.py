# ===============================================================================
# Copyright 2015 Jake Ross
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
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
from pychron.canvas.canvas2D.scene.dumper_scene import DumperScene


class DumperCanvas(ExtractionLineCanvas2D):
    def load_canvas_file(self, pathname, configpath, valvepath, canvas):
        self.scene.load(pathname, configpath, valvepath, canvas)

    def set_item_state(self, item_name, state):
        item = self.scene.get_item(item_name)
        if item:
            item.state = state
            self._select_hook(item)
            self.invalidate_and_redraw()

    def _select_hook(self, item):
        if hasattr(item, 'associations'):
            if item.associations:
                for i in item.associations:
                    self._set_associated(i, item.state)

    def _set_associated(self, i, state):
        item = self.scene.get_item(i)

        item.set_state(state)
        item.request_layout()

    def _scene_default(self):
        s = DumperScene()
        return s

# ============= EOF =============================================
