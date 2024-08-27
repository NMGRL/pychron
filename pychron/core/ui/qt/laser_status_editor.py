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
import math
from traits.api import HasTraits, Property, Int, Callable, Any, Str, Dict
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt.editor import Editor

# ============= standard library imports ========================
from pyface.qt.QtGui import (
    QColor,
    QFont,
    QWidget,
    QLabel,
    QSizePolicy,
    QGraphicsView,
    QGraphicsScene,
    QBrush,
    QPen,
    QRadialGradient,
    QVBoxLayout,
    QGraphicsItem,
    QPolygon,
    QPainter,
)
from pyface.qt.QtCore import (
    QPropertyAnimation,
    QObject,
    Property as QProperty,
    QPoint,
    QParallelAnimationGroup,
    Qt,
    QSequentialAnimationGroup,
)
from six.moves import range

# ============= local library imports  ==========================
# ============= views ===================================
COLORS = ["red", "yellow", "green", "black"]
QT_COLORS = [QColor(ci) for ci in COLORS]


class _LaserStatusEditor(Editor):
    _state = False
    animation = Any
    animation_objects = Dict

    def init(self, parent):
        """ """
        self.control = self._create_control()

    def update_editor(self, *args, **kw):
        """ """
        if self.value:
            self._start_animation()
        else:
            self._stop_animation()

    def _create_control(self):
        ctrl = QGraphicsView()
        ctrl.setRenderHints(QPainter.Antialiasing)
        scene = QGraphicsScene()
        ctrl.setScene(scene)

        scene.setBackgroundBrush(QBrush(QColor(237, 237, 237)))

        ctrl.setStyleSheet("border: 0px")

        w, h = 150, 150
        ctrl.setMinimumHeight(h + 22)
        ctrl.setMinimumWidth(w + 22)

        cx, cy = w / 2, h / 2.0
        ex, ey = cx, cy + 20
        pen = QPen()
        pen.setStyle(Qt.NoPen)
        # pen.setColor(QColor(237, 237, 237))
        bounding_rect = scene.addRect(0, 0, w, h, pen=pen)
        bounding_rect.setFlag(QGraphicsItem.ItemClipsChildrenToShape)

        self.animation = QSequentialAnimationGroup()
        self._add_laser_logo(scene, bounding_rect, ex, ey, cx, cy, w, h)
        self._add_bullet(scene, bounding_rect, ex, ey, cx, cy)
        self._add_fragments(scene, bounding_rect, ex, ey)

        self.animation.setLoopCount(-1)

        return ctrl

    def _add_fragments(self, scene, bounding_rect, ex, ey):
        pen = QPen()
        pen.setWidth(1)

        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(QColor("orange"))
        ganim = QParallelAnimationGroup()

        n = 8
        s = 360 / n
        vs = ((0, 50, 7), (s / 2, 30, 10))
        vs = ((0, 50, 10),)
        for j, l, ed in vs:
            for i in range(n):
                theta = math.radians(j + i * s)
                x = l * math.cos(theta)
                y = l * math.sin(theta)

                fragment = scene.addEllipse(
                    ex - ed / 2, ey - ed / 2, ed, ed, pen=pen, brush=brush
                )
                fragment.setParentItem(bounding_rect)

                self.animation_objects["fragment{}{}".format(l, i)] = w = Wrapper(
                    fragment
                )
                gg = QSequentialAnimationGroup()
                anim = QPropertyAnimation(w, "position")
                anim.setDuration(750)
                pos = fragment.pos()
                anim.setKeyValueAt(0, pos)

                anim.setKeyValueAt(1, QPoint(x, y))

                gg.addAnimation(anim)
                anim = QPropertyAnimation(w, "position")
                anim.setDuration(1)
                anim.setKeyValueAt(0, pos)
                anim.setKeyValueAt(1, pos)

                gg.addAnimation(anim)
                ganim.addAnimation(gg)

        r = 15
        center = scene.addEllipse(
            ex - r / 2.0, ey - r / 2.0, r, r, pen=pen, brush=brush
        )
        center.setParentItem(bounding_rect)
        center.setBrush(Qt.black)
        self.animation_objects["center"] = w = Wrapper(
            center, opos=(ex - r / 2.0, ey - r / 2.0), radius=r
        )
        gg = QSequentialAnimationGroup()
        anim = QPropertyAnimation(w, "radius")
        anim.setDuration(750)
        anim.setKeyValueAt(0, r)
        anim.setKeyValueAt(1, r * 3)
        gg.addAnimation(anim)
        anim = QPropertyAnimation(w, "radius")
        anim.setDuration(1)
        anim.setKeyValueAt(0, r)
        anim.setKeyValueAt(1, r)
        gg.addAnimation(anim)

        ganim.addAnimation(gg)
        self.animation.addAnimation(ganim)

    def _add_laser_logo(self, scene, bounding_rect, ex, ey, cx, cy, w, h):
        tw = w - 20
        poly = QPolygon()
        poly.append(QPoint(cx - tw / 2, h - 10))
        poly.append(QPoint(cx + tw / 2, h - 10))
        poly.append(QPoint(cx, 10))
        pen = QPen()
        pen.setWidth(5)
        # brush = QBrush()
        # brush.setStyle(Qt.SolidPattern)
        # brush.setColor(QColor(255, 255, 0))
        item = scene.addPolygon(poly, pen=pen)
        item.setBrush(QColor(255, 255, 0))
        item.setParentItem(bounding_rect)
        pen = QPen()
        pen.setWidth(3)
        item = scene.addLine(cx - 40, ey, cx, ey, pen=pen)
        item.setParentItem(bounding_rect)

        pen = QPen()
        pen.setColor(Qt.black)
        pen.setWidth(2)

        for l, n in ((25, 12), (17, 24)):
            s = 360 / n
            for theta in range(n):
                theta = math.radians(theta * s)
                x = l * math.cos(theta)
                y = l * math.sin(theta)
                ll = scene.addLine(ex, ey, ex + x, ey + y, pen=pen)
                ll.setParentItem(bounding_rect)

        return bounding_rect

    def _start_animation(self):
        self.animation.start()

    def _stop_animation(self):
        self.animation.setCurrentTime(0)
        self.animation.stop()

    def _add_bullet(self, scene, bounding_rect, ex, ey, cx, cy):
        pen = QPen()
        pen.setColor(QColor("orange"))
        pen.setWidth(1)
        bullet = scene.addRect(-16, ey - 5, 15, 10, pen=pen)
        bullet.setParentItem(bounding_rect)
        bullet.setBrush(Qt.black)
        self.animation_objects["bullet"] = w = Wrapper(bullet)

        anim = QPropertyAnimation(w, "position")
        anim.setDuration(500)
        anim.setKeyValueAt(0, bullet.pos())
        anim.setKeyValueAt(1, QPoint(cx + 10, 0))
        self.animation.addAnimation(anim)


class Wrapper(QObject):
    def __init__(self, item, radius=1, opos=None):
        super(Wrapper, self).__init__()
        self._item = item
        self._position = QPoint(0, 0)
        self._radius = radius

        if opos:
            self._ox, self._oy = opos
        else:
            self._ox = None
            self._oy = None

    def get_position(self):
        return self._position

    def set_position(self, v):
        self._position = v
        self._item.setPos(v)

    def get_radius(self):
        return self._radius

    def set_radius(self, r):
        rect = self._item.rect()
        rect.setWidth(r)
        rect.setHeight(r)
        rect.setX(self._ox - (r - self._radius) / 2.0)
        rect.setY(self._oy - (r - self._radius) / 2.0)
        self._item.setRect(rect)

    position = QProperty(QPoint, get_position, set_position)
    radius = QProperty(int, get_radius, set_radius)


class LaserStatusEditor(BasicEditorFactory):
    """ """

    klass = _LaserStatusEditor
    message_name = Str


# ============= EOF ====================================
