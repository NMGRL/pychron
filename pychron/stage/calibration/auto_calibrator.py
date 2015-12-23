# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance
# ============= standard library imports ========================
import time
from threading import Thread
# ============= local library imports  ==========================
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.view_util import open_view
from pychron.lasers.stage_managers.stage_visualizer import StageVisualizer
from pychron.stage.calibration.calibrator import TrayCalibrator


class SemiAutoCalibrator(TrayCalibrator):
    """
        1a. user move to center
         b. record position
        2a. user move to right
         b. record position
        3. traverse holes finding autocenter position
    """

    _alive = False
    stage_map = Instance('pychron.stage.maps.base_stage_map.BaseStageMap')

    def handle(self, step, x, y, canvas):
        if step == 'Calibrate':
            canvas.new_calibration_item()
            return dict(calibration_step='Locate Center')
        elif step == 'Locate Center':
            canvas.calibration_item.set_center(x, y)
            return dict(calibration_step='Locate Right', cx=x, cy=y)
        elif step == 'Locate Right':
            canvas.calibration_item.set_right(x, y)
            self.save(canvas.calibration_item)
            return dict(calibration_step='Tranverse',
                        rotation=canvas.calibration_item.rotation)
        elif step == 'Tranverse':
            self._alive = True
            t = Thread(target=self._traverse, args=(canvas.calibration_item,))
            t.start()
            return dict(calibration_step='Cancel')
        elif step == 'Cancel':
            self._alive = False
            return dict(calibration_step='Calibrate')

    def _traverse(self, calibration):
        """
            visit each hole in holes
            record autocenter position
            warn user about failures
        """
        sm = self.stage_manager

        holes = self.stage_map.sample_holes
        results = []
        failures = []
        for hi in holes:
            if not self.isAlive():
                self.info('hole tranverse canceled')
                break

            x, y = hi.x, hi.y
            # move to nominal hole position
            sm.linear_move(x, y, use_calibration=True, block=True)

            # delay for image refresh
            time.sleep(0.5)

            # autocenter
            npt, corrected, interp = sm.autocenter(holenum=hi.id, save=True)
            results.append((npt, corrected))
            if not corrected:
                self.info('Failed to autocenter {}'.format(hi.id))
            else:
                failures.append(npt)

        # display the results
        sv = StageVisualizer()
        sv.set_stage_map(self.stage_map, results, calibration)

        invoke_in_main_thread(open_view, sv)

    def isAlive(self):
        return self._alive


class AutoCalibrator(TrayCalibrator):
    """
        1a. move to center position automatically
         b. autocenter
        2a. move to right position automatically
         b. autocenter
    """
# ============= EOF =============================================
