#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Int, Str
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
#============= standard library imports ========================
from PySide.QtGui import QProgressBar, QVBoxLayout, QLabel
#============= local library imports  ==========================

class _ProgressEditor(Editor):
    max=Int
    message=Str
    def init(self, parent):
        self.control = self._create_control(parent)
        self.control.setMaximum(self.factory.max)
        self.control.setMinimum(self.factory.min)
        if self.factory.max_name:
            self.sync_value(self.factory.max_name,'max',mode='from')
        if self.factory.message_name:
            self.sync_value(self.factory.message_name, 'message', mode='from')

    def _max_changed(self):
        print 'max',self.max
        self.control.setMaximum(self.max)

    def _message_changed(self, m):
        print 'message',m
        self._message_control.setText(m)

    def _create_control(self, parent):
        print parent
        layout=QVBoxLayout()
        pb = QProgressBar()

        self._message_control=QLabel()
        self._message_control.setText('     ')
        layout.addWidget(self._message_control)
        layout.addWidget(pb)
        parent.addLayout(layout)

        return pb

    def update_editor(self):
        print 'update editor',self.value
        self.control.setValue(self.value)


class ProgressEditor(BasicEditorFactory):
    klass = _ProgressEditor
    min = Int
    max = Int
    max_name=Str
    message_name=Str


#============= EOF =============================================
