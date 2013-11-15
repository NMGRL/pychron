#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Any, Int, Instance, Event
from traitsui.api import View, Item
from pychron.loggable import Loggable
import time
#============= standard library imports ========================
#============= local library imports  ==========================
from numpy import exp, mgrid, linspace, hstack, array, rot90
from pychron.helpers.datetime_tools import generate_datestamp
from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.consumer_mixin import ConsumerMixin
import random
from scipy.interpolate.ndgriddata import griddata
from pychron.graph.contour_graph import ContourGraph
from pychron.graph.graph import Graph
from chaco.plot_containers import HPlotContainer
from pychron.paths import paths
# from pychron.ui.gui import invoke_in_main_thread


def power_generator(nsteps):
    '''
    '''
    def gaussian(height, center_x, center_y, width_x, width_y):
        '''
        Returns a gaussian function with the given parameters
        '''

        width_x = float(width_x)
        width_y = float(width_y)
        return lambda x, y: height * exp(
 -(((center_x - x) / width_x) ** 2 + ((center_y - y) / width_y) ** 2) / 2)

    x, y = mgrid[0:nsteps, 0:nsteps]
    data = gaussian(2, 5, 5, 5, 5)(x, y)  # +np.random.random(x.shape)
    i = 0
    j = 0
    while 1:
        yield data[i][j]
        j += 1
        if j == nsteps:
            i += 1
            j = 0


class PowerMapper(Loggable, ConsumerMixin):
    laser_manager = Any
    canvas = Any
    graph = Any
    nintegrations = Int(5)
    data_manager = Instance(H5DataManager, ())

    _alive = False
    completed = Event
    def make_component(self, padding):
        cg = ContourGraph()

        cg.new_plot(title='Beam Space',
                    xtitle='X mm',
                    ytitle='Y mm',
                    aspect_ratio=1
                    )

        g = Graph()
        g.new_plot(title='Motor Space',
                     xtitle='X mm',
                     ytitle='Power',
                     )
        g.new_series(
                     )

        self.graph = g
        self.contour_graph = cg
        c = HPlotContainer()
        c.add(g.plotcontainer)
        c.add(cg.plotcontainer)

        return c

    def stop(self):
        self._alive = False
        lm = self.laser_manager
        if lm:
            lm.set_laser_power(0)
            lm.disable_device()

            sm = lm.stage_manager
            sm.stop()

        dm = self.data_manager
        if dm:
            dm.close_file()

    def do_power_mapping(self, bd, rp, cx, cy, padding, step_len):
        self._padding = padding
        self._beam_diameter = bd
        self._power = rp
        xl, xh = cx - padding, cx + padding
        yl, yh = cy - padding, cy + padding
        self._bounds = [xl, xh, yl, yh]

        xi = linspace(-padding, padding, 25)
        yi = linspace(-padding, padding, 25)
        X = xi[None, :]
        Y = yi[:, None]

        self.area = (X, Y)
        self.info('executing power map')
        self.info('beam diameter={} request_power={}'.format(bd, rp))

        lm = self.laser_manager
        if lm is not None:
            self.setup_consumer(func=self._add_data)
            self._alive = True
            # enable the laser
            lm.enable_laser()

            lm.set_motor('beam', bd, block=True)

            lm.set_laser_power(rp)
            discrete = False
            if discrete:
                self._discrete_scan(cx, cy, padding, step_len)
            else:
                self._continuous_scan(cx, cy, padding, step_len)

            self.stop()

            self.completed = True
            self._measure_properties()

            # stop the consumer
            self._should_consume = False

        else:
            self.warning_dialog('No Laser Manager available')

    def _add_data(self, data):


#        def _refresh_data(v):
        tab, x, y, col, row, mag, sid = data

#        self.debug('{} {} {} {} {}'.format(*v[1:]))
        self._write_datum(tab, x, y, col, row, mag)
        self.graph.add_datum((x, mag), series=sid)

        self._xs = hstack((self._xs, x))
        self._ys = hstack((self._ys, y))
        self._zs = hstack((self._zs, mag))

#         xl, xh = self._bounds[:2]
#         yl, yh = self._bounds[2:]

        if col % 10 == 0 and row:
            cg = self.contour_graph
            xx = self._xs
            yy = self._ys
            z = self._zs

#             print 'xx-----', xx
#             print 'yy-----', yy
            zd = griddata((xx, yy), z, self.area,
#                        method='cubic',
                        fill_value=0)

            zd = rot90(zd, k=2)
#             zd = zd.T
#             print zd
            if not cg.plots[0].plots.keys():
                cg.new_series(z=zd,
                              xbounds=(-self._padding, self._padding),
                              ybounds=(-self._padding, self._padding),
#                              xbounds=(xl, xh),
#                              ybounds=(yl, yh),
                              style='contour')
            else:
                cg.plots[0].data.set_data('z0', zd)

#        invoke_in_main_thread(_refresh_data, data)

    def _continuous_scan(self, cx, cy, padding, step_len):
        self.info('doing continuous scan')

        _nrows, row_gen = self._row_generator(cx, cy, padding, step_len)
        endpt_gen = self._endpoints_generator(cx, padding)

        lm = self.laser_manager
        sm = lm.stage_manager
        apm = lm.get_device('analog_power_meter')
        self._xs, self._ys, self._zs = array([]), array([]), array([])
        tab = self._new_data_table(padding)

        sc = sm.stage_controller
        while 1:
            if not self._alive:
                self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%%% not alive')
                break
            try:
                row, ny = row_gen.next()
            except StopIteration:
                self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%% Stop iteration1')
                break
            try:
                sx, ex = endpt_gen.next()
            except StopIteration:
                self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%% Stop iteration2')
                break

            self.info('move to start {},{}'.format(sx, ny))
            # move to start position
            sc.linear_move(sx, ny, block=True)

            self.graph.new_series(color='black')
            sid = len(self.graph.series[0]) - 1

            # move to start position
            self.info('move to end {},{}'.format(ex, ny))
            sc.linear_move(ex, ny, block=False, velocity=0.1, immediate=True)
            time.sleep(0.1)
#             if lm.simulation:
#                 n = 21
#                 r = random.random()
#                 if r < 0.25:
#                     n += 1
#                 elif r > 0.75:
#                     n -= 1
#                 for i in range(n):
#                     x, y = i * 0.1 - 1, ny
#                     mag = row + random.random()
#                     self.add_consumable((tab, x, y, i, row, mag, sid))
#             else:
            xaxis = sc.axes['x']
            yaxis = sc.axes['y']
            col = 0
            p = sc.timer.get_interval()
            self.debug('power map timer {}'.format(p))
            while 1:
#                self.debug('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ power map iteration {}'.format(p))
                time.sleep(p)
                x, y = xaxis.position - cx, yaxis.position - cy
                if apm:
                    mag = apm.read_power_meter(verbose=False)
                else:
                    mag = row + random.random()

#                self.debug('x={}, y={}'.format(x, y))
                v = (tab, x, y, col, row, mag, sid)
                if not sc.timer.isActive():
                    self.debug('%%%%%%%%%%%%%%%%%%%%%% timer not active')
                    self.add_consumable(v)
                    break
                else:
                    self.add_consumable(v)
                    col += 1

            self.debug('row {} y={} complete'.format(row, ny))

        self.debug('scan complete')

    def _endpoints_generator(self, cx, padding):
        def gen():
            a = True
            while 1:
                s, e = cx + padding, cx - padding
                yield s, e if a else e, s

        return gen()

    def _row_generator(self, cx, cy, padding, step_len):
        nsteps = int(padding / step_len)
#        ysteps = xrange(-nsteps, nsteps + 1)
        ysteps = xrange(nsteps + 1, -nsteps, -1)

        self.graph.set_x_limits(-padding, padding, pad='0.1')
        def gen():
            for j, yi in enumerate(ysteps):
                ny = (yi * step_len) + cy
                yield j, ny
        return nsteps, gen()

    def _step_generator(self, cx, cy, padding, step_len):
        nsteps = int(padding / step_len)
        xsteps = xrange(-nsteps, nsteps + 1)
        ysteps = xrange(-nsteps, nsteps + 1)

        self.canvas.set_parameters(xsteps, ysteps)
        self.canvas.request_redraw()

        def gen():
            for j, yi in enumerate(ysteps):
                ny = (yi * step_len) + cy
                for i, xi in enumerate(xsteps):
                    nx = (xi * step_len) + cx
                    yield i, nx, j, ny

        return len(xsteps), gen()

    def _measure_properties(self):
        pass
#===============================================================================
# data
#===============================================================================
    def _new_data_table(self, padding):
        dm = self.data_manager
#        root = '/usr/local/pychron/powermaps'
#         dw = DataWarehouse(root=paths.powermap_db_root)
#                           root=os.path.join(paths.co2laser_db_root, 'power_map'))
#                           os.path.join(data_dir, base_dir))
#         dw.build_warehouse()
        dm.new_frame(base_frame_name='powermap-{}'.format(generate_datestamp()),
                     directory=paths.power_map_dir
                     )
        t = dm.new_table('/', 'power_map', table_style='PowerMap')
        t._v_attrs['bounds'] = padding
        t._v_attrs['beam_diameter'] = self._beam_diameter
        t._v_attrs['power'] = self._power
        return t

    def _write_datum(self, tab, nx, ny, c, r, mag):
        nr = tab.row
        nr['col'] = c
        nr['row'] = r
        nr['x'] = nx
        nr['y'] = ny
        nr['power'] = mag
        nr.append()
        tab.flush()
#===============================================================================
# discrete
#===============================================================================
def _discrete_scan(self, cx, cy, padding, step_len):
        self.info('doing discrete scan')
        nsteps, step_gen = self._step_generator(cx, cy, padding, step_len)

        lm = self.laser_manager
        sm = lm.stage_manager
        apm = lm.get_device('analog_power_meter')

        if lm.simulation:
            pgen = power_generator(nsteps)

        tab = self._new_data_table(padding)

        while 1:
            if not self._alive:
                break
            try:
                col, nx, row, ny = step_gen.next()
            except StopIteration:
                break

            if lm.simulation:
                mag = pgen.next()
            else:
                sm.linear_move(nx, ny)
                if col == 0:
                    # sleep for 1.5 nsecs to let the detector cool off.
                    # usually gets blasted as the laser moves into position
                    time.sleep(1.5)

                mag = 0
                for _ in range(self.nintegrations):
                    mag += apm.read_power_meter(verbose=False)
                    time.sleep(0.01)

                mag /= self.integration

            self._write_datum(tab, nx, ny, col, row, mag)
            self.canvas.set_cell_value(col, row, mag)

#============= EOF =============================================


