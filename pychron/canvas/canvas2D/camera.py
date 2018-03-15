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
from __future__ import absolute_import

import yaml
from numpy import polyval, exp
from traits.api import Float, Tuple, Int, Str, HasTraits

from pychron.config_loadable import ConfigLoadable
from pychron.loggable import Loggable


class BaseCamera(HasTraits):
    ratio = Float
    current_position = Tuple
    fit_degree = Int
    width = Float(1)
    height = Float(1)
    pxpercm = Float

    focus_z = Float
    zoom_coefficients = Str
    config_path = Str
    zoom_fitfunc = 'polynominal'

    def save_calibration(self):
        raise NotImplementedError

    def load(self, p):
        """
        """
        self.config_path = p
        config = self.get_configuration(self.config_path)

        self.set_attribute(config, 'width', 'General', 'width', cast='int')
        self.set_attribute(config, 'height', 'General', 'height', cast='int')
        self.set_attribute(config, 'focus_z', 'General', 'focus', cast='float')

        self.set_attribute(config, 'zoom_coefficients', 'Zoom', 'coefficients',
                           default='0,0,23')
        self.set_attribute(config, 'zoom_fitfunc', 'Zoom', 'fitfunc',
                           default='polynomial')

    def set_attribute(self, config, name, section, option, **kw):
        raise NotImplementedError

    def get_configuration(self, path):
        raise NotImplementedError

    def write_configuration(self, obj, path):
        raise NotImplementedError

    def calculate_pxpermm(self, zoom):
        if self.zoom_fitfunc == 'polynomial':
            func = polyval
        else:
            ff = 'lambda p,x: {}'.format(self.zoom_fitfunc)
            func = eval(ff, {'exp': exp})

        if self.zoom_coefficients:
            pxpermm = func(list(map(float, self.zoom_coefficients.split(','))), zoom)
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
            # if canvas is None:
            #     canvas = self.parent

            if canvas:
                d /= 2.0 * px_per_mm
                lim = (-d + cur_pos, d + cur_pos)
                canvas.set_mapper_limits(axis_key, lim)

        pxpermm = self.calculate_pxpermm(zoom)
        if cx is not None:
            _set_limits('x', pxpermm, cx, canvas)
        if cy is not None:
            _set_limits('y', pxpermm, cy, canvas)
        return pxpermm


class YamlCamera(Loggable, BaseCamera):
    def save_calibration(self):
        self.info('saving px per mm calibration to {}'.format(self.config_path))
        config = self.get_configuration(self.config_path)
        zoom = config.get('Zoom', {})
        zoom['coefficients'] = self.zoom_coefficients
        config['Zoom'] = zoom
        self.write_configuration(config, self.config_path)

    def set_attribute(self, config, name, section, option, default=None, **kw):
        sec = config.get(section)
        if sec:
            opt = sec.get(option, default)

            if opt is not None:
                setattr(self, name, opt)

    def get_configuration(self, path):
        with open(path, 'r') as rfile:
            return yaml.load(rfile)

    def write_configuration(self, obj, path):
        with open(path, 'w') as wfile:
            yaml.dump(obj, wfile, default_flow_style=False)


class Camera(ConfigLoadable, BaseCamera):
    """
    """

    def save_calibration(self):
        """
             only has to update the coeff str in config file
        """
        self.info('saving px per mm calibration to {}'.format(self.config_path))
        config = self.get_configuration(self.config_path)
        if config:
            if not config.has_section('Zoom'):
                config.add_section('Zoom')
            config.set('Zoom', 'coefficients', self.zoom_coefficients)
            self.write_configuration(config, self.config_path)
# if __name__ == '__main__':
#    c = Camera()
#    p = '/Users/fargo2/Pychrondata_beta/setupfiles/canvas2D/camera.txt'
#    c.save_calibration_data(p)
#     c = CalibrationData(xcoeff_str='1.1, 5')
#     c.configure_traits()

# ============= EOF ====================================
