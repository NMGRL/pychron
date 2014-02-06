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
from traits.api import Int, Any, Instance, Bool, Str, Property

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
        control.setIconSize(QtCore.QSize(self.factory.width, self.factory.height))

        self.tooltip_on = self.factory.tooltip_on
        self.tooltip_off = self.factory.tooltip_off

        control.setToolTip(self.tooltip_on)

        control.setCheckable(True)
        control.toggled.connect(self._toggle_button)
        if self.factory.label:
            control.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        else:
            control.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

        QtCore.QObject.connect(control, QtCore.SIGNAL('clicked()'),
                               self.update_object)

    def _toggle_button(self):
        self.toggle_state = not self.toggle_state
        if self.toggle_state:
            self.control.setIcon(self.icon_off)
            self.control.setToolTip(self.tooltip_off)
        else:
            self.control.setIcon(self.icon_on)
            self.control.setToolTip(self.tooltip_on)

    def prepare(self, parent):
        """ Finishes setting up the editor. This differs from the base class
            in that self.update_editor() is not called at the end, which
            would fire an event.
        """
        name = self.extended_name
        if name != 'None':
            self.context_object.on_trait_change(self._update_editor, name,
                                                dispatch='ui')
        self.init(parent)
        self._sync_values()

    def update_object(self):
        """ Handles the user clicking the button by setting the factory value
            on the object.
        """
        self.value = self.factory.value

    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        pass


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
    value = Property


    def __init__(self, **traits):
        self._value = 0
        super(ToggleButtonEditor, self).__init__(**traits)


    def _get_value(self):
        return self._value

    def _set_value(self, value):
        self._value = value
        if isinstance(value, basestring):
            try:
                self._value = int(value)
            except:
                try:
                    self._value = float(value)
                except:
                    pass


#============= EOF =============================================

