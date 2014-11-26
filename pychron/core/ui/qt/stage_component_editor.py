# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================


# ============= enthought library imports =======================
from traits.api import Event, Str
from enable.component_editor import ComponentEditor, _ComponentEditor
from enable.window import Window as EWindow
from PySide.QtCore import Qt
# ============= standard library imports ========================

# ============= local library imports  ==========================


class Window(EWindow):
    on_key_release = None

    def _on_key_released(self, event):
        if self.on_key_release:
            self.on_key_release(event)


class _LaserComponentEditor(_ComponentEditor):
    keyboard_focus = Event

    def init(self, parent):
        '''
        Finishes initializing the editor by creating the underlying toolkit
        widget.
   
        '''

        size = self._get_initial_size()
        self._window = Window(parent,
                              size=size,
                              component=self.value)

        self.control = self._window.control
        self._window.bgcolor = self.factory.bgcolor
        self._parent = parent

        self.sync_value('keyboard_focus', 'keyboard_focus', mode='both')
        self._window.on_key_release = self.onKeyUp

    def onKeyUp(self, event):


        '''
            key_released looking for text repr
            
            <-- = left
            --> = right
        '''
        ekey = event.key()
        for sk, n in ((Qt.Key_Left, 'left'),
                      (Qt.Key_Right, 'right'),
                      (Qt.Key_Up, 'up'),
                      (Qt.Key_Down, 'down')):

            if ekey == sk:
                if hasattr(self.value, 'key_released'):
                    self.value.key_released(n)
                break

    def _keyboard_focus_changed(self):
        self.control.setFocus()


class LaserComponentEditor(ComponentEditor):
    klass = _LaserComponentEditor
    keyboard_focus = Str

# ============= EOF =============================================
