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
from traits.api import HasTraits, Button, Bool
from traitsui.api import View, UItem, HGroup
# ============= standard library imports ========================
from threading import Thread
import time

# ============= local library imports  ==========================
from pychron.paths import paths


class ZoomCalibrationManager(HasTraits):
    _alive = Bool(False)

    start_button = Button('Start')
    stop_button = Button('Stop')

    def do_collection(self):
        t = Thread(target=self._do_collection)
        t.start()

    def _do_collection(self):
        self._alive = True
        for steps in (xrange(5, 105, 5), xrange(100, 0, -5)):
            if not self._alive:
                break

            with open(paths.data_dir, 'w') as wfile:
                for zoom in steps:
                    if not self._alive:
                        break
                    self._do_collection_step(zoom, wfile)

    def _do_collection_step(self, z, wfile):
        # set zoom
        self.laser_manager.set_zoom(z, block=True)
        time.sleep(0.5)
        p, up = self.laser_manager.stage_manager.snapshot(name='zoom_cal',
                                                          auto=True)
        wfile.write('{},{}\n'.format(p, z))

    def _start_button_fired(self):
        self.do_collection()

    def _stop_button_fired(self):
        self._alive = False

    def traits_view(self):
        v = View(HGroup(UItem('start_button', enabled_when='not _alive'),
                        UItem('stop_button', enabled_when='_alive')))
        return v

# ============= EOF =============================================
