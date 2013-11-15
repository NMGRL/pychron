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
from traits.api import HasTraits, Str, List, Int, Event
from traitsui.api import View, Item
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from PySide.QtGui import QGraphicsView, QGraphicsScene, QBrush, QColor, \
    QPen, QWidget, QPainter
import math
#============= standard library imports ========================
#============= local library imports  ==========================
class PieClock(QWidget):
#     def __init__(self):
#         super(PieClock, self).__init__()
#         self.setGeometry(300, 300, 280, 170)
    indicator = 0
    slices = None
    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self._draw_slices(event, qp)
        self._draw_indicator(event, qp)
        qp.end()

    def _draw_indicator(self, event, qp):
        rect = event.rect()
        w = rect.width() - 10
        r = w / 2.
        theta = math.radians(self.indicator - 90)
        qp.setPen(QColor(168, 34, 255))
        cx, cy = r, r
        qp.drawLine(cx, cy, cx + r * math.cos(theta),
                    cy + r * math.sin(theta)
                    )

    def _draw_slices(self, event, painter):
        painter.setPen(QColor(168, 34, 3))

        rect = event.rect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        w -= 10
        h -= 10
        start = 90 * 16

        if self.slices:
            hours = self.slices
            sh = sum(hours)

            nh = []
            for hi in hours:
                ni = hi / float(sh) * 360
                nh.append(ni)

            for si in nh:
                span = -si * 16
                painter.drawPie(x, y, w, h, start, span)
                start += span


class _PieClockEditor(Editor):
    update_slices = Event
    def init(self, parent):
        self.control = self._create_control(parent)
        self.sync_value(self.factory.update_slices,
                        'update_slices',
                        'from')

    def _create_control(self, parent):
        ctrl = PieClock()
        return ctrl

    def _update_slices_changed(self):
        sli = getattr(self.object, self.factory.slices)
        self.control.slices = sli
        self.control.update()

#         return QGraphicsView()

#     def _build_scene(self):
#         scene = QGraphicsScene()
# #             self.control.setStyleSheet("qtLED { border-style: none; }");
# #             self.control.setAutoFillBackground(True)
#
#         # system background color
#         scene.setBackgroundBrush(QBrush(QColor(237, 237, 237)))
#         self.control.setStyleSheet("border: 0px")
#         self.control.setMaximumWidth(100)
#         self.control.setMaximumHeight(100)
#
#         x, y = 10, 10
#         rad = 20
#         cx = x + rad / 1.75
#         cy = y + rad / 1.75
#
#         brush = self.get_color(self.value.state, cx, cy, rad / 2)
#         pen = QPen()
#         pen.setWidth(0)
# #         led = scene.addEllipse(x, y, rad, rad,
# #                          pen=pen,
# #                          brush=brush
# #                          )
#
#         self.control.setScene(scene)

    def update_editor(self):
        self.control.indicator = self.value
        self.control.update()


class PieClockEditor(BasicEditorFactory):
    klass = _PieClockEditor
    slices = Str
    update_slices = Str
#============= EOF =============================================
