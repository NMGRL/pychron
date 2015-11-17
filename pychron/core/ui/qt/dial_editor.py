# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from pyface.qt import QtGui
from traits.api import Any, Int, Float, Str, Bool, Either, Callable

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class _DialEditor(Editor):
    dial = Any
    label = Any
    _format_func = None

    def init(self, parent):
        self._create_control(parent)

    def _create_control(self, parent):
        self.dial = QtGui.QDial()
        self.dial.setNotchesVisible(self.factory.notches_visible)
        self.dial.setRange(self.factory.low, self.factory.high)
        self.dial.setSingleStep(self.factory.step)
        if self.factory.width > 0:
            self.dial.setFixedWidth(self.factory.width)
        if self.factory.height > 0:
            self.dial.setFixedHeight(self.factory.height)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.dial)
        if self.factory.display_value:
            self.label = QtGui.QLabel()

            hbox.addWidget(self.label)

            if self.factory.value_format:
                if hasattr(self.factory.value_format, '__call__'):
                    func = self.factory.value_format
                else:
                    func = lambda x: self.factory.value_format.format(x)

            else:
                func = lambda x: '{}'.format(x)

            self.label.setText(func(self.value))
            self._format_func = func

        self.control = self.dial
        self.dial.valueChanged[int].connect(self.valueChanged)
        parent.addLayout(hbox)

    def update_editor(self):
        pass

    def valueChanged(self):
        self.value = self.dial.value()
        if self.label:
            v = self._format_func(self.value)

            self.label.setText(v)


class DialEditor(BasicEditorFactory):
    klass = _DialEditor
    low = Int
    high = Int
    step = Int(1)
    display_value = Bool(False)
    value_format = Either(Str, Callable)
    height = Float
    width = Float
    notches_visible = Bool(False)

# ============= EOF =============================================

