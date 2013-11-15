#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Event, Callable
from traitsui.api import View, Item
from traitsui.qt4.table_editor import TableEditor as qtTableEditor, TableView
from traitsui.editors.table_editor import TableEditor
from PySide.QtCore import Qt
#============= standard library imports ========================
#============= local library imports  ==========================
class myTableView(TableView):
    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self._editor.factory.command_key = True
        else:
            return TableView.keyPressEvent(self, event)

    def keyReleaseEvent(self, *args, **kwargs):
        self._editor.factory.command_key = False
        return TableView.keyReleaseEvent(self, *args, **kwargs)

class myTableEditor(TableEditor):
    table_view_factory = myTableView
    command_key = Event
    on_command_key = Callable
    def _command_key_changed(self, new):
        if self.on_command_key:
            self.on_command_key(new)


#============= EOF =============================================
