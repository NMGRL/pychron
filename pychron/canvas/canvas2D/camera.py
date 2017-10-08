# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import  Bool, Any, Float, Tuple, Int, Str
# ============= standard library imports ========================
from numpy import polyval, exp
# ============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable


class Camera(ConfigLoadable):
    """
    """
    parent = Any
    ratio = Float
    current_position = Tuple
    fit_degree = Int
    width = Float(1)
    height = Float(1)
    pxpercm = Float

    swap_rb = Bool(True)
    vflip = Bool(False)
    hflip = Bool(False)
    focus_z = Float
    fps = Int
    zoom_coefficients = Str

    def save_calibration(self):
        """
             only has to update the coeff str in config file
        """
        self.info('saving px per mm calibration to {}'.format(self.config_path))
        config = self.get_configuration(self.config_path)

        if not config.has_section('Zoom'):
            config.add_section('Zoom')
        config.set('Zoom', 'coefficients', self.zoom_coefficients)
        self.write_configuration(config, self.config_path)

    def load(self, p):
        """
        """
        self.config_path = p
        config = self.get_configuration(self.config_path)
        self.set_attribute(config, 'swap_rb', 'General', 'swap_rb', cast='boolean')
        self.set_attribute(config, 'vflip', 'General', 'vflip', cast='boolean')
        self.set_attribute(config, 'hflip', 'General', 'hflip', cast='boolean')

        self.set_attribute(config, 'width', 'General', 'width', cast='int')
        self.set_attribute(config, 'height', 'General', 'height', cast='int')
        self.set_attribute(config, 'focus_z', 'General', 'focus', cast='float')

        self.set_attribute(config, 'fps', 'General', 'fps', cast='int', default=12)

        self.set_attribute(config, 'zoom_coefficients', 'Zoom', 'coefficients',
                           default='1,0,23')
        self.set_attribute(config, 'zoom_fitfunc', 'Zoom', 'fitfunc',
                           default='polynomial')

    def calculate_pxpermm(self, zoom):
        if self.zoom_fitfunc == 'polynomial':
            func = polyval
        else:
            ff = 'lambda p,x: {}'.format(self.zoom_fitfunc)
            func = eval(ff, {'exp': exp})

        if self.zoom_coefficients:
            pxpermm = func(map(float, self.zoom_coefficients.split(',')), zoom)
        else:
            pxpermm = 1

        return pxpermm

    def set_limits_by_zoom(self, zoom, cx, cy, canvas=None):
        """
        """
        def _set_limits(axis_key, px_per_mm, cur_pos, canvas):

            if axis_key == 'x':
                d = self.width
            else:
                d = self.height

            # scale to mm
            if canvas is None:
                canvas = self.parent

            if canvas:
                d /= 2.0 * px_per_mm
                lim = (-d + cur_pos, d + cur_pos)
                canvas.set_mapper_limits(axis_key, lim)

        pxpermm = self.calculate_pxpermm(zoom)
        _set_limits('x', pxpermm, cx, canvas)
        _set_limits('y', pxpermm, cy, canvas)
        return pxpermm

# if __name__ == '__main__':
#    c = Camera()
#    p = '/Users/fargo2/Pychrondata_beta/setupfiles/canvas2D/camera.txt'
#    c.save_calibration_data(p)
#     c = CalibrationData(xcoeff_str='1.1, 5')
#     c.configure_traits()

# ============= EOF ====================================

