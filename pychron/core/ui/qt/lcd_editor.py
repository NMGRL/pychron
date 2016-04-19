# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import Int, Bool
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

# ============= standard library imports ========================
from PySide.QtGui import QColor, QLCDNumber


# ============= local library imports  ==========================

class _LCDEditor(Editor):
    def init(self, parent):
        """
        """
        self.control = lcd = QLCDNumber()
        lcd.setDigitCount(self.factory.ndigits)
        lcd.setSmallDecimalPoint(self.factory.use_small_decimal_point)
        lcd.setSegmentStyle(QLCDNumber.Flat)
        lcd.setStyleSheet('background-color:rgb(0,0,0)')
        lcd.setMinimumHeight(self.factory.height)
        lcd.setMinimumWidth(self.factory.width)
        palette = lcd.palette()
        palette.setColor(palette.Foreground, QColor('green'))
        lcd.setPalette(palette)

    def update_object(self, obj, name, new):
        """
        """
        pass

    def update_editor(self, *args, **kw):
        """
        """
        if self.control:
            self.control.display(self.str_value)


class LCDEditor(BasicEditorFactory):
    """
    """
    klass = _LCDEditor
    ndigits = Int(5)
    use_small_decimal_point = Bool(True)
    width = Int(500)
    height = Int(200)

# ============= EOF ====================================
