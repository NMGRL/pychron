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
from traits.api import HasTraits
from traitsui.api import View, Item
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
from pychron.pyscripts.pyscript import makeRegistry, verbose_skip
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.ui.gui import invoke_in_main_thread
import time
#============= standard library imports ========================
#============= local library imports  ==========================
command_register = makeRegistry()

class LaserPyScript(ExtractionPyScript):

    _task = None
    @verbose_skip
    @command_register
    def power_map(self, *args, **kw):
        self._task = None
        self.debug('Opening power map task')
        invoke_in_main_thread(self._open_power_map, *args)

        # wait until task is opened
        while self._task is None:
            time.sleep(0.5)

        self._task.execute_active_editor(block=True)
        self.debug('power mapping complete')

    def _open_power_map(self, cx, cy, padding, step_length, bd, power):
        app = self.application
        task = app.open_task('pychron.laser.calibration')
        task.new_power_map()
        task.active_editor.editor.trait_set(center_x=cx,
                                            center_y=cy,
                                            beam_diameter=bd,
                                            padding=padding,
                                            request_power=power,
                                            step_length=step_length
                                            )
        self._task = task

#     def _power_map(self, cx, cy, padding, bd, power):
#         print cx, cy, padding
#         task.execute_active_editor(block=True)

#         self._manager_action([('do_power_map', (cx, cy, padding, bd, power), {})],
#                              name=self.extract_device,
#                              protocol=ILaserManager)
#============= EOF =============================================
