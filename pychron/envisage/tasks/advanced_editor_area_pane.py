# ===============================================================================
# Copyright 2014 Jake Ross
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
import sys

from PySide import QtCore
from PySide.QtGui import QAction, QCursor
from pyface.qt import QtGui
from pyface.ui.qt4.tasks.advanced_editor_area_pane import EditorAreaWidget
from pyface.ui.qt4.tasks.editor_area_pane import EditorAreaDropFilter
from pyface import confirmation_dialog
from pyface.constant import NO
from pyface.tasks.advanced_editor_area_pane import AdvancedEditorAreaPane

# ============= standard library imports ========================
# ============= local library imports  ==========================
class myEditorAreaWidget(EditorAreaWidget):
    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        for name, func in (('Close', 'close_action'),
                           ('Close All', 'close_all_action'),
                           ('Close Others', 'close_others_action')):
            act = QAction(name, self)
            act.triggered.connect(getattr(self, func))
            menu.addAction(act)

        menu.exec_(event.globalPos())

    def close_action(self):
        current = self._get_closest_editor()
        if current:
            current.editor.close()

    def close_all_action(self):
        for di in self.get_dock_widgets():
            di.editor.close()

    def close_others_action(self):
        current = self._get_closest_editor()
        if current:
            for di in self.get_dock_widgets():
                if di != current:
                    di.editor.close()

    def _get_closest_editor(self):
        pos = QCursor.pos()
        key = lambda w: QtGui.QVector2D(pos - w.pos()).lengthSquared()
        all_widgets = self.get_dock_widgets()
        if all_widgets:
            return min(all_widgets, key=key)


class myAdvancedEditorAreaPane(AdvancedEditorAreaPane):
    def create(self, parent):
        """ Create and set the toolkit-specific control that represents the
            pane.
        """
        self.control = control = myEditorAreaWidget(self, parent)
        self._filter = EditorAreaDropFilter(self)
        self.control.installEventFilter(self._filter)

        # Add shortcuts for scrolling through tabs.
        if sys.platform == 'darwin':
            next_seq = 'Ctrl+}'
            prev_seq = 'Ctrl+{'
        else:
            next_seq = 'Ctrl+PgDown'
            prev_seq = 'Ctrl+PgUp'
        shortcut = QtGui.QShortcut(QtGui.QKeySequence(next_seq), self.control)
        shortcut.activated.connect(self._next_tab)
        shortcut = QtGui.QShortcut(QtGui.QKeySequence(prev_seq), self.control)
        shortcut.activated.connect(self._previous_tab)

        # Add shortcuts for switching to a specific tab.
        mod = 'Ctrl+' if sys.platform == 'darwin' else 'Alt+'
        mapper = QtCore.QSignalMapper(self.control)
        mapper.mapped.connect(self._activate_tab)
        for i in xrange(1, 10):
            sequence = QtGui.QKeySequence(mod + str(i))
            shortcut = QtGui.QShortcut(sequence, self.control)
            shortcut.activated.connect(mapper.map)
            mapper.setMapping(shortcut, i - 1)

    def remove_editor(self, editor):
        """ Removes an editor from the pane.
        """
        editor_widget = editor.control.parent()
        if editor.dirty:
            ret = confirmation_dialog.confirm(editor_widget,
                                              'Unsaved changes to "{}". '
                                              'Do you want to continue'.format(editor.name))
            if ret == NO:
                return

        self.editors.remove(editor)
        self.control.remove_editor_widget(editor_widget)
        editor.editor_area = None
        if not self.editors:
            self.active_editor = None

# ============= EOF =============================================

