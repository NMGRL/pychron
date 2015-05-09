# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Button, Bool, Any, List
from traitsui.api import Item, HGroup
# from pychron.core.ui.custom_label_editor import CustomLabel
# from pychron.core.geometry.geometry import calculate_reference_frame_center, calc_length
from traitsui.view import View
from pychron.lasers.stage_managers.calibration.calibrator import TrayCalibrator
from pychron.core.geometry.reference_point import ReferencePoint
from pychron.core.geometry.affine import calculate_rigid_transform
# ============= standard library imports ========================
# ============= local library imports  ==========================


class FreeCalibrator(TrayCalibrator):
    accept_point = Button
    finished = Button
    calibrating = Bool(False)

    manager = Any

    points = List
    append_current_calibration = Bool(False)

    # def get_controls(self):
    #
    def traits_view(self):
        cg = HGroup(Item('accept_point',
                         enabled_when='calibrating',
                         show_label=False),
                    Item('append_current_calibration',
                         label='Append Points',
                         tooltip='Should points be appended to the current calibration or a new calibration started?'
                         ))
        return View(cg)

    def handle(self, step, x, y, canvas):
        if step == 'Calibrate':
            self.calibrating = True
            if self.append_current_calibration:
                if not self.points:
                    self.points = []
                    canvas.new_calibration_item()
            else:
                canvas.new_calibration_item()
                self.points = []
            return dict(calibration_step='End Calibrate')
        # return 'End Calibrate', None, None, None, None, None

        elif step == 'End Calibrate':
            n = 0
            if self.points:
                n = len(self.points)

            if n < 3:
                d = None
                if self.confirmation_dialog('Need to enter at least 3 calibration points. Current NPoints: {}\n\n'
                                            'Are you sure you want to End calibration'.format(n)):
                    self.calibrating = False
                    d = dict(calibration_step='Calibrate')
                return d

            d = dict(calibration_step='Calibrate')
            self.calibrating = False

            refpoints, points = zip(*self.points)

            scale, theta, (tx, ty), err = calculate_rigid_transform(refpoints,
                                                                    points)

            # set canvas calibration
            ca = canvas.calibration_item
            ca.cx, ca.cy = tx, ty
            ca.rotation = theta
            ca.scale = 1 / scale
            d.update(dict(cx=tx, cy=ty, rotation=theta, scale=1 / scale, error=err
                          ))
            return d
            # return 'Calibrate', tx, ty, theta, 1 / scale, err
            # else:
            #                return dict(calibration_step='Calibrate')
            #                return 'Calibrate', None, None, None, None, None

    def _accept_point(self):
        sp = self.manager.get_current_position()
        npt = self._get_point(sp)
        if npt:
            self.points.append(npt)

    def _get_point(self, sp):
        rp = ReferencePoint(sp)
        info = rp.edit_traits()
        if info.result:
            refp = rp.x, rp.y
            return refp, sp

            # ===============================================================================
            # handlers
            # ===============================================================================

    def _accept_point_fired(self):
        self._accept_point()


# ============= EOF =============================================
