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

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
import time

from pychron.lasers.stage_managers.calibration.calibrator import TrayCalibrator


class SemiautoCalibrator(TrayCalibrator):
    '''
        1a. user move to center
         b. record position
        2a. user move to right
         b. record position
        3. traverse holes finding autocenter position
    '''

    _alive = False

    def handle(self, step, x, y, canvas):
        if step == 'Calibrate':
            self._alive = True
            return dict(calibration_step='Locate Center')
#            return 'Locate Center', None, None, None, None
        elif step == 'Locate Center':
            return dict(calibration_step='Locate Right')
#            return 'Locate Right', None, None, None, None
        elif step == 'Cancel':
            self._alive = False
            return dict(calibration_step='Calibrate')
#            return 'Calibrate', None, None, None, None

    def _traverse(self, holes):
        '''
            visit each hole in holes 
            record autocenter position
            warn user about failures
        '''
        sm = self.stage_manager

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
            npts, corrected, interp = sm.autocenter(save=True)
            if not corrected:
                self.info('Failed to autocenter {}'.format(hi.id))

    def isAlive(self):
        return self._alive

class AutoCalibrator(TrayCalibrator):
    '''
        1a. move to center position automatically
         b. autocenter
        2a. move to right position automatically
         b. autocenter
    '''
# ============= EOF =============================================
