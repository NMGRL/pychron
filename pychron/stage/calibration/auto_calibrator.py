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
from traits.api import Instance, HasTraits, Str, Bool, Float
# ============= standard library imports ========================
import time
from threading import Thread
from numpy import array, hstack
# ============= local library imports  ==========================
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.view_util import open_view
from pychron.lasers.stage_managers.stage_visualizer import StageVisualizer
from pychron.stage.calibration.calibrator import TrayCalibrator


class Result(HasTraits):
    hole_id = Str
    corrected = Bool
    dx = Float
    dy = Float


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
        ret = None
        if step == 'Calibrate':
            canvas.new_calibration_item()
            self.calibration_step = 'Locate Center'
        elif step == 'Locate Center':
            canvas.calibration_item.set_center(x, y)

            # check stage map has at least one calibration hole.
            # if not issue warning and ask for manual locate right
            if self._check_auto_calibration():
                self.calibration_step = 'Auto Calibration'
            else:
                name = self.stage_map.name
                msg = 'Auto Rotation calibration not available.\n ' \
                      '{} has no calibration holes'.format(name)
                self.warning_dialog(msg)
                self.calibration_step = 'Locate Right'

            ret = dict(cx=x, cy=y, clear_corrections=False)
            canvas.calibration_item.rotation = 0
            canvas.calibration_item.set_right(x, y)

        elif step == 'Locate Right':
            canvas.calibration_item.set_right(x, y)
            ret = dict(calibration_step='Traverse',
                       clear_corrections=False,
                       rotation=canvas.calibration_item.rotation)
        elif step == 'Auto Calibration':
            self._alive = True
            t = Thread(target=self._auto_calibrate,
                       args=(canvas.calibration_item,))
            t.start()
            self.calibration_step = 'Cancel'
        elif step == 'Traverse':
            if self.confirmation_dialog('Start Autocentering Travsere'):
                t = Thread(target=self._traverse,
                           args=(canvas.calibration_item,))
                t.start()
                self.calibration_step = 'Cancel'
            else:
                self.calibration_step = 'Calibrate'
        elif step == 'Cancel':
            self._alive = False
            self.calibration_step = 'Calibrate'

        return ret

    def _auto_calibrate(self, calibration):
        smap = self.stage_map

        rrot = lrot = None
        # locate right
        if self._alive:
            hole = smap.get_calibration_hole('east')
            if hole is not None:
                self.debug('Locate east {}'.format(hole.id))
                npt, corrected = self._autocenter(hole)
                if corrected:
                    rrot = calibration.calculate_rotation(*npt)
                    calibration.set_right(*npt)
                    self.debug('Calculated rotation= {}'.format(rrot))

        # locate left
        if self._alive:
            hole = smap.get_calibration_hole('west')
            if hole is not None:
                self.debug('Locate west {}'.format(hole.id))
                npt, corrected = self._autocenter(hole)
                if corrected:
                    lrot = calibration.calculate_rotation(*npt, sense='west')
                    self.debug('Calculated rotation= {}'.format(lrot))

        if self._alive:
            if lrot is None:
                rot = rrot
            elif rrot is None:
                rot = lrot
            else:
                self.debug('rrot={}, lrot={}'.format(rrot, lrot))
                # average rotation
                rot = (rrot + lrot) / 2.

            if rot is None:
                self.warning('failed calculating rotation')
                self.calibration_step = 'Calibrate'
                return

            # set rotation
            calibration.rotation = rot
            self.rotation = rot
            self.save_event = {'clear_corrections': False}

            # traverse holes
            self._traverse(calibration)

    def _traverse(self, calibration):
        """
            visit each hole in holes
            record autocenter position
            warn user about failures
        """
        sm = self.stage_manager
        smap = self.stage_map
        holes = smap.sample_holes
        results = []
        points = []
        center = calibration.center

        # center = (-calibration.center[0], -calibration.center[1])

        dxs, dys = array([]), array([])
        guess = None
        for hi in holes:
            sm.close_open_images()

            if not self.isAlive():
                self.info('hole traverse canceled')
                break

            nominal_x, nominal_y = smap.map_to_calibration(hi.nominal_position,
                                                           center,
                                                           calibration.rotation)
            if dxs:
                dx, dy = dxs.mean(), dys.mean()
                guess = nominal_x - dx, nominal_y - dy

            npt, corrected = self._autocenter(hi, guess=guess)
            if not corrected:
                self.info('Failed to autocenter {}'.format(hi.id))
                npt = nominal_x, nominal_y

            dx = nominal_x - npt[0]
            dy = nominal_y - npt[1]
            dxs = hstack((dxs[-5:], dx))
            dys = hstack((dys[-5:], dy))

            res = Result(hole_id=hi.id, corrected=corrected,
                         dx=dx, dy=dy)
            results.append(res)
            points.append((npt, corrected))

        sm.close_open_images()

        # display the results
        sv = StageVisualizer()
        sv.results = results
        sv.set_stage_map(self.stage_map, points, calibration)

        invoke_in_main_thread(open_view, sv)

        # reset calibration manager
        self.calibration_step = 'Calibrate'

    def _autocenter(self, hi, guess=None):
        sm = self.stage_manager
        if guess is None:
            x, y = hi.x, hi.y
            # move to nominal hole position
            sm.linear_move(x, y, use_calibration=True, block=True)
        else:
            x, y = guess
            sm.linear_move(x, y, use_calibration=False, block=True)
        # delay for image refresh
        time.sleep(0.5)
        # autocenter
        npt, corrected, interp = sm.autocenter(holenum=hi.id, save=True,
                                               inform=False,
                                               alpha_enabled=False,
                                               auto_close_image=False)
        return npt, corrected

    def isAlive(self):
        return self._alive

    def _check_auto_calibration(self):
        smap = self.stage_map
        l = smap.get_calibration_hole('west')
        r = smap.get_calibration_hole('east')

        return l is not None or r is not None


class AutoCalibrator(TrayCalibrator):
    """
        1a. move to center position automatically
         b. autocenter
        2a. move to right position automatically
         b. autocenter
    """

# ============= EOF =============================================
