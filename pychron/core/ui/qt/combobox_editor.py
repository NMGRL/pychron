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
import six
from pyface.qt import QtGui
from pyface.qt.QtGui import (
    QCompleter,
    QSizePolicy,
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QWidget,
)
from traits.api import Str, Bool, Event, List, Enum
from traits.trait_errors import TraitError
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.constants import OKColor, ErrorColor
from traitsui.qt4.enum_editor import SimpleEditor

from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.envisage.resources import icon


class ComboBoxWidget(QWidget):
    def __init__(self, *args, **kw):
        super(ComboBoxWidget, self).__init__(*args, **kw)

        layout = QHBoxLayout()
        layout.setSpacing(2)
        self.combo = combo = QComboBox()
        combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.button = button = QPushButton()
        button.setEnabled(False)
        button.setIcon(icon("add").create_icon())
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setFixedWidth(20)
        button.setFixedHeight(20)

        layout.addWidget(combo)
        layout.addSpacing(10)
        layout.addWidget(button)
        self.setLayout(layout)

    def setSizePolicy(self, *args, **kwargs):
        self.combo.setSizePolicy(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self.combo, item)


class _ComboboxEditor(SimpleEditor):
    # _no_enum_update = 0
    refresh = Event
    _onames = List

    def init(self, parent):
        super(_ComboboxEditor, self).init(parent)

        self.control = control = self.create_combo_box()
        if self.factory.addable:
            control = control.combo

        if self.factory.use_filter:
            self._onames = self.names

        control.addItems(self.names)

        # QtCore.QObject.connect(control,
        #                        QtCore.SIGNAL('currentIndexChanged(QString)'),
        #                        self.update_object)
        control.currentIndexChanged[str].connect(self.update_object)

        if self.factory.evaluate is not None:
            control.setEditable(True)
            if self.factory.auto_set:
                control.editTextChanged.connect(self.update_text_object)
                # QtCore.QObject.connect(control,
                #                        QtCore.SIGNAL('editTextChanged(QString)'),
                #                        self.update_text_object)
            else:
                control.lineEdit().editingFinished().connect(self.update_text_object)
                # QtCore.QObject.connect(control.lineEdit(),
                #                        QtCore.SIGNAL('editingFinished()'),
                #                        self.update_autoset_text_object)
            control.setInsertPolicy(QtGui.QComboBox.NoInsert)

        # self._no_enum_update = 0
        self.set_tooltip()
        control.setCompleter(QCompleter(control))
        self.sync_value(self.factory.refresh, "refresh", "from")

        if self.factory.addable:
            self.control.button.clicked.connect(self.update_add)

    def _refresh_fired(self):
        self.update_editor()

    def create_combo_box(self):
        if self.factory.addable:
            return ComboBoxWidget()
        else:
            return super(_ComboboxEditor, self).create_combo_box()

    def update_add(self):
        v = self.control.combo.currentText()
        if v and v not in self._names:
            self._names.append(v)
            setattr(self._object, self._name, self._names)

            self.rebuild_editor()
            self.control.combo.setEditText(v)

    def update_text_object(self, text):
        """Handles the user typing text into the combo box text entry field."""
        if self._no_enum_update == 0:
            value = six.text_type(text)
            if self.factory.use_strict_values:
                try:
                    value = self.mapping[value]
                except:
                    try:
                        value = self.factory.evaluate(value)
                    except Exception as excp:
                        self.error(excp)
                        return

            self._no_enum_update += 1
            try:
                self.value = value
                self._set_background(OKColor)
                if self.factory.addable:
                    self.control.button.setEnabled(True)

                if self.factory.use_filter:
                    vv = self._value()

                    if value and value not in vv:
                        names = fuzzyfinder(value, vv)

                        self.control.clear()
                        self.control.addItems(names)
                        self.control.showPopup()
                    else:
                        names = self.names
                        self.control.clear()
                        self.control.addItems(names)

                    try:
                        self.control.setEditText(self.str_value)
                    except:
                        self.control.setEditText("")

            except TraitError as excp:
                if self.factory.addable:
                    self.control.button.setEnabled(False)
                self._set_background(ErrorColor)

            self._no_enum_update -= 1

    def update_editor(self):
        """Updates the editor when the object trait changes externally to the
        editor.
        """
        if self._no_enum_update == 0:
            self._no_enum_update += 1
            if not self.factory.evaluate:
                try:
                    index = self.names.index(self.inverse_mapping[self.value])

                    self.control.setCurrentIndex(index)
                except BaseException as e:
                    self.control.setEditText(str(self.value))
            else:
                try:
                    self.control.setEditText(self.str_value)
                except:
                    self.control.setEditText("")
            self._no_enum_update -= 1

    use_separator = Bool(False)

class ComboboxEditor(BasicEditorFactory):
    klass = _ComboboxEditor
    name = Str
    evaluate = Str
    auto_set = Bool(True)
    use_strict_values = Bool(False)
    addable = Bool(False)
    refresh = Str
    use_filter = Bool(True)
    completion_mode = Enum(("popup", "inline"))
    use_separator = Bool(False)
    separator = Str("")


    #: The separator string used in values trait (Qt only)
    separator = Str("")
# ============= EOF =============================================
