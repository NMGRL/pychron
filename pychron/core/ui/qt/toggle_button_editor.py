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
from pyface.image_resource import ImageResource
from traits.api import Int, Any, Instance, Bool, Str

#============= standard library imports ========================
#============= local library imports  ==========================

from pyface.qt import QtGui, QtCore
from traitsui.qt4.editor import Editor


class _ToggleButtonEditor(Editor):
    icon_on = Any
    icon_off = Any
    toggle_state = Bool
    tooltip_on = Str
    tooltip_off = Str

    def init(self, parent):
        self.icon_on = QtGui.QIcon(self.factory.image_on.absolute_path)
        self.icon_off = QtGui.QIcon(self.factory.image_off.absolute_path)
        control = self.control = QtGui.QToolButton()
        control.setAutoRaise(True)
        control.setIcon(self.icon_on)

        self.tooltip_on = self.factory.tooltip_on
        self.tooltip_off = self.factory.tooltip_off

        control.setToolTip(self.tooltip_on)

        control.setCheckable(True)
        control.toggled.connect(self._toggle_button)
        if self.factory.label:
            control.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        else:
            control.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

    def _toggle_button(self):
        self.toggle_state = not self.toggle_state
        if self.toggle_state:
            self.control.setIcon(self.icon_off)
            self.control.setToolTip(self.tooltip_off)
        else:
            self.control.setIcon(self.icon_on)
            self.control.setToolTip(self.tooltip_on)


from traitsui.qt4.basic_editor_factory import BasicEditorFactory


class ToggleButtonEditor(BasicEditorFactory):
    klass = _ToggleButtonEditor
    width = Int
    height = Int
    image_on = Instance(ImageResource)
    image_off = Instance(ImageResource)

    tooltip_on = Str
    tooltip_off = Str
    label = Str


#============= EOF =============================================

