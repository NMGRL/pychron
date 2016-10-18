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
import os
import time
from threading import Thread

from numpy import array, hstack, average
from traits.api import Instance, HasTraits, Str, Bool, Float

from pychron.core.helpers.filetools import pathtolist
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.view_util import open_view
from pychron.lasers.stage_managers.stage_visualizer import StageVisualizer
from pychron.stage.calibration.calibrator import TrayCalibrator


class Result(HasTraits):
    hole_id = Str
    corrected = Bool
    dx = Float
    dy = Float
    nx = Float
    ny = Float


class SemiAutoCalibrator(TrayCalibrator):
    """
        1a. user move to center
         b. record position
        2a. user move to right
         b. record position
        3. traverse holes finding autocenter position
    """

    stage_map = Instance('pychron.stage.maps.base_stage_map.BaseStageMap')

    def handle(self, step, x, y, canvas):
        ret = None
        if step == 'Calibrate':
            self.stage_map.clear_correction_file()
            canvas.new_calibration_item()
            self.calibration_step = 'Locate Center'
        elif step == 'Locate Center':
            canvas.calibration_item.set_center(x, y)

            # check stage map has at least one calibration hole.
            # if not issue warning and ask for manual locate right
            if self._check_auto_calibration():
                self.calibration_step = 'Auto Calibrate'
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
            self.calibration_enabled = False
            # self.calibration_step = 'Cancel'
        elif step == 'Traverse':
            if self.confirmation_dialog('Start Autocentering Traverse'):
                self._alive = True
                t = Thread(target=self._traverse,
                           args=(canvas.calibration_item,))
                t.start()
                self.calibration_enabled = False
                # self.calibration_step = 'Cancel'
            else:
                self.calibration_step = 'Calibrate'
                self.calibration_enabled = True

        return ret

    def _auto_calibrate(self, calibration):
        smap = self.stage_map

        rrot = lrot = None
        # locate right
        if self._alive:
            east = smap.get_calibration_hole('east')
            if east is not None:
                center = smap.get_calibration_hole('center')
                if center is not None:
                    self.debug('walk out to locate east')
                    for hid in xrange(int(center.id) + 1, int(east.id), 2):
                        if not self._alive:
                            break
                        hole = smap.get_hole(hid)
                        npt, corrected = self._autocenter(hole)
                        if corrected:
                            rrot = calibration.calculate_rotation(*npt)
                            calibration.set_right(*npt)
                            self.debug('Calculated rotation= {}'.format(rrot))
                        self.stage_manager.close_open_images()

                if self._alive:
                    self.debug('Locate east {}'.format(east.id))
                    npt, corrected = self._autocenter(east)
                    if corrected:
                        rrot = calibration.calculate_rotation(*npt)
                        calibration.set_right(*npt)
                        self.debug('Calculated rotation= {}'.format(rrot))
                self.stage_manager.close_open_images()

        # locate left
        if self._alive:
            hole = smap.get_calibration_hole('west')
            if hole is not None:
                self.debug('Locate west {}'.format(hole.id))
                npt, corrected = self._autocenter(hole)
                if corrected:
                    lrot = calibration.calculate_rotation(*npt, sense='west')
                    self.debug('Calculated rotation= {}'.format(lrot))
                self.stage_manager.close_open_images()

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

            # move back to center hole
            center = self.stage_map.get_calibration_hole('center')
            if center:
                x, y = center.corrected_position if center.has_correction else center.nominal_position
                self.stage_manager.linear_move(x, y, block=True, force=True, use_calibration=False)
            else:
                self.warning('No calibration hole defined for "center" in Stage Map file {}'.format(
                    self.stage_map.file_path))

    def _traverse(self, calibration):
        """
            visit each hole in holes
            record autocenter position
            warn user about failures
        """
        sm = self.stage_manager
        smap = self.stage_map

        # holes = smap.row_ends(alternate=True)
        holes = list(smap.circumference_holes())
        holes.extend(smap.mid_holes())

        results = []
        points = []
        center = calibration.center

        dxs, dys = array([]), array([])
        guess = None
        weights = [1, 2, 3, 4, 5, 6]
        # holes = [smap.get_hole(1), smap.get_hole(3), smap.get_hole(5)]
        success = True
        non_corrected = 0
        for hi in holes:
            sm.close_open_images()

            if not self._alive:
                self.info('hole traverse canceled')
                break

            nominal_x, nominal_y = smap.map_to_calibration(hi.nominal_position,
                                                           center,
                                                           calibration.rotation)

            n = len(dxs)
            if n:
                lim = min(6, n)
                dx = average(dxs, weights=weights[:lim])
                dy = average(dys, weights=weights[:lim])
                guess = nominal_x - dx, nominal_y - dy

            npt, corrected = self._autocenter(hi, guess=guess)
            if not corrected:
                non_corrected += 1
                self.info('Failed to autocenter {}'.format(hi.id))
                npt = nominal_x, nominal_y

            if non_corrected > 5:
                invoke_in_main_thread(self.warning_dialog,
                                      '6 consecutive holes failed to autocenter. Autocalibration Canceled')
                success = False
                break
            else:
                non_corrected = -1

            non_corrected += 1

            dx = nominal_x - npt[0]
            dy = nominal_y - npt[1]
            dxs = hstack((dxs[-5:], dx))
            dys = hstack((dys[-5:], dy))

            res = Result(hole_id=hi.id, corrected=corrected,
                         dx=dx, dy=dy,
                         nx=nominal_x, ny=nominal_y)
            results.append(res)
            points.append((npt, corrected))

        sm.close_open_images()

        if success:
            smap.generate_row_interpolated_corrections()
            # display the results
            sv = StageVisualizer()
            sv.results = results
            sv.set_stage_map(self.stage_map, points, calibration)
            sv.save()

            invoke_in_main_thread(open_view, sv)

        # reset calibration manager
        self.calibration_step = 'Calibrate'
        self.calibration_enabled = True

    def _autocenter(self, hi, guess=None):
        self.debug('autocentering hole={}, guess={}'.format(hi.id, guess))
        sm = self.stage_manager
        kw = {'block': True, 'force': True}
        if guess is None:
            x, y = hi.x, hi.y
            # move to nominal hole position
            kw['use_calibration'] = True
        else:
            x, y = guess
            kw['use_calibration'] = False

        sm.linear_move(x, y, **kw)
        # delay for image refresh
        time.sleep(0.5)
        # autocenter
        npt, corrected, interp = sm.autocenter(holenum=hi.id, save=True,
                                               inform=False,
                                               alpha_enabled=False,
                                               auto_close_image=False)
        return npt, corrected

    def _check_auto_calibration(self):
        smap = self.stage_map

        l = smap.get_calibration_hole('west')
        r = smap.get_calibration_hole('east')

        return l is not None or r is not None


class AutoCalibrator(SemiAutoCalibrator):
    """
        1a. move to center position automatically
         b. autocenter
        2a. move to right position automatically
         b. autocenter
    """

    _warned = False

    def handle(self, step, x, y, canvas):

        center_guess = self._get_center_guess()
        center_hole = self.stage_map.get_calibration_hole('center')
        if not self._check_auto_calibration():
            if not self._warned:
                self.warning_dialog('Auto calibration not available. Stage map not properly configured')
                self._warned = True
            return super(AutoCalibrator, self).handle(step, x, y, canvas)

        if center_guess is None or center_hole is None:
            if not self._warned:
                self.warning_dialog('Center hole/Center guess not configured. Center hole={}, Guess={}'.format(
                    center_hole, center_guess))
                self._warned = True
            return super(AutoCalibrator, self).handle(step, x, y, canvas)
        else:
            ret = None
            if step == 'Calibrate':
                self.stage_map.clear_correction_file()
                canvas.new_calibration_item()
                self.calibration_enabled = False

                self._alive = True
                t = Thread(target=self._auto_calibrate,
                           args=(canvas.calibration_item, center_hole, center_guess))
                t.start()
            return ret

    def _auto_calibrate(self, calibration, center_hole, center_guess):
        npos, corrected = self._autocenter(center_hole, center_guess)
        if not corrected:
            invoke_in_main_thread(self.warning_dialog, 'Failed to located center hole. Try SemiAutoCalibration')
            self._warned = False
            self.calibration_step = 'Calibrate'
            self.calibration_enabled = True
        else:
            super(AutoCalibrator, self)._auto_calibrate(calibration)

    def _get_center_guess(self):
        path = self.stage_map.center_guess_path

        if os.path.isfile(path):
            try:
                guess = pathtolist(path)
                return map(float, guess[0].split(','))
            except BaseException, e:
                self.debug('Failed parsing center guess file {}. error={}'.format(path, e))

# ============= EOF =============================================
