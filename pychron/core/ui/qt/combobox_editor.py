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
from PySide.QtGui import QCompleter, QSizePolicy
from traits.api import Str, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.constants import OKColor
from traitsui.qt4.enum_editor import SimpleEditor


# class BaseComboBox(QComboBox):
#     def __init__(self, parent):
#         super(BaseComboBox, self).__init__(parent)
#         self.setEditable(True)
#         self.setCompleter(QCompleter(self))


class _ComboboxEditor(SimpleEditor):
    _no_enum_update = 0

    def init(self, parent):
        super(_ComboboxEditor, self).init(parent)

        control=self.control
        control.setCompleter(QCompleter(control))

    def set_size_policy(self, *args, **kw):
        self.control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def update_text_object(self, text):
        """ Handles the user typing text into the combo box text entry field.
        """
        if self._no_enum_update == 0:
            value = unicode(text)
            if self.factory.use_strict_values:
                try:
                    value = self.mapping[value]
                except:
                    try:
                        value = self.factory.evaluate(value)
                    except Exception, excp:
                        self.error( excp )
                        return

            self._no_enum_update += 1
            self.value = value
            self._set_background(OKColor)
            self._no_enum_update -= 1


class ComboboxEditor(BasicEditorFactory):
    klass = _ComboboxEditor
    name = Str
    evaluate = Str
    auto_set = Bool(True)
    use_strict_values=Bool(False)

# ============= EOF =============================================



