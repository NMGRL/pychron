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
from traits.api import Float, Event, String, Any, Enum, Button, List, Instance
# ============= standard library imports ========================
import shutil
import cPickle as pickle
import os
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.stage.calibration.auto_calibrator import SemiAutoCalibrator
from pychron.stage.calibration.free_calibrator import FreeCalibrator
from pychron.stage.calibration.calibrator import TrayCalibrator, \
    LinearCalibrator, BaseCalibrator
from pychron.paths import paths
from pychron.stage.calibration.hole_calibrator import HoleCalibrator

TRAY_HELP = '''1. Locate center hole
2. Locate right hole
'''

HELP_DICT = {
    'Free': '''1. Move to Point, Enter Reference Position. Repeat at least 2X
2. Hit End Calibrate to finish and compute parameters
''',
    'Hole': '''1. Move to Hole, Enter Reference hole. Repeat at least 2X
2. Hit End Calibrate to finish and compute parameters''',
    'Linear': '1. Locate Origin (i.e. 0)'

}

STYLE_DICT = {'Free': FreeCalibrator,
              'Hole': HoleCalibrator,
              'Linear': LinearCalibrator,
              'SemiAuto': SemiAutoCalibrator}


def get_hole_calibration(name, hole):
    root = os.path.join(paths.hidden_dir, '{}_calibrations'.format(name))
    if os.path.isdir(root):
        hole = int(hole)
        for pp in os.listdir(root):
            with open(os.path.join(root, pp), 'rb') as rfile:
                _, holes, ca = pickle.load(rfile)
                if hole in holes:
                    return ca


class TrayCalibrationManager(Loggable):
    x = Float
    y = Float
    rotation = Float
    scale = Float
    error = Float

    calibrate = Event
    calibration_step = String('Calibrate')
    calibration_help = String(TRAY_HELP)
    style = Enum('Tray', 'Free', 'Hole', 'Linear', 'SemiAuto')
    canvas = Any
    calibrator = Instance(BaseCalibrator)
    # calibrator = Property(depends_on='style')

    add_holes_button = Button
    reset_holes_button = Button
    holes_list = List

    def isCalibrating(self):
        return self.calibration_step != 'Calibrate'

    def load_calibration(self, stage_map=None):
        if stage_map is None:
            stage_map = self.parent.stage_map_name

        self.debug('loading calibration for {}'.format(stage_map))

        self._load_holes_calibrations(stage_map)

        calobj = TrayCalibrator.load(stage_map)
        if calobj is not None:
            try:
                self.x, self.y = calobj.cx, calobj.cy
                self.rotation = calobj.rotation
                self.scale = calobj.scale
                self.style = calobj.style
            except AttributeError:
                self.debug('calibration file is an older incompatible version')
                return

            self.canvas.calibration_item = calobj
            # force style change update
            self._style_changed()

    def save_calibration(self, name=None, clear_corrections=True):
        pickle_path = os.path.join(paths.hidden_dir, '{}_stage_calibration')
        if name is None:
            # delete the corrections file
            name = self.parent.stage_map_name

        ca = self.canvas.calibration_item
        if ca is not None:
            if clear_corrections:
                self.parent.stage_map.clear_correction_file()
            ca.style = self.style
            p = pickle_path.format(name)
            self.info('saving calibration {}'.format(p))
            with open(p, 'wb') as f:
                pickle.dump(ca, f)

            self.load_calibration(name)

    def _load_holes_calibrations(self, sm):
        self.holes_list = []
        root = os.path.join(paths.hidden_dir, '{}_calibrations'.format(sm))
        if os.path.isdir(root):
            for pp in os.listdir(root):
                with open(os.path.join(root, pp), 'rb') as rfile:
                    hs, _, _ = pickle.load(rfile)
                    self.holes_list.append(hs)

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _reset_holes_button_fired(self):
        name = self.parent.stage_map_name
        root = os.path.join(paths.hidden_dir, '{}_calibrations'.format(name))
        if os.path.isdir(root):
            shutil.rmtree(root)

        self.holes_list = []

    def _add_holes_button_fired(self):
        from pychron.stage.calibration.add_holes_view import AddHolesView
        ahv = AddHolesView()
        info = ahv.edit_traits(kind='livemodal')
        if info.result:
            name = self.parent.stage_map_name
            root = os.path.join(paths.hidden_dir,
                                '{}_calibrations'.format(name))
            if not os.path.isdir(root):
                os.mkdir(root)

            self.holes_list.append(ahv.hole_str)

            holes = ahv.holes
            p = os.path.join(root, ahv.holes_id)
            with open(p, 'wb') as wfile:
                ca = self.canvas.calibration_item
                pickle.dump((ahv.hole_str, holes, ca), wfile)

    def _style_changed(self):
        if self.style in HELP_DICT:
            self.calibration_help = HELP_DICT[self.style]
        else:
            self.calibration_help = TRAY_HELP

        self.calibrator = self._calibrator_factory()

    def _calibrate_fired(self):

        x, y = self.parent.get_current_position()
        self.rotation = 0

        kw = self.calibrator.handle(self.calibration_step,
                                    x, y, self.canvas)
        if kw:
            for a in ('calibration_step', 'cx', 'cy',
                      'scale', 'error', 'rotation'):
                if a in kw:
                    setattr(self, a, kw[a])

            cc = kw.get('clear_corrections', True)
            self.save_calibration(clear_corrections=cc)

    def _destroy_calibrator(self):
        if self.calibrator:
            self.calibrator.stage_manager = None
            self.calibrator.stage_map = None
            self.calibrator.on_trait_change(self._handle_step,
                                            'calibration_step', remove=True)
            self.calibrator.on_trait_change(self._handle_rotation,
                                            'rotation', remove=True)

    def _calibrator_factory(self):
        self._destroy_calibrator()

        kw = dict(name=self.parent.stage_map_name or '',
                  stage_manager=self.parent,
                  stage_map=self.parent.stage_map)

        if self.style in STYLE_DICT:
            klass = STYLE_DICT[self.style]
        else:
            klass = TrayCalibrator

        cal = klass(**kw)
        cal.on_trait_change(self._handle_step, 'calibration_step')
        cal.on_trait_change(self._handle_rotation, 'rotation')
        return cal

    def _handle_step(self, new):
        self.calibration_step = new

    def _handle_rotation(self, new):
        self.rotation = new
    # ===============================================================================
    # property get/set
    # ===============================================================================
        # @cached_property
        # def _get_calibrator(self):
        #     kw = dict(name=self.parent.stage_map_name or '',
        #               stage_manager=self.parent,
        #               stage_map=self.parent.stage_map)
        #
        #     if self.style in STYLE_DICT:
        #         klass = STYLE_DICT[self.style]
        #     else:
        #         klass = TrayCalibrator
        #
        #     return klass(**kw)

# ============= EOF =============================================
