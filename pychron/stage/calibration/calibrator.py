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
from __future__ import absolute_import
from traits.api import Str, Float, Event, Bool

# ============= standard library imports ========================
import six.moves.cPickle as pickle
import os

# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths

SIMPLE_HELP = """1. Locate center hole
2. Locate right hole
"""


class BaseCalibrator(Loggable):
    calibration_step = Str
    rotation = Float
    save_event = Event
    _alive = False
    calibration_enabled = Bool(True)

    def isAlive(self):
        return self._alive

    def cancel(self):
        self._alive = False
        self.calibration_step = "Calibrate"

    def save(self, obj):
        p = self._get_path(self.name)
        with open(p, "wb") as f:
            pickle.dump(obj, f)

    def handle(self, step, x, y, canvas):
        raise NotImplementedError

    @classmethod
    def load(cls, name):
        path = cls._get_path(name)
        #        print os.path.isfile(path), path
        if os.path.isfile(path):
            with open(path, "rb") as f:
                try:
                    obj = pickle.load(f)
                    return obj
                except (
                        pickle.PickleError,
                        EOFError,
                        AttributeError,
                        UnicodeDecodeError,
                ) as e:
                    pass
                    #                    cls.debug(e)

    @classmethod
    def _get_path(cls, name):
        return os.path.join(paths.hidden_dir, "{}_stage_calibration".format(name))

    def traits_view(self):
        from traitsui.api import View

        return View()


class LinearCalibrator(BaseCalibrator):
    def handle(self, step, x, y, canvas):
        if step == "Calibrate":
            canvas.new_calibration_item()
            return dict(calibration_step="Locate Origin")
        # return 'Locate Center', None, None, None, 1
        elif step == "Locate Origin":
            canvas.calibration_item.set_center(x, y)
            return dict(calibration_step="Calibrate", cx=x, cy=y, rotation=0)
            #            return 'Locate Right', x, y, None, 1
            #         elif step == 'Locate Right':
            #             canvas.calibration_item.set_right(x, y)
            #             self.save(canvas.calibration_item)
            # #            return 'Calibrate', None, None, canvas.calibration_item.rotation, 1
            #             return dict(calibration_step='Calibrate',
            #                         rotation=canvas.calibration_item.rotation)


class BaseTrayCalibrator(BaseCalibrator):
    _clear_corrections = True

    def handle(self, step, x, y, canvas):
        print(step, x, y)
        if step == "Calibrate":
            canvas.new_calibration_item()
            return dict(calibration_step="Locate Center", clear_corrections=self._clear_corrections)
        elif step == "Locate Center":
            canvas.calibration_item.set_center(x, y)
            return dict(calibration_step="Locate Right", cx=x, cy=y, clear_corrections=self._clear_corrections)
        elif step == "Locate Right":
            canvas.calibration_item.set_right(x, y)
            self.save(canvas.calibration_item)
            self._save_hook(canvas.calibration_item)
            return dict(
                calibration_step="Calibrate", rotation=canvas.calibration_item.rotation,
                clear_corrections=self._clear_corrections
            )

    def _save_hook(self, ca):
        pass


class TrayCalibrator(BaseTrayCalibrator):
    pass


class SemiAutoCorrectionCalibrator(BaseTrayCalibrator):
    _clear_corrections = False

    def _save_hook(self, ca):
        #print('vaasd', ca, ca.center, canvas.nominal_center)
        # update the correction affine file
        sm = self.stage_map

        ch = self.stage_map.get_calibration_hole('center')
        nx, ny = ch.corrected_position
        sm.update_correction_affine_file((-nx+ca.center[0],
                                          -ny+ca.center[1]), ca.rotation)

# ============= EOF =============================================
