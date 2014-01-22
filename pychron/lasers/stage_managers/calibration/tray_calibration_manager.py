#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Float, Event, String, Any, Enum, Property, cached_property
from traitsui.api import View, Item, VGroup, HGroup
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.lasers.stage_managers.calibration.free_calibrator import FreeCalibrator
from pychron.lasers.stage_managers.calibration.calibrator import TrayCalibrator
import os
from pychron.paths import paths
from pychron.lasers.stage_managers.calibration.hole_calibrator import HoleCalibrator

TRAY_HELP = '''1. Locate center hole
2. Locate right hole
'''

HELP_DICT = {
           'Free':'''1. Move to Point, Enter Reference Position. Repeat at least 2X
2. Hit End Calibrate to finish and compute parameters
''',
            'Hole':'''1. Move to Hole, Enter Reference hole. Repeat at least 2X
2. Hit End Calibrate to finish and compute parameters'''
            }

STYLE_DICT = {'Free':FreeCalibrator,
              'Hole':HoleCalibrator,
             }

class TrayCalibrationManager(Manager):
    x = Float
    y = Float
    rotation = Float
    scale = Float
    error = Float

    calibrate = Event
    calibration_step = String('Calibrate')
    calibration_help = String(TRAY_HELP)
    style = Enum('Tray', 'Free', 'Hole')
    canvas = Any
    calibrator = Property(depends_on='style')

    def isCalibrating(self):
        return self.calibration_step != 'Calibrate'

    def get_current_position(self):
        x = self.parent.stage_controller.x
        y = self.parent.stage_controller.y
        return x, y

    def load_calibration(self, stage_map=None):
        if stage_map is None:
            stage_map = self.parent.stage_map

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

    def save_calibration(self, name=None):
        PICKLE_PATH = p = os.path.join(paths.hidden_dir, '{}_stage_calibration')
        if name is None:
        # delete the corrections file
            name = self.parent.stage_map

        ca = self.canvas.calibration_item
        if  ca is not None:
            self.parent._stage_map.clear_correction_file()
            ca.style = self.style
            p = PICKLE_PATH.format(name)
            self.info('saving calibration {}'.format(p))
            with open(p, 'wb') as f:
                pickle.dump(ca, f)

    def get_additional_controls(self):
        return self.calibrator.get_controls()

    def traits_view(self):
        cg = VGroup(
                    Item('style', show_label=False, enabled_when='not object.isCalibrating()'),
                    self._button_factory('calibrate', 'calibration_step'),
                    HGroup(Item('x', format_str='%0.3f', style='readonly'),
                           Item('y', format_str='%0.3f', style='readonly')),
                    Item('rotation', format_str='%0.3f', style='readonly'),
                    Item('scale', format_str='%0.4f', style='readonly'),
                    Item('error', format_str='%0.2f', style='readonly')
                    )
        ad = self.get_additional_controls()
        if ad is not None:
            cg.content.append(ad)

        v = View(cg,
                 CustomLabel('calibration_help',
                            color='green',
                            height=75, width=300),
                )
        return v

#===============================================================================
# handlers
#===============================================================================
    def _style_changed(self):
        if self.style in HELP_DICT:
            self.calibration_help = HELP_DICT[self.style]
        else:
            self.calibration_help = TRAY_HELP

    def _calibrate_fired(self):
        '''
        '''
        x, y = self.get_current_position()
        self.rotation = 0

        args = self.calibrator.handle(self.calibration_step,
                                      x, y, self.canvas)
        if args:
            for a in ('calibration_step', 'cx', 'cy', 'scale', 'error', 'rotation'):
                if args.has_key(a):
                    setattr(self, a, args[a])
                    if a == 'rotation':
                        self.save_calibration()

#===============================================================================
# property get/set
#===============================================================================

    @cached_property
    def _get_calibrator(self):
        kw = dict(name=self.parent.stage_map or '',
                  manager=self)

        if self.style in STYLE_DICT:
            klass = STYLE_DICT[self.style]
        else:
            klass = TrayCalibrator

        if self.style == 'Hole':
            kw['stage_map'] = self.parent._stage_map

        return klass(**kw)
#============= EOF =============================================
