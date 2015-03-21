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
from traits.api import Float, Enum, Str
from traitsui.api import Item, HGroup, VGroup
# ============= standard library imports ========================
import os
from numpy import linspace, polyval, polyfit, array
# ============= local library imports  ==========================
from pychron.database.core.database_selector import DatabaseSelector
from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.database.orms.power_calibration_orm import PowerCalibrationTable
from pychron.database.core.base_db_result import DBResult
from pychron.database.core.query import PowerCalibrationQuery

FITDEGREE = dict(Linear=1, Parabolic=2, Cubic=3)
class PowerCalibrationResult(DBResult):
    title_str = 'PowerCalibrationRecord'
    request_power = Float
    exportable = True
    fit = Enum('Linear', 'Parabolic', 'Cubic')
    coeffs = Str
    bounds = None
    calibration_bounds = None
    coefficients = None

    def _fit_changed(self):
        g = self.graph
        x = g.get_data()
        y = g.get_data(axis=1)

        coeffs, x, y = self._calculate_fit(x, y)
        self._set_coeffs(coeffs)

        g.set_data(x, series=1)
        g.set_data(y, series=1, axis=1)
        g.redraw()

    def _get_graph_item(self):
        g = super(PowerCalibrationResult, self)._get_graph_item()
#        g.height = 1.0
#        g.springy = True
        return VGroup(
                         HGroup(Item('fit', show_label=False),
                             Item('coeffs', style='readonly'),
#                             spring
                             ),
                      g,
#                      springy=True,
#                      label='Graph'
                      )

    def _apply_bounds(self, x, y):
        bounds = self.bounds
        if bounds:
            ox = array(x)
            y = array(y)
            x = ox[(ox > bounds[0]) & (ox < bounds[1])]
            y = y[(ox > bounds[0]) & (ox < bounds[1])]
        return x, y

    def _calculate_fit(self, x, y, deg=None):
        if deg is None:
            deg = FITDEGREE[self.fit]

        rxi = linspace(min(x), max(x), 500)
        x, y = self._apply_bounds(x, y)

        coeffs = polyfit(x, y, deg)
        ryi = polyval(coeffs, rxi)
#        ryi = polyval(coeffs, x)
        return coeffs, rxi, ryi

    def get_data(self):
        dm = self.data_manager
        calibration = dm.get_table('calibration', '/')
#        x = linspace(0, 100)
#        y = 0.01 * x ** 2 - 5
#        return x, y
        x, y = zip(*[(r['setpoint'], r['value']) for r in calibration.iterrows()])
#        return self._apply_bounds(x, y)
        return x, y

    def load_graph(self, graph=None, new_plot=True, *args, **kw):
        if graph is None:
            graph = self._graph_factory()

#        dm = self.data_manager
#        calibration = dm.get_table('calibration', '/')
        if new_plot:
            graph.new_plot(xtitle='Setpoint (%)',
                       ytitle='Measured Power (W)',
                       padding=[50, 10, 10, 40],
                       zoom=True,
                       pan=True
                       )
        xi, yi = self.get_data()
#        xi, yi = zip(*[(r['setpoint'], r['value']) for r in calibration.iterrows()])
        color = graph.get_next_color(exclude='red')
        graph.new_series(*self._apply_bounds(xi, yi),
                         color=color
                         )

        coeffs, rxi, ryi = self._calculate_fit(xi, yi)
        self._set_coeffs(coeffs)
        graph.new_series(rxi, ryi, color='red',
                         line_style='dash'
                         )

#        self.summary = 'coeffs ={}'.format(', '.join(['{:0.3f}'.format(c) for c in coeffs]))

        self.graph = graph

    def _set_coeffs(self, coeffs):
        self.coefficients = coeffs
        alpha = 'abcde'
        self.coeffs = ', '.join(['{}={:0.3f}'.format(a, c) for a, c in zip(alpha, coeffs)])

    def _load_hook(self, dbr):
        data = os.path.join(self.directory, self.filename)
        dm = H5DataManager()
        if os.path.isfile(data):
            dm.open_data(data)

        self.data_manager = dm


class PowerCalibrationSelector(DatabaseSelector):
#    parameter = String('PowerCalibrationTable.rundate')
    query_table = PowerCalibrationTable
    query_klass = PowerCalibrationQuery
#    record_klass = PowerCalibrationResult
    title = 'Power Calibration'

    def _get_selector_records(self, **kw):
        return self._db.get_calibration_records(**kw)

if __name__ == '__main__':
    p = PowerCalibrationResult(directory='/Users/ross/Sandbox',
                               filename='power_calibration004.hdf5')
    p.load()
    p.initialize()
    p.load_graph()
    p.configure_traits()
# ============= EOF =============================================
