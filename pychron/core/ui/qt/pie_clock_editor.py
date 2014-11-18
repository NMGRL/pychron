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
from PySide.QtCore import Qt, QThread

from traits.api import Str, Event
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from PySide.QtGui import QColor, \
    QWidget, QPainter, QPainterPath


#============= standard library imports ========================
#============= local library imports  ==========================
class PieClock(QWidget):
    #     def __init__(self):
    #         super(PieClock, self).__init__()
    #         self.setGeometry(300, 300, 280, 170)
    indicator = 0
    slices = None
    continue_flag = False

    def resizeEvent(self, event):
        print self.width(), self.height()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)
        self._draw_rim(event, qp)
        self._draw_slices(event, qp)
        self._draw_indicator(event, qp)
        qp.end()

    def _draw_indicator(self, event, qp):

        cx, cy, w, r = self._get_geometry(event)

        pen = qp.pen()
        pen.setWidth(3)
        pen.setColor(Qt.black)
        qp.setPen(pen)
        qp.setBrush(Qt.black)

        ro = r - 10
        cx, cy = r + 5, r + 5

        qp.translate(cx, cy)
        qp.rotate(self.indicator)

        path = QPainterPath()
        path.moveTo(-2, 0)
        path.lineTo(0, -ro)
        path.lineTo(2, 0)
        qp.drawPath(path)

        cr = 10
        cr2 = cr / 2.0

        qp.drawEllipse(-cr2, -cr2, cr, cr)

        # qp.translate(0,-ro)
        # qp.drawEllipse(-cr2, -cr2, cr, cr)


    def _get_geometry(self, event):
        rect = event.rect()
        #print rect.width(), rect.height()

        w = rect.width() - 10
        r = w / 2.
        cx, cy = r + 5, r + 5
        return cx, cy, w, r

    def _set_pen(self, qp, width=2, color=Qt.black):
        pen = qp.pen()
        pen.setWidth(width)
        pen.setColor(color)
        qp.setPen(pen)

    def _draw_rim(self, event, qp):
        cx, cy, w, r = self._get_geometry(event)
        self._set_pen(qp, width=5)
        qp.drawEllipse(cx - r, cy - r, w, w)

    def _draw_slices(self, event, qp):

        #qp.setPen(QColor(168, 34, 3))
        self._set_pen(qp)

        cx, cy, w, r = self._get_geometry(event)

        start = 90 * 16
        cx, cy = cx - w / 2., cy - w / 2.
        if self.slices:
            hours, colors = zip(*self.slices)
            sh = sum(hours)

            nh = []
            for hi, ci in self.slices:
                ni = hi / float(sh) * 360
                nh.append((ni, QColor(*ci)))

            for si, color in nh:
                span = -si * 16
                qp.setBrush(color)
                qp.drawPie(cx, cy, w, w, start, span)
                start += span


class ClockThread(QThread):
    def __init__(self, control, period=1000):
        self._control = control
        self._period = period
        QThread.__init__(self)

    def run(self):
        control = self._control
        s, _ = zip(*control.slices)
        total = float(sum(s))
        period = self._period
        tc = 0
        try:
            for si in s:
                n = int(si)
                for i in xrange(n + 1):
                    if control.continue_flag:
                        control.continue_flag = False
                        break

                    try:
                        control.indicator = 360 / total * (i + tc)
                        control.update()
                    except RuntimeError:
                        break

                    self.msleep(period)

                control.continue_flag = False
                tc += n
        except RuntimeError:
            return

        try:
            control.indicator = 360
            control.update()
        except RuntimeError:
            pass


class _PieClockEditor(Editor):
    update_slices_event = Event
    start_event = Event
    stop_event = Event
    finish_slice_event = Event
    _clock_thread = None


    def init(self, parent):
        self.control = self._create_control(parent)
        self.sync_value(self.factory.update_slices_event,
                        'update_slices_event',
                        'from')
        self.sync_value(self.factory.start_event,
                        'start_event',
                        'from')
        self.sync_value(self.factory.stop_event,
                        'stop_event',
                        'from')
        self.sync_value(self.factory.finish_slice_event,
                        'finish_slice_event',
                        'from')
        self._set_slices()
        # direction=QBoxLayout.LeftToRight
        # resizable=True
        # springy=False
        # stretch=False
        # self.set_size_policy(direction, resizable, springy, stretch)

    def _create_control(self, parent):
        ctrl = PieClock()
        return ctrl

    def _update_slices_event_changed(self):
        self._set_slices()

    def _finish_slice_event_changed(self):
        self.control.continue_flag = True

    def _set_slices(self):
        if hasattr(self.value, 'slices'):
            self.control.slices = self.value.slices
            self.control.update()

    def _stop_event_changed(self):
        if self._clock_thread:
            self._clock_thread.terminate()

    def _start_event_changed(self):
        if self._clock_thread:
            self._clock_thread.terminate()
            self._clock_thread = None

        self._clock_thread = ClockThread(self.control)
        self._clock_thread.start()

    def update_editor(self):
        pass


class PieClockEditor(BasicEditorFactory):
    klass = _PieClockEditor
    slices = Str
    update_slices_event = Str
    start_event = Str
    stop_event = Str
    finish_slice_event = Str

#============= EOF =============================================
