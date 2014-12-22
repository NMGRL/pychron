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
# from traitsui.api import View, Item  # , TableEditor
# import apptools.sweet_pickle as pickle
# ============= standard library imports ========================
from numpy import polyval
# ============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable


# class CalibrationPoint(HasTraits):
#     zoom = Float(enter_set=True, auto_set=False)
#     pxpercm = Float(enter_set=True, auto_set=False)
#     pxpercmx = Float
#     pxpercmy = Float
#     z = Float
#
#
# class CalibrationData(HasTraits):
#     calibration_points = List(CalibrationPoint)
#
#     xcoeff_str = String(enter_set=True, auto_set=False)
#     ycoeff_str = String(enter_set=True, auto_set=False)
#     graph = Any
#
#     def get_xcoeffs(self):
#         return map(float, self.xcoeff_str.split(','))
#
#     def get_ycoeffs(self):
#         return map(float, self.ycoeff_str.split(','))
#
#     def _coeff_str_changed(self):
#         g = self.graph
#         xs, ys = self._get_poly_data()
#         g.set_data(xs, series=4)
#         g.set_data(ys, series=4, axis=1)
#
#     def _graph_default(self):
#         from pychron.graph.regression_graph import RegressionGraph
#
#         g = RegressionGraph()
#         g.new_plot()
#         xs, ys = self._get_data()
#         g.new_series(x=xs, y=ys)
#
#         xs, ys = self._get_poly_data()
#         g.new_series(x=xs, y=ys, regress=False)
#         return g
#
#     def _get_poly_data(self):
#         i = np.linspace(0, 100, 100)
#         xs = np.polyval(self.get_xcoeffs(), i)
#         ys = np.polyval(self.get_ycoeffs(), i)
#         return i, xs, ys
#
#     def _calibration_points_default(self):
#         coeffs = [1, 0]
#         return [CalibrationPoint(zoom=i, pxpercm=np.polyval(coeffs, i)) for i in range(0, 110, 10)]
#
#     def load(self):
#         with open(self.path, 'rb') as f:
#             _obj = pickle.load(f)
#
#     def dump(self):
#         with open(self.path, 'wb') as f:
#             pickle.dump(self, f)
#
#     def _get_data(self):
#
# #        xs = [ci.zoom for ci in self.calibration_points]
# #        ys = [ci.pxpercm for ci in self.calibration_points]
#
#         return zip(*[(ci.zoom, ci.pxpercm) for ci in self.calibration_points])
# #        return xs, ys
#
#     def traits_view(self):
# #        cols = [
# #              ObjectColumn(name = 'zoom'),
# #              ObjectColumn(name = 'pxpercm')
# #              ]
# #        editor = TableEditor(columns = cols)
#         v = View(
#                  Item('xcoeff_str', show_label=False),
# #                 HGroup(Item('calibration_points', editor = editor,
# #                             width = 0.15,
# #                             show_label = False
# #                        ),
#                         Item('graph', show_label=False, style='custom',
#                              width=.85),
#
#                  width=700,
#                  height=600,
#                  resizable=True
#                  )
#         return v


class Camera(ConfigLoadable):
    '''
    '''
    parent = Any
#    calibration_data = Array
    ratio = Float
    current_position = Tuple
    fit_degree = Int
    width = Float(1)
    height = Float(1)
    pxpercm = Float

    swap_rb = Bool(True)
    vflip = Bool(False)
    hflip = Bool(False)
#     calibration_data = Instance(CalibrationData, ())
    focus_z = Float
    fps = Int
    zoom_coefficients = Str

#     def save_focus(self):
#         self.info('saving focus position to {}'.format(self.config_path))
#         config = self.get_configuration(self.config_path)
#         config.set('General', 'focus', self.focus_z)
#         self.write_configuration(config, self.config_path)

    def save_calibration(self):
        '''
             only has to update the coeff str in config file
        '''
        self.info('saving px per mm calibration to {}'.format(self.config_path))
        config = self.get_configuration(self.config_path)

        if not config.has_section('Zoom'):
            config.add_section('Zoom')
        config.set('Zoom', 'coefficients', self.zoom_coefficients)
#                    self.calibration_data.xcoeff_str)
#         config.set('General', 'ycoefficients', self.calibration_data.ycoeff_str)
        self.write_configuration(config, self.config_path)

    def load(self, p):
        '''
        '''
        self.config_path = p
        config = self.get_configuration(self.config_path)
        self.set_attribute(config, 'swap_rb', 'General', 'swap_rb', cast='boolean')
#        self.set_attribute(config, 'mirror', 'General', 'mirror', cast='boolean')
        self.set_attribute(config, 'vflip', 'General', 'vflip', cast='boolean')
        self.set_attribute(config, 'hflip', 'General', 'hflip', cast='boolean')

        self.set_attribute(config, 'width', 'General', 'width', cast='int')
        self.set_attribute(config, 'height', 'General', 'height', cast='int')
        self.set_attribute(config, 'focus_z', 'General', 'focus', cast='float')

        self.set_attribute(config, 'fps', 'General', 'fps', cast='int', default=12)

        self.set_attribute(config, 'zoom_coefficients', 'Zoom', 'coefficients',
                           default='1,0,23'
                           )
        self.set_attribute(config, 'zoom_fitfunc', 'Zoom', 'fitfunc',
                           default='polynomial')

#         cxs = self.config_get(config, 'General', 'xcoefficients')
#         cys = self.config_get(config, 'General', 'ycoefficients')

#         self.calibration_data.xcoeff_str = cxs
#         self.calibration_data.ycoeff_str = cys

#     def add_calibration_point(self, zoom, z, px, py):
#         self.calibration_data.calibration_points.append(CalibrationPoint(zoom=zoom,
#                                                                          z=z,
#                                                                          pxpercm=px,
#                                                                          pxpercmx=px,
#                                                                          pxpercmy=py,
#
#                                                                          ))

    def calculate_pxpermm(self, zoom):
#     def _calculate_pxpermm(self, zoom):
        if self.zoom_fitfunc == 'polynomial':
            func = polyval
        else:
            ff = 'lambda p,x: {}'.format(self.zoom_fitfunc)
            func = eval(ff)

        if self.zoom_coefficients:
    #         print func, self.zoom_fitfunc
            pxpermm = func(map(float, self.zoom_coefficients.split(',')), zoom)
        else:
            pxpermm = 1

        return pxpermm

    def set_limits_by_zoom(self, zoom, cx, cy, canvas=None):
        '''
        '''
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

#         cdata = self.calibration_data
#         xpx_per_cm = np.polyval(cdata.get_xcoeffs(), [zoom])[0]
#         ypx_per_cm = np.polyval(cdata.get_ycoeffs(), [zoom])[0]

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
#    def reset_calibration_data(self):
#
#        self.calibration_data = np.array([[], []])
# #
#    def add_calibration_datum(self, zoom, pxpercm):
#        x = self.calibration_data[0]
#        if zoom in x:
#            i = np.where(x == zoom)[0][0]
#            self.calibration_data[0][i] = zoom
#            self.calibration_data[1][i] = pxpercm            #self.calibration_data[2][i] = px_height
#        else:
#
#            x = np.hstack((self.calibration_data[0], [zoom]))
#            pw = np.hstack((self.calibration_data[1], [pxpercm]))
#            #h = hstack((self.calibration_data[2], [px_height]))
#            self.calibration_data = np.vstack((x, pw))
#
#    def save_calibration_data(self, path = None):
#        if path is None:
#            path = os.path.join(canvas2D_dir, 'camera.txt')
#
#        self.info('saving calibration data to {}'.format(path))
#        lines = []
#
#        x, y = self.calibration_data
#
#        x = [str(i) for i in x]
#        y = [str(int(i)) for i in y]
#        #y2 = ['%s' % i for i in y2]
#        data = np.transpose((x, y))
#
#        with open(path, 'r') as f:
#            #read until at calibration data
#            while 1:
#                line = f.next()
#                lines.append(line)
#                if line.startswith('#zoom'):
#                    break
#
#        with open(path, 'w') as f:
#            for pline in lines:
#                f.write(pline)
#
#            for d in data:
#                f.write(','.join(d) + '\n')
