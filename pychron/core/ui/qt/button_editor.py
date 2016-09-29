# ===============================================================================
# Copyright 2015 Jake Ross
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
from pyface.qt.QtGui import QSizePolicy
from traits.api import Property, Enum, Range, Str, Trait, Bool
from traitsui.api import View
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.button_editor import CustomEditor
from traitsui.ui_traits import AView, Image
# ============= standard library imports ========================
# ============= local library imports  ==========================


class _ButtonEditor(CustomEditor):
    def init(self, parent):
        super(_ButtonEditor, self).init(parent)

        self.control.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.control.setFixedHeight(32)

        self.control.setFlat(self.factory.flat)


class ButtonEditor(BasicEditorFactory):
    """ Editor factory for buttons.
    """
    klass = _ButtonEditor

    # ---------------------------------------------------------------------------
    #  Trait definitions:
    # ---------------------------------------------------------------------------

    # Value to set when the button is clicked
    value = Property

    # Optional label for the button
    label = Str

    # The name of the external object trait that the button label is synced to
    label_value = Str

    # The name of the trait on the object that contains the list of possible
    # values.  If this is set, then the value, label, and label_value traits
    # are ignored; instead, they will be set from this list.  When this button
    # is clicked, the value set will be the one selected from the drop-down.
    values_trait = Trait(None, None, Str)

    # (Optional) Image to display on the button
    image = Image

    # Extra padding to add to both the left and the right sides
    width_padding = Range(0, 31, 7)

    # Extra padding to add to both the top and the bottom sides
    height_padding = Range(0, 31, 5)

    # Presentation style
    style = Enum('button', 'radio', 'toolbar', 'checkbox')

    # Orientation of the text relative to the image
    orientation = Enum('vertical', 'horizontal')

    # The optional view to display when the button is clicked:
    view = AView

    # ---------------------------------------------------------------------------
    #  Traits view definition:
    # ---------------------------------------------------------------------------

    traits_view = View(['label', 'value', '|[]'])

    flat = Bool(False)
    # ---------------------------------------------------------------------------
    #  Implementation of the 'value' property:
    # ---------------------------------------------------------------------------

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

# ============= EOF =============================================



