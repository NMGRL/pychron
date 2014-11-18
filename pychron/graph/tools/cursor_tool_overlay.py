#===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from chaco.text_box_overlay import TextBoxOverlay
from traits.api import Enum, Any, Bool

#============= standard library imports ========================
#============= local library imports  ==========================

class CursorToolOverlay(TextBoxOverlay):
    border_visible = True
    bgcolor = 'lightgreen'
    border_color = 'darkgreen'
    tool = Any
    visibility = Enum("auto", True, False)
    visible = False
    tooltip_mode = Bool(False)

    def _tool_changed(self, old, new):
        if old:
            old.on_trait_event(self._new_value_updated, 'current_position', remove=True)
            old.on_trait_change(self._tool_visible_changed, "visible", remove=True)
        if new:
            new.on_trait_event(self._new_value_updated, 'current_position')
            new.on_trait_change(self._tool_visible_changed, "visible")
            self._tool_visible_changed()

    def _new_value_updated(self, new):
        if new is None:
            self.text = ""
            if self.visibility == "auto":
                self.visible = False
            return
        elif self.visibility == "auto":
            self.visible = True

        if self.tooltip_mode:
            self.alternate_position = self.tool.last_mouse_position
        else:
            self.alternate_position = None

        ns = ['DAC      ={:0.5f}'.format(new[0]),
              'Intensity={:0.5f}'.format(new[1])]

        self.text = '\n'.join(ns)
        self.component.request_redraw()

    def _visible_changed(self):
        self.component.request_redraw()

    def _tool_visible_changed(self):
        self.visibility = self.tool.visible
        if self.visibility != "auto":
            self.visible = self.visibility

#============= EOF =============================================

