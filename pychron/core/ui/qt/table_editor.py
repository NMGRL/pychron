# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from pyface.qt.QtCore import Qt
from pyface.qt.QtGui import QFont, QFontMetrics
from traits.api import Event, Callable, Bool
from traitsui.editors.table_editor import TableEditor
from traitsui.qt4.table_editor import TableView


# ============= standard library imports ========================
# ============= local library imports  ==========================


class myTableView(TableView):
    clear_selection_on_dclicked = False

    def __init__(self, *args, **kw):
        super(myTableView, self).__init__(*args, **kw)

        editor = self._editor
        self.clear_selection_on_dclicked = editor.factory.clear_selection_on_dclicked
        font = editor.factory.cell_font
        if font is not None:
            fnt = QFont(font)
            size = QFontMetrics(fnt)

            vheader = self.verticalHeader()
            hheader = self.horizontalHeader()

            vheader.setDefaultSectionSize(size.height() + 2)
            #hheader.setStretchLastSection(editor.factory.stretch_last_section)

            hheader.setFont(fnt)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self._editor.factory.command_key = True
        else:
            return TableView.keyPressEvent(self, event)

    def keyReleaseEvent(self, *args, **kwargs):
        self._editor.factory.command_key = False
        return TableView.keyReleaseEvent(self, *args, **kwargs)

    def mouseDoubleClickEvent(self, QMouseEvent):
        if self.clear_selection_on_dclicked:
            self.clearSelection()


class myTableEditor(TableEditor):
    table_view_factory = myTableView
    command_key = Event
    on_command_key = Callable
    clear_selection_on_dclicked = Bool

    def _command_key_changed(self, new):
        if self.on_command_key:
            self.on_command_key(new)


# ============= EOF =============================================
