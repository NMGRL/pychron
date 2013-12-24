#===============================================================================
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
#===============================================================================


#============= enthought library imports =======================
from traits.api import Event, Str
from enable.component_editor import ComponentEditor, _ComponentEditor

#============= standard library imports ========================
from wx import EVT_KEY_UP

#============= local library imports  ==========================

class _LaserComponentEditor(_ComponentEditor):
    keyboard_focus = Event
    def init(self, parent):
        '''
        Finishes initializing the editor by creating the underlying toolkit
        widget.
   
        '''
        super(_LaserComponentEditor, self).init(parent)
        self.control.Bind(EVT_KEY_UP, self.onKeyUp)

        self.sync_value('keyboard_focus', 'keyboard_focus', mode='both')

    def onKeyUp(self, event):
        self.value.normal_key_up(event)

    def _keyboard_focus_changed(self):
        self.control.SetFocus()

class LaserComponentEditor(ComponentEditor):
    klass = _LaserComponentEditor
    keyboard_focus = Str
#============= EOF =============================================
