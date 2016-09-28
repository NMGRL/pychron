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
from pyface.qt.QtCore import QRect, QSize
from pyface.qt.QtGui import QRegion, QWidget, QVBoxLayout, QLabel, QFont, QFontMetrics, QSizePolicy, QHBoxLayout, QPalette, \
    QColor, QPainter, QPen
from pyface.qt import QtCore


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


# class BorderWidget(QWidget):
# def __init__(self, *args, **kw):
# super(BorderWidget, self).__init__(*args, **kw)
#
#         pal = QPalette()
#         color = QColor()
#         color.setNamedColor('black')
#
#         pal.setColor(QPalette.Background, color)



class NotificationWidget(QWidget):
    on_close = None

    def __init__(self, txt,
                 parent=None, color='black',
                 font='arial', fontsize=18,
                 opacity=0.75, window_bgcolor='red', *args, **kw):
        super(NotificationWidget, self).__init__(*args, **kw)

        self._font = font
        self._window_bgcolor = window_bgcolor
        self._opacity = opacity
        self._color = color
        self._fontsize = fontsize

        self._init_ui(txt)
        if parent:
            w = parent.width()
            self.setParent(parent)
            self.move(w - self.width(), 0)
            self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        c = QColor()
        c.setNamedColor(self._window_bgcolor)

        h, s, l, a = c.getHsl()
        c.setHsl(h, s, 100, a)

        pen = QPen(c, 8, QtCore.Qt.SolidLine)
        qp.setPen(pen)

        qp.drawRoundedRect(event.rect(), 12, 12)
        qp.end()

    def mouseDoubleClickEvent(self, *args, **kwargs):
        self.close()
        if self.on_close:
            self.on_close(self)

    def _init_ui(self, txt):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        pal = QPalette()
        color = QColor()
        color.setNamedColor(self._window_bgcolor)
        color.setAlpha(255 * self._opacity)
        pal.setColor(QPalette.Background, color)

        self.setAutoFillBackground(True)
        self.setPalette(pal)

        wm, hm = 5, 5
        spacing = 8
        layout = QVBoxLayout()
        layout.setSpacing(spacing)
        layout.setContentsMargins(wm, hm, wm, hm)

        nlines, ts = self._generate_text(txt)

        qlabel = QLabel('\n'.join(ts))

        ss = 'QLabel {{color: {}; font-family:{}, sans-serif; font-size: {}px}}'.format(self._color,
                                                                                        self._font,
                                                                                        self._fontsize)
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

        font = QFont(self._font, self._fontsize)
        fm = QFontMetrics(font)

        pw = max([fm.width(ti) for ti in ts])
        ph = (fm.height() + 2) * nlines

        w = pw + wm * 2
        h = ph + (hm + spacing + 1) * 2

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedWidth(w)
        self.setFixedHeight(h)

        self.setMask(mask(self.rect(), 10))

    def _generate_text(self, txt, n=20):
        if len(txt) > n:
            def tokenize(t):
                return t.split(' ')

            def linize(ts):
                s = 0
                tt = []
                for ti in ts:
                    s += len(ti)
                    tt.append(ti)
                    if s > n:
                        yield ' '.join(tt)
                        tt = []
                        s = 0
                if tt:
                    yield ' '.join(tt)

            lines = list(linize(tokenize(txt)))
            ret = len(lines), lines
        else:
            ret = 1, (txt,)
        return ret


# ============= EOF =============================================



