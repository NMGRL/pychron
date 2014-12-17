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
from pyface.qt import QtCore
from PySide.QtCore import QRect, QSize
from PySide.QtGui import QRegion, QWidget, QVBoxLayout, QLabel, QFont, QFontMetrics, QSizePolicy, QHBoxLayout
# ============= standard library imports ========================
# ============= local library imports  ==========================


def mask(rect, r):
    region = QRegion()
    region += rect.adjusted(r, 0, -r, 0)
    region += rect.adjusted(0, r, 0, -r)

    # top left
    corner = QRect(rect.topLeft(), QSize(r * 2, r * 2))
    region += QRegion(corner, QRegion.Ellipse)

    # top right
    corner.moveTopRight(rect.topRight())
    region += QRegion(corner, QRegion.Ellipse)

    # bottom left
    corner.moveBottomLeft(rect.bottomLeft())
    region += QRegion(corner, QRegion.Ellipse)

    # bottom right
    corner.moveBottomRight(rect.bottomRight())
    region += QRegion(corner, QRegion.Ellipse)

    return region


class NotificationWidget(QWidget):
    on_close = None

    def __init__(self, txt, color='black',
                 font='arial', fontsize=18,
                 opacity=0.95, window_bgcolor='red', *args, **kw):
        super(NotificationWidget, self).__init__(*args, **kw)
        self.font = font
        self.window_bgcolor = window_bgcolor
        self.opacity = opacity
        self.color = color
        self.fontsize = fontsize
        self._init_ui(txt)

    def _init_ui(self, txt):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('NotificationWidget {{background-color: {}}}'.format(self.window_bgcolor))

        wm, hm = 5, 5
        spacing = 8
        layout = QVBoxLayout()
        layout.setSpacing(spacing)
        layout.setContentsMargins(wm, hm, wm, hm)
        self.label = qlabel = QLabel(txt)

        ss = 'QLabel {{color: {}; font-family:{}, sans-serif; font-size: {}px}}'.format(self.color,
                                                                                        self.font,
                                                                                        self.fontsize)
        qlabel.setStyleSheet(ss)
        layout.addWidget(qlabel)

        hlabel = QLabel('double click to dismiss')
        hlabel.setStyleSheet('QLabel {font-size: 10px}')

        hlayout = QHBoxLayout()

        hlayout.addStretch()
        hlayout.addWidget(hlabel)
        hlayout.addStretch()

        layout.addLayout(hlayout)

        self.setLayout(layout)

        font = QFont(self.font, self.fontsize)
        fm = QFontMetrics(font)

        pw = fm.width(txt)
        ph = fm.height()
        w = pw + wm * 2
        h = ph + (hm+spacing+1) * 2

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedWidth(w)
        self.setFixedHeight(h)
        self.setWindowOpacity(self.opacity)

        self.setMask(mask(self.rect(), 10))
        self.show()

    def set_position(self, x, y, w, h):
        self.setGeometry(x + w - self.width(), y, self.width(), self.height())

    def mouseDoubleClickEvent(self, *args, **kwargs):
        self.close()
        if self.on_close:
            self.on_close(self)


# ============= EOF =============================================



