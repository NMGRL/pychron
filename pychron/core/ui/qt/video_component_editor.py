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

import time

# ============= standard library imports ========================
from pyface.qt.QtCore import QTimer
# ============= enthought library imports =======================
from traits.api import Any, Int, Str, Event

# ============= local library imports  ==========================
from .stage_component_editor import _LaserComponentEditor, LaserComponentEditor


class _VideoComponentEditor(_LaserComponentEditor):
    """
    """
    playTimer = Any
    fps = Int
    stop_timer = Event
    _alive = None

    def init(self, parent):
        """
        Finishes initializing the editor by creating the underlying toolkit
        widget.

        """
        super(_VideoComponentEditor, self).init(parent)

        # self.playTimer = QTimer(self.control)
        # self.playTimer.timeout.connect(self.update)
        # self.control.connect(self.playTimer, SIGNAL('timeout()'), self.update)

        # if self.value.fps:
        #     self.playTimer.setInterval(1000 / float(self.value.fps))
        # self.playTimer.start()

        self.value.on_trait_change(self.stop, 'closed_event')

        # self.value.on_trait_change(self._update_fps, 'fps')
        self.sync_value('stop_timer', 'stop_timer', mode='from')
        # self._prev_time = time.time()
        self._alive = True
        QTimer.singleShot(self._get_interval(), lambda: self.update(-1))

    # def _update_fps(self):
    #     pass
    # if self.value.fps:
    #     self.playTimer.setInterval(1000 / float(self.value.fps))

    def _get_interval(self):
        if self.value.fps:
            return 1000 / float(self.value.fps)

    def stop(self):
        print('VideoComponentEditor stop')
        self._alive = False
        # try:
        #     self.playTimer.stop()
        # except RuntimeError:
        #     pass

    def update(self, pt):
        if self.control and self._alive:
            self.value.request_redraw()
            # self.value.invalidate_and_redraw()
            st = time.time()
            et = time.time() - pt
            pt = st
            # print et
            #  = time.time()
            # self.value.invalidate_and_redraw()
            QTimer.singleShot(max(1, self._get_interval() - et), lambda: self.update(pt))

    def _stop_timer_fired(self):
        print('VideoComponentEditor stopping playTimer')
        self._alive = False
        # self.playTimer.stop()


class VideoComponentEditor(LaserComponentEditor):
    """
    """
    klass = _VideoComponentEditor
    stop_timer = Str

# ============= EOF ====================================
