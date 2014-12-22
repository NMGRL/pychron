# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Float, Str
# ============= standard library imports ========================
from PySide.QtGui import QDoubleSpinBox
from PySide import QtCore
from traitsui.qt4.range_editor import SimpleSpinEditor
from traitsui.basic_editor_factory import BasicEditorFactory
# ============= local library imports  ==========================

class _DoubleSpinnerEditor(SimpleSpinEditor):
    def init (self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        factory = self.factory
        if not factory.low_name:
            self.low = factory.low

        if not factory.high_name:
            self.high = factory.high

        self.sync_value(factory.low_name, 'low', 'from')
        self.sync_value(factory.high_name, 'high', 'from')
        low = self.low
        high = self.high

        self.control = QDoubleSpinBox()
        if factory.step:
            self.control.setSingleStep(factory.step)

        self.control.setMinimum(low)
        self.control.setMaximum(high)
        self.control.setValue(self.value)
        QtCore.QObject.connect(self.control,
                QtCore.SIGNAL('valueChanged(int)'), self.update_object)
        self.set_tooltip()

class DoubleSpinnerEditor(BasicEditorFactory):
    low = Float
    high = Float
    low_name = Str
    high_name = Str
    step = Float
    klass = _DoubleSpinnerEditor
# ============= EOF =============================================
