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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from PySide.QtGui import QBrush
from PySide.QtGui import QColor
from PySide.QtGui import QGraphicsScene
from PySide.QtGui import QGraphicsView
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QWidget
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class _ReferenceMarkEditor(Editor):
    _scene = None
    _dimension = 15
    _spacing = 5

    def init(self, parent):
        self._create_control()

    def _create_control(self):
        ctrl = QGraphicsView()
        scene = QGraphicsScene()
        ctrl.setScene(scene)

        scene.setBackgroundBrush(QBrush(QColor(237, 237, 237)))
        ctrl.setStyleSheet("border: 0px")
        md = self._dimension * 3 + self._spacing * 4
        ctrl.setMaximumWidth(md)
        ctrl.setMaximumHeight(md)

        layout = QVBoxLayout()

        layout.addWidget(ctrl)
        self._scene = scene
        self.control = QWidget()
        self.control.setLayout(layout)

    def update_editor(self, ):
        dim = self._dimension
        sp = self._spacing
        self._scene.clear()
        for r, v in enumerate(self.value.split('\n')):
            for c, vi in enumerate(v):
                rect = self._scene.addRect(c * (dim + sp), r * (dim + sp), dim, dim)
                if vi == '1':
                    rect.setBrush(QColor(200, 0, 0))


class ReferenceMarkEditor(BasicEditorFactory):
    """
    """
    klass = _ReferenceMarkEditor

# ============= EOF =============================================
