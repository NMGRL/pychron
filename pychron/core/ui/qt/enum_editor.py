# ===============================================================================
# Copyright 2016 ross
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
from pyface.qt import QtGui
from traits.api import Any, Str, Event, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.helper import enum_values_changed
from traitsui.qt4.enum_editor import SimpleEditor


class mComboBox(QtGui.QComboBox):
    def __init__(self, disable_scroll=True, *args, **kw):
        super(mComboBox, self).__init__(*args, **kw)
        self._disable_scroll = disable_scroll

    def wheelEvent(self, *args, **kwargs):
        if not self._disable_scroll:
            return super(mComboBox, self).wheelEvent(*args, **kwargs)


class _EnumEditor(SimpleEditor):
    def create_combo_box(self):
        """ Returns the QComboBox used for the editor control.
        """
        control = mComboBox(self.factory.disable_scroll)
        control.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        control.setSizePolicy(QtGui.QSizePolicy.Maximum,
                              QtGui.QSizePolicy.Fixed)
        return control


class myEnumEditor(BasicEditorFactory):
    klass = _EnumEditor

    evaluate = Any

    values = Any

    # Extended name of the trait on **object** containing the enumeration data:
    object = Str('object')

    # Name of the trait on 'object' containing the enumeration data
    name = Str

    # Fired when the **values** trait has been updated:
    values_modified = Event

    disable_scroll = Bool(True)

    def _values_changed(self):
        """ Recomputes the mappings whenever the **values** trait is changed.
        """
        self._names, self._mapping, self._inverse_mapping = \
            enum_values_changed(self.values)

        self.values_modified = True

# ============= EOF =============================================
