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
from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = 'qt4'



#============= enthought library imports =======================
from traits.api import HasTraits, Float, Button, Instance, Int, \
     Event, Property, Bool, Any, Enum, on_trait_change, List
from traitsui.api import View, Item, VGroup, Group
import apptools.sweet_pickle as pickle
from pyface.timer.do_later import do_later
#============= standard library imports ========================
from numpy import polyfit, linspace, polyval
from threading import Event as TEvent
from threading import Thread
import os
import time
import random
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.paths import paths
from pychron.graph.graph import Graph
from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.database.data_warehouse import DataWarehouse
# from pychron.database.adapters.power_calibration_adapter import PowerCalibrationAdapter
from pychron.hardware.analog_power_meter import AnalogPowerMeter
from pychron.hardware.meter_calibration import MeterCalibration

FITDEGREES = dict(Linear=1, Parabolic=2, Cubic=3)


class DummyAPM:
    def read_power_meter(self, setpoint):
        return setpoint ** 2 + random.randint(0, 5)

    def check_saturation(self, n=3):
        return False

class DummyLB:
    def read_power_meter(self, setpoint):
        return setpoint + random.randint(0, 5)

class Parameters(HasTraits):
    pstart = Float(0)
    pstop = Float(100)
    pstep = Float(1)

    sample_delay = Float(1)
    integration_period = Float(1)
    nintegrations = Int(5)
    use_db = Bool(False)
    fit_degree = Enum('Linear', 'Parabolic', 'Cubic')
    def traits_view(self):
        v = View(
              *self._get_view_items()
              )
        return v
    def _get_view_items(self):
        items = [Item('pstart', label='Start'),
              Item('pstop', label='Stop'),
              Item('pstep', label='Step'),
              Item('sample_delay'),
              Item('integration_period'),
              Item('nintegrations'),
              Item('fit_degree', label='External Meter Fit'),
              Item('use_db')]
        return items

class FusionsCO2Parameters(Parameters):
    ifit_degree = Enum('Linear', 'Parabolic', 'Cubic')
    def _get_view_items(self):
        v = super(FusionsCO2Parameters, self)._get_view_items()
        v.insert(-1, Item('ifit_degree', label='Internal Meter Fit'))
        return v

class PowerCalibrationManager(Manager):
    parameters = Instance(Parameters)
    check_parameters = Instance(Parameters)
    parameters_klass = Parameters
    execute = Event
    execute_check = Event
    execute_check_label = Property(depends_on='_check_alive')
    _check_alive = Bool(False)

    execute_label = Property(depends_on='_alive')
    _alive = Bool(False)
    data_manager = None
    graph = None
    db = Any
    coefficients = Property(depends_on='_coefficients')
    _coefficients = List
    save = Button

    power_meter = Instance(AnalogPowerMeter)
#    def configure_power_meter_fired(self):
#        if self.parent is not None:
#            apm = self.parent.get_device('analog_power_meter')
#            apm.edit_traits(kind='modal')
    graph_cnt = 0
    def _execute_power_calibration_check(self):
        '''
        
        '''
        g = Graph()
        g.new_plot()
        g.new_series()
        g.new_series(x=[0, 100], y=[0, 100], line_style='dash')
        do_later(self._open_graph, graph=g)

        self._stop_signal = TEvent()
        callback = lambda pi, r: None
        self._iterate(self.check_parameters,
                      g, False, callback)

    def _graph_factory(self):
        gc = self.graph_cnt
        cnt = '' if not gc else gc
        self.graph_cnt += 1
        name = self.parent.name if self.parent else 'Foo'

        g = Graph(window_title='{} Power Calibration {}'.format(name, cnt),
                               container_dict=dict(padding=5),
                               window_x=500 + gc * 25,
                               window_y=25 + gc * 25
                               )

        g.new_plot(
                   xtitle='Setpoint (%)',
                   ytitle='Measured Power (W)')
        g.new_series()
        return g

    def _execute_power_calibration(self):
        self.graph = self._graph_factory()
#        s, _ = g.new_series()
#        po = g.plots[0]
#        g.add_aux_axis(po, s)

#        if self.parent is not None:
        self._open_graph()

        self.data_manager = dm = H5DataManager()
        if self.parameters.use_db:
            dw = DataWarehouse(root=os.path.join(self.parent.db_root, 'power_calibration'))
            dw.build_warehouse()
            directory = dw.get_current_dir()
        else:
            directory = os.path.join(paths.data_dir, 'power_calibration')

        _dn = dm.new_frame(directory=directory,
                base_frame_name='power_calibration')

        table = dm.new_table('/', 'calibration', table_style='PowerCalibration')
        callback = lambda p, r, t: self._write_data(p, r, t)
        self._stop_signal = TEvent()
        self._iterate(self.parameters,
                      self.graph, True,
                      callback, table)

        self._finish_calibration()

        if self._alive:
            self._alive = False
            self._save_to_db()
            self._apply_calibration()

    def _finish_calibration(self):
        self._calculate_calibration()
        self._apply_fit()

    def _iterate(self, params, graph,
                 is_calibrating, callback, *args):
        pstop = params.pstop
        pstep = params.pstep
        pstart = params.pstart
        sample_delay = params.sample_delay
#        nintegrations = params.nintegrations

        if self.parent is None:
            sample_delay /= 10.

#        integration_period = params.integration_period
        sign, dev = self._set_graph_limits(pstart, pstop)

        apm = self.power_meter
#        apm = DummyAPM()
#        if self.parent is not None:
#            apm = self.parent.get_device('analog_power_meter')
#        else:
#            apm = DummyPowerMeter()
        if self.parent is not None:
            self.parent.enable_laser()

        nsteps = int((dev + pstep) / pstep)
        for i in range(nsteps):
#            if not self._alive:
#                break
            if self._stop_signal.isSet():
                break

            pi = pstart + sign * i * pstep
            self.info('setting power to {}'.format(pi))
            time.sleep(sample_delay)
            if self.parent is not None:
                self.parent.set_laser_power(pi, use_calibration=not is_calibrating)
                if not is_calibrating:
                    pi = self.parent._calibrated_power

            rp = 0
            if apm is not None:
                pi, rp = self._get_iteration_data(pi)
#                    for _ in range(nintegrations):
#        #                if not self._alive:
#        #                    break
#                        if self._stop_signal.isSet():
#                            break
#
#                        self._read_power_meter(pi)
#    #                    if apm is not None:
#    #                        rp += apm.read_power_meter(pi)
#
#                        time.sleep(integration_period)
#            else:
#                n = 10
#                rp = pi + n * random.random() - n / 2

#            if not self._alive:
#                break
                if self._stop_signal.isSet():
                    break

#                graph.add_datum(data, do_after=1)
                self._graph_data((pi, rp))

                callback(pi, rp, *args)


            # check for detector saturation
#            if apm is not None:
                if apm.check_saturation(n=3):
                    if not self.confirmation_dialog('Increment Power Meter'):
                        self._alive = False
                        break
            # calculate slope and intercept of data

#        x = graph.get_data()
#        y = graph.get_data(axis=1)
#        try:
#            coeffs = polyfit(x, y, 1)
#        except TypeError:
#            pass

#            self._write_data(pi, , table)
    def _set_graph_limits(self, pstart, pstop):
        graph = self.graph
        dev = abs(pstop - pstart)
        sign = 1 if pstart < pstop else -1
        if sign == 1:
            graph.set_x_limits(pstart, pstop)
        else:
            graph.set_x_limits(pstop, pstart)
        return sign, dev

    def _graph_data(self, data):
        self.graph.add_datum(data)

    def _get_iteration_data(self, pi):
        params = self.parameters
        nintegrations = params.nintegrations
        integration_period = params.integration_period
        rp = 0
        apm = self.power_meter
        if apm is not None:
            for _ in range(nintegrations):
                if self._stop_signal.isSet():
                    break
                rp += apm.read_power_meter(pi)
                time.sleep(integration_period)

        return (pi, rp / float(nintegrations))

    def _get_parameters_path(self, name):
        p = os.path.join(paths.hidden_dir, 'power_calibration_{}'.format(name))
        return p

    def _load_parameters(self, p):
        pa = None
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                try:
                    pa = pickle.load(f)
                except (pickle.PickleError, EOFError):
                    pass

        klass = self.parameters_klass
        if pa is None or not isinstance(pa, klass):
            pa = klass()

        return pa

    def _apply_calibration(self):

        if self.confirmation_dialog('Apply Calibration'):
            self._calculate_calibration()
#            pc = PowerCalibrationObject()
            pc = MeterCalibration(self._coefficients)
            self.dump_calibration(pc)


#    def _dump_calibration(self, pc):
#        name = self.parent.name if self.parent else 'foo'
#        p = os.path.join(paths.hidden_dir, '{}_power_calibration'.format(name))
#        self.info('saving power calibration to {}'.format(p))
#        try:
#            with open(p, 'wb') as f:
#                pickle.dump(pc, f)
#
#        except pickle.PickleError:
#            pass
#
#        #also update logic board configuration file
#        if self.parent is not None:
#            lb = self.parent.laser_controller
#            config = lb.get_configuration()
#            section = 'PowerOutput'
#            if not config.has_section(section):
#                config.add_section(section)
#            config.set(section,
#                       'coefficients',
#                       ','.join(map('{:0.3e}'.format, pc.coefficients))
#                       )
#            lb.write_configuration(config)


    def _save_to_db(self):
        if self.parameters.use_db:
#            db = PowerCalibrationAdapter(name=co2laser_db,
#                                         kind='sqlite')
            db = self.db
            db.connect()
            r = db.add_calibration_record()
            db.add_path(r, self.data_manager.get_current_path())
            db.commit()
            db.close()
        self.data_manager.close_file()

#    def _gragh_data(self, data):
#        g = self.graph
#        if isinstance(data, (tuple, list)):
#
#            g.add_datum(
#                            (pi, di),
#                            do_after=1)


    def _write_data(self, pi, rp, table):

        row = table.row
        row['setpoint'] = pi
        row['value'] = rp
        row.append()
        table.flush()

    def _calculate_calibration(self):
        xs = self.graph.get_data()
        ys = self.graph.get_data(axis=1)
        deg = FITDEGREES[self.parameters.fit_degree]
        self._coefficients = self._regress(xs, ys, deg)

    def _regress(self, xs, ys, deg):


#        try:
#            #make x and y same lenght
        if xs is not None and ys is not None:
            xs, ys = zip(*zip(xs, ys))

        coeffs = polyfit(xs, ys, deg)
#        print coeffs
        return list(coeffs)

#        except TypeError:
#        return [1, 0]
#            return [1, 0]

    def _open_graph(self, graph=None):
        def _open(graph):
            if graph is None:
                graph = self.graph

            ui = graph.edit_traits()
            if self.parent:
                self.parent.add_window(ui)
        do_later(_open, graph=graph)

    def _apply_fit(self, new=True):
        xs = self.graph.get_data()

        x = linspace(min(xs), max(xs), 500)
        y = polyval(self._coefficients, x)
        g = self.graph
        if new:
            g.new_series(x, y, color='black', line_style='dash')
        else:
            g.set_data(x, series=2)
            g.set_data(y, series=2, axis=1)
        g.redraw()
#===============================================================================
# handlers
#===============================================================================
    @on_trait_change('parameters:[fit_degree, ifit_degree]')
    def update_graph(self):
        if self.graph:
            self._calculate_calibration()
            self._apply_fit(new=False)

    def __alive_changed(self):
        if not self._alive:
            if self.parent is not None:
                self.parent.disable_laser()

    def _save_fired(self):
#        pc = PowerCalibrationObject()
        pc = MeterCalibration(self.coefficients)
        self.dump_power_calibration(pc.coefficients)

    def _parse_coefficient_string(self, cs, warn=True):
        try:
            return map(float, cs.split(','))
        except ValueError:
            if warn:
                self.warning_dialog('Invalid coefficient string {}'.format(cs))

    def _execute_check_fired(self):
        if self._check_alive:
            self._stop_signal.set()
            self._check_alive = False
        else:
            self._check_alive = True
            t = Thread(target=self._execute_power_calibration_check)
            t.start()

    def _execute_fired(self):
        if self._alive:
            self._stop_signal.set()
            self._alive = False
            if self.parameters.use_db:
                if self.confirmation_dialog('Save to Database'):
                    self._save_to_db()
                    return
                else:
                    self.data_manager.delete_frame()
                    self.data_manager.close_file()

                self._apply_calibration()

        else:
            self._alive = True
            t = Thread(target=self._execute_power_calibration)
            t.start()

    def kill(self):
        super(PowerCalibrationManager, self).kill()
        if self.initialized:
            for n in ['parameters', 'check_parameters']:
                with open(self._get_parameters_path(n),
                          'wb') as f:
                    pickle.dump(getattr(self, n), f)
#            with open(self._get_parameters_path('parameters'),
#                      'wb') as f:
#                pickle.dump(self.check_parameters, f)

    def traits_view(self):

        self.graph_cnt = 0

        v = View(
                 VGroup(

                        Group(
                                Group(
                                      self._button_factory('execute', align='right'),
                                      Item('parameters', show_label=False, style='custom'),
                                      label='Calculate'
                                      ),
                                Group(
                                      self._button_factory('execute_check', align='right'),
                                      Item('check_parameters', show_label=False, style='custom'),
                                      label='Check'
                                      ),
                                layout='tabbed',
                                show_border=True,
                                label='Setup'
                                ),
                 VGroup(Item('coefficients', tooltip='Polynomial coefficients. Enter A,B,C... where\
                 Watts=Ax^2+Bx+C, x=Power'),
                        self._button_factory('save', align='right'),
                        show_border=True,
                        label='Set Calibration'
                        ),
                 VGroup(
                        Item('power_meter', style='custom', show_label=False),
                            show_border=True,
                            label='Power Meter')
                 ),

                 handler=self.handler_klass,
                 title='Power Calibration',
                 id='pychron.power_calibration_manager',
                 resizable=True
                 )
        return v

    def _get_execute_label(self):
        return 'Stop' if self._alive else 'Start'

    def _get_execute_check_label(self):
        return 'Stop' if self._alive else 'Start'

    def _get_coefficients(self):
        return ','.join(['{:0.4f}'.format(c) for c in self._coefficients]) if self._coefficients else ''

    def _validate_coefficients(self, v):
        try:
            return map(float, [c for c in v.split(',')])

        except (ValueError, AttributeError):
            pass

    def _set_coefficients(self, v):
        self._coefficients = v

    def _parameters_default(self):
        p = self._get_parameters_path('parameters')
        return self._load_parameters(p)

    def _check_parameters_default(self):
        p = self._get_parameters_path('check_parameters')
        return self._load_parameters(p)

    def __coefficients_default(self):
        r = [1, 0]
#        if self.parent:
        pc = self.load_power_calibration()
        if pc:
            if pc.coefficients:
                r = list(pc.coefficients)
        return r

    def _power_meter_default(self):
        if self.parent is not None:
            apm = self.parent.get_device('analog_power_meter')
        else:
            apm = AnalogPowerMeter()
        return apm

    def _get_calibration_path(self, cp):
        if cp is None:
            cp = os.path.join(paths.hidden_dir, '{}_power_calibration'.format(self.parent.name))
        return cp

#===============================================================================
# persistence
#===============================================================================
    def dump_power_calibration(self, coefficients, calibration_path=None):

#        calibration_path = self._get_calibration_path(calibration_path)
#        self.info('dumping power calibration {}'.format(calibration_path))

        coeffstr = lambda c:'calibration coefficients= {}'.format(', '.join(map('{:0.3e}'.format, c)))
        self.info(coeffstr(coefficients))
#        if bounds:
#            for coeffs, bi in zip(coefficients, bounds):
#                self.info('calibration coefficient')
#            self.info('{} min={:0.2f}, max={:0.2f}'.format(coeffstr(coeffs, *bi)))
#        else:
#            self.info(coeffstr(coefficients))
#
#        pc = MeterCalibration(coefficients)
#        pc.bounds = bounds
#        try:
#            with open(calibration_path, 'wb') as f:
#                pickle.dump(pc, f)
#        except  (pickle.PickleError, EOFError, OSError), e:
#            self.warning('pickling error {}'.format(e))

        # also update logic board configuration file
        if self.parent is not None:
            lb = self.parent.laser_controller
            config = lb.get_configuration()
            section = 'PowerOutput'
            if not config.has_section(section):
                config.add_section(section)

            config.set(section,
                       'coefficients',
                       ','.join(map('{:0.3e}'.format, coefficients))
                       )
            lb.write_configuration(config)

    def load_power_calibration(self, calibration_path=None, verbose=True, warn=True):
#        calibration_path = self._get_calibration_path(calibration_path)
#        if os.path.isfile(calibration_path):
#            if verbose:
#                self.info('loading power calibration {}'.format(calibration_path))

#            with open(calibration_path, 'rb') as f:
#                try:
#                    pc = pickle.load(f)
#                except (pickle.PickleError, EOFError, OSError), e:
#                    self.warning('unpickling error {}'.format(e))
#                    pc = MeterCalibration([1, 0])

#        else:
#            pc = MeterCalibration([1, 0])

        if self.parent is not None:
            lb = self.parent.laser_controller
            config = lb.get_configuration()
            section = 'PowerOutput'
            if config.has_section(section):
                coefficients = config.get(section, 'coefficients')
                cs = self._parse_coefficient_string(coefficients, warn)
                if cs is None:
                    return
            else:
                cs = [1, 0]

        pc = MeterCalibration(cs)
        return pc

class FusionsCO2PowerCalibrationManager(PowerCalibrationManager):
    '''
        fusions co2 has a built in power meter that needs to be calibrated
        
    '''
    parameters_klass = FusionsCO2Parameters

    _internal_powe_meter_coeffs = None
    _ipm_coeffs_w_v_r = None
    _ipm_coeffs_w_v_r1 = None
    def _apply_calibration(self):
        super(FusionsCO2PowerCalibrationManager, self)._apply_calibration()
#        n = self.parent.name if self.parent else 'foo'
#        p = os.path.join(paths.hidden_dir, '{}_internal_meter_calibration'.format(n))
#        with open(p, 'wb') as f:
#            obj = MeterCalibration(self._ipm_coeffs_w_v_r)
#            try:
#                pickle.dump(obj, f)
#                self.info('dumped internal power meter calibration to {}'.format(p))
#            except (OSError, pickle.PickleError):
#                pass
        # write coeffs to logic board config file
        if self.parent:
            lb = self.parent.laser_controller
            config = lb.get_configuration()
            sec = 'PowerMeter'
            if not config.has_section(sec):
                config.add_section(sec)

            config.set(sec, 'coefficients', self._ipm_coeffs_w_v_r)
            self.write_configuration(config)

    def _finish_calibration(self):
        super(FusionsCO2PowerCalibrationManager, self)._finish_calibration()
        g = Graph()
        g.new_plot()

        # plot W vs 8bit dac
        x = self.graph.get_data(axis=1)
        _, y = self.graph.get_aux_data()

        xf = self.graph.get_data(axis=1, series=2)
        _, yf = self.graph.get_aux_data(series=3)

#        print xf
#        print yf
        x, y = zip(*zip(x, y))
        xf, yf = zip(*zip(xf, yf))
        g.new_series(x, y)
        g.new_series(xf, yf)

        self._ipm_coeffs_w_v_r = self._regress(x, y, FITDEGREES['linear'])
        self. _ipm_coeffs_w_v_r1 = self._regress(xf, yf, FITDEGREES['linear'])

        self._open_graph(graph=g)


    def _calculate_calibration(self):
        super(FusionsCO2PowerCalibrationManager, self)._calculate_calibration()
        g = self.graph
        xs, ys = g.get_aux_data()
        deg = FITDEGREES[self.parameters.ifit_degree]
        self._internal_powe_meter_coeffs = self._regress(xs, ys, deg)

    def _apply_fit(self, new=True):
        super(FusionsCO2PowerCalibrationManager, self)._apply_fit(new=new)

        xs, ys = self.graph.get_aux_data()
        x = linspace(min(xs), max(xs), 500)
        y = polyval(self._internal_powe_meter_coeffs, x)
        g = self.graph
        if new:
            s, p = g.new_series(x, y, color='red',
                         aux_plot=True,
                         dash='dash')

            pp = p.plots['aux001'][0]
            s.index_mapper = pp.index_mapper
            s.value_mapper = pp.value_mapper

        else:
            g.set_aux_data(x, y, series=3)
        g.redraw()

    def _set_graph_limits(self, pstart, pstop):
        sign, dev = super(FusionsCO2PowerCalibrationManager, self)._set_graph_limits(pstart, pstop)

        p = self.graph.plots[0].plots['aux001'][0]
        s = pstart
        e = pstop
        if sign == -1:
            s = pstop
            e = pstart

        p.index_mapper.range.low_setting = s
        p.index_mapper.range.high_setting = e
        return sign, dev

    def _graph_data(self, data):
        g = self.graph
        g.add_datum(data[0], do_after=1)
        g.add_aux_datum(data[1])

    def _get_iteration_data(self, pi):
        params = self.parameters
        nintegrations = params.nintegrations
        integration_period = params.integration_period
        apm = self.power_meter
        apm = DummyAPM()

#        lb = self.parent.logic_board
        lb = DummyLB()

        if self.parent is None:
            integration_period /= 10.

        rp = 0
        rip = 0
        if apm is not None:
            gtime = time.time
            for _ in range(nintegrations):
                st = gtime()

                if self._stop_signal.isSet():
                    break
                rp += apm.read_power_meter(pi)
                rip += lb.read_power_meter(setpoint=pi)
                time.sleep(max(1e-6,
                               integration_period - (gtime() - st)))

        return [(pi, rp), (pi, rip)]

    def _graph_factory(self):
        g = super(FusionsCO2PowerCalibrationManager, self)._graph_factory()

        s, p = g.new_series(
#                     [1, 2, 3, 4], [10, 30, 5, 100],
                     aux_plot=True)
        g.add_aux_axis(p, s, title='Internal Meter (8bit)')
        return g

if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('pcm')
    pac = FusionsCO2PowerCalibrationManager()
    pac.configure_traits()
#============= EOF =============================================
