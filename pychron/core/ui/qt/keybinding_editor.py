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
from PySide import QtGui, QtCore
from traits.trait_types import Event
from traitsui.api import View, UItem
from traitsui.editors import TableEditor
from traitsui.handler import Controller
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from traitsui.qt4.key_event_to_name import key_event_to_name
from traitsui.table_column import ObjectColumn
# ============= standard library imports ========================
# ============= local library imports  ==========================
# from traitsui.basic_editor_factory import BasicEditorFactory
from pychron.envisage.key_bindings import keybinding_exists


class KeyBindingsEditor(Controller):
    def traits_view(self):
        cols = [ObjectColumn(name='binding', editor=KeyBindingEditor()),
                ObjectColumn(name='description', editable=False, width=400)]
        v = View(UItem('bindings', editor=TableEditor(columns=cols)),
                 width=500,
                 height=600,
                 title='Edit Key Bindings',
                 kind='livemodal',
                 buttons=['OK','Cancel'],
                 resizable=True)
        return v


class KeyBindingControl(QtGui.QLabel):
    def keyPressEvent(self, event):
        """ Handle keyboard keys being pressed.
        """
        # Ignore presses of the control and shift keys.
        if event.key() not in (QtCore.Qt.Key_Control, QtCore.Qt.Key_Shift):
            self.editor.key = event


class _KeyBindingEditor(Editor):
    key = Event
    # clear = Event
    # refresh_needed = Event
    # dump_needed = Event

    def dispose(self):
        # override Editor.dispose. don't break reference to control
        if self.ui is None:
            return

        name = self.extended_name
        if name != 'None':
            self.context_object.on_trait_change(self._update_editor, name,
                                                remove=True)

        if self._user_from is not None:
            for name, handler in self._user_from:
                self.on_trait_change(handler, name, remove=True)

        if self._user_to is not None:
            for object, name, handler in self._user_to:
                object.on_trait_change(handler, name, remove=True)

                # self.object = self.ui = self.item = self.factory = self.control = \
                # self.label_control = self.old_value = self._context_object = None

    def init(self, parent):
        self.control = self._create_control()
        # self.sync_value(self.factory.refresh_needed, 'refresh_needed', mode='to')
        # self.sync_value(self.factory.refresh_needed, 'dump_needed', mode='to')

    def _create_control(self):
        ctrl = KeyBindingControl()
        ctrl.editor = self
        return ctrl

    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        if self.control:
            self.control.setText(self.value)

    def _key_changed(self, event):
        key_name = key_event_to_name(event)
        key_name = key_name.replace('-', '+')
        desc = keybinding_exists(key_name)
        if desc:
            if QtGui.QMessageBox.question(self.control,
                                          "Duplicate Key Definition",
                                          "'%s' has already been assigned to '%s'.\n"
                                          "Do you wish to continue?" % (key_name,
                                                                        desc),
                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                          QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
                return
            # else:
            #     clear_keybinding(desc)
            #     self.refresh_needed = True

        self.value = key_name
        self.control.setText(key_name)


class KeyBindingEditor(BasicEditorFactory):
    klass = _KeyBindingEditor
    # refresh_needed = Str

# ============= EOF =============================================



