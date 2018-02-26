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
from __future__ import absolute_import
from pyface.qt.QtCore import Qt
from pyface.qt.QtGui import QColor, QWidget, QLabel
from pyface.qt.QtGui import QGraphicsView, QGraphicsScene, QBrush, \
    QPen, QRadialGradient, QVBoxLayout
from traits.api import HasTraits, Int, Callable, Str, List
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

# ============= standard library imports ========================

# ============= local library imports  ==========================


COLORS = ['red', 'yellow', 'green', 'black']
QT_COLORS = [QColor(ci) for ci in COLORS]


class LED(HasTraits):
    state = Int

    def set_state(self, v):
        if isinstance(v, str):
            self.state = COLORS.index(v)
        elif isinstance(v, (bool, int)):
            self.state = v


class ButtonLED(LED):
    callable = Callable

    def on_action(self):
        self.callable()


def change_intensity(color, fac):
    rgb = [color.red(), color.green(), color.blue()]
    rgb = [min(int(round(c * fac, 0)), 255) for c in rgb]
    return QColor(*rgb)


def get_gradient(c, cx, cy, rad):
    gradient = QRadialGradient(cx, cy, rad)  # (10, 10, 10, 10)
    gradient.setColorAt(0, Qt.white)
    gradient.setColorAt(1, c)
    brush = QBrush(gradient)
    return brush


class LEDGraphicsView(QGraphicsView):
    def __init__(self, rad, scene, *args, **kw):
        super(LEDGraphicsView, self).__init__(*args, **kw)
        self.setStyleSheet("border: 0px")
        self.setMaximumWidth(rad + 15)
        self.setMaximumHeight(rad + 15)
        self.setScene(scene)


DIAMETER_SCALAR = 1.75


class _LEDEditor(Editor):
    colors = List

    def __init__(self, *args, **kw):
        super(_LEDEditor, self).__init__(*args, **kw)
        self._led_ellipse = None

    def init(self, parent):
        """
        """
        rad = self.factory.radius

        if not rad:
            rad = 20

        if self.control is None:

            scene = QGraphicsScene()

            # system background color
            scene.setBackgroundBrush(QBrush(QColor(237, 237, 237)))

            x, y = 10, 10
            cx = x + rad / DIAMETER_SCALAR
            cy = y + rad / DIAMETER_SCALAR

            self.colors = [QColor(ci) for ci in self.factory.colors]
            brush = get_gradient(self.colors[self.value], cx, cy, rad / 2)
            pen = QPen()
            pen.setWidth(0)
            self._led_ellipse = scene.addEllipse(x, y, rad, rad, pen=pen, brush=brush)

            ctrl = LEDGraphicsView(rad, scene)

            layout = QVBoxLayout()
            layout.addWidget(ctrl)
            layout.setAlignment(ctrl, Qt.AlignHCenter)

            if self.factory.label:
                txt = QLabel(self.factory.label)
                layout.addWidget(txt)
                layout.setAlignment(txt, Qt.AlignHCenter)

            self.control = QWidget()
            self.control.setLayout(layout)

    def update_editor(self):
        """
        """
        if self.control is not None:
            rect = self._led_ellipse.rect()
            x = rect.x()
            y = rect.y()
            r = rect.width()
            x += r / DIAMETER_SCALAR
            y += r / DIAMETER_SCALAR

            self._led_ellipse.setBrush(get_gradient(self.colors[self.value], x, y, r / 2))


class LEDEditor(BasicEditorFactory):
    """
    """
    klass = _LEDEditor
    radius = Int(20)
    label = Str
    colors = List(['red', 'yellow', 'green', 'black'])

# ============= EOF ====================================


# class qtLED(QLabel):
#     _state = False
#
#     def __init__(self, parent, obj, state):
#         '''
#
#         '''
#         super(qtLED, self).__init__()
#
#         self._blink = 0
#         self.blink = False
#
#
#
#
#         self._obj = obj
#         s = self._obj.shape
#         if s == 'circle':
#             self.ascii_led = '''
#         000000-----000000
#         0000---------0000
#         000-----------000
#         00-----XXX-----00
#         0----XXXXXXX----0
#         0---XXXXXXXXX---0
#         ----XXXXXXXXX----
#         ---XXXXXXXXXXX---
#         ---XXXXXXXXXXX---
#         ---XXXXXXXXXXX---
#         ----XXXXXXXXX----
#         0---XXXXXXXXX---0
#         0----XXXXXXX----0
#         00-----XXX-----00
#         000-----------000
#         0000---------0000
#         000000-----000000
#         '''.strip()
#         else:
#             self.ascii_led = '''
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         XXXXXXXXXXXXXXXXX
#         '''.strip()
#
#         self.set_state(state)
#
#
# #    def OnMotion(self, event):
# #        print 'exception', event
# #
# #    def OnLeft(self, event):
# #        if self._state:
# #            self.set_state(0)
# #        else:
# #            self.set_state(2)
# #
# #        if self._obj is not None:
# #            self._obj.on_action()
# #
# #    def GetValue(self):
# #        return self._state
#
#     def setText(self, v):
#         pass
#
# #    def SetValue(self, v):
# #        if isinstance(v, int):
# #            self._state = v
# #
# #    def OnTimer(self, event):
# #        '''
# #
# #        '''
# #        if self.blink:
# #            if self._blink % 3 == 0:
# #                self._set_led_color(0, color=change_intensity(WX_COLORS[self._state], 0.5))
# #            else:
# #                self._set_led_color(self._state)
# #
# #            self._blink += 1
# #            if self._blink >= 100:
# #                self._blink = 0
#
#     def set_state(self, s):
#         '''
#
#         '''
#         self.blink = False
#         # use negative values for blinking
#         if s < 0:
#             self.blink = True
# #            self.timer.Start(200)
#         else:
#             pass
# #            self.timer.Stop()
#
#         s = abs(s)
#
#         self._state = s
#         self._set_led_color(s)
#
#
#     def _set_image(self, color1, color2):
#         xpm = ['17 17 3 1',  # width height ncolors chars_per_pixel
#                '0 c None',
#                'X c {}'.format(color1.name()),
#                '- c {}'.format(color2.name())
#                ]
#         xpm += [s.strip() for s in self.ascii_led.splitlines()]
#
#         def _update():
#             qim = QImage(xpm)
#             pix = QPixmap.fromImage(qim)
#             self.setPixmap(pix)
#
#         invoke_in_main_thread(_update)
#
#     def _set_led_color(self, state, color=None):
#         '''
#
#         '''
#         if color is not None:
#             color1 = color
#             color2 = color
#         else:
# #            base_color = WX_COLORS[state]
#             base_color = QT_COLORS[state]
#             color1 = base_color
#             color2 = change_intensity(base_color, 0.5)
#
#         self._set_image(color1, color2)
