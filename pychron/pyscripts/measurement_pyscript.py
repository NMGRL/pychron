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
#============= standard library imports ========================
import time
import os
from ConfigParser import ConfigParser
#============= local library imports  ==========================
from pychron.core.helpers.filetools import fileiter
from pychron.pyscripts.pyscript import verbose_skip, count_verbose_skip, \
    makeRegistry
from pychron.paths import paths
from pychron.pyscripts.valve_pyscript import ValvePyScript
from pychron.pychron_constants import MEASUREMENT_COLOR

ESTIMATED_DURATION_FF = 1.045

command_register = makeRegistry()


class MeasurementPyScript(ValvePyScript):
    automated_run = None
    ncounts = 0
    info_color = MEASUREMENT_COLOR
    _time_zero = None
    _time_zero_offset = 0

    _series_count = 0
    _baseline_series = None

    _regress_id = 0

    _detectors = None
    abbreviated_count_ratio = None
    _fit_series_count = 0

    def gosub(self, *args, **kw):
        kw['automated_run'] = self.automated_run
        super(MeasurementPyScript, self).gosub(*args, **kw)

    def reset(self, arun):
        self.debug('%%%%%%%%%%%%%%%%%% setting automated run {}'.format(arun.runid))
        self.automated_run = arun

        self._baseline_series = None
        self._series_count = 0
        self._fit_series_count = 0
        self._time_zero = None
        self._regress_id = 0
        self._detectors = None
        self.abbreviated_count_ratio = None
        self.ncounts = 0

    def get_command_register(self):
        cs = super(MeasurementPyScript, self).get_command_register()
        return cs + command_register.commands.items()

    def truncate(self, style=None):
        if style == 'quick':
            self.abbreviated_count_ratio = 0.25
        super(MeasurementPyScript, self).truncate(style=style)

    #    def get_script_commands(self):
    #        cmds = super(MeasurementPyScript, self).get_script_commands()
    #
    #        cmds += []
    #        return cmds

    def get_variables(self):
        return ['truncated', 'eqtime']

    #===============================================================================
    # commands
    #===============================================================================
    @verbose_skip
    @command_register
    def extraction_gosub(self, *args, **kw):
        kw['klass'] = 'ExtractionPyScript'
        super(MeasurementPyScript, self).gosub(*args, **kw)

    @count_verbose_skip
    @command_register
    def sniff(self, ncounts=0, calc_time=False,
              integration_time=1.04):
        if calc_time:
            self._estimated_duration += (ncounts * integration_time * ESTIMATED_DURATION_FF)
            return
        self.ncounts = ncounts
        if not self._automated_run_call('py_sniff', ncounts,
                                        self._time_zero, self._time_zero_offset,
                                        series=self._series_count):
            self.cancel()
        self._series_count += 1

    @count_verbose_skip
    @command_register
    def multicollect(self, ncounts=200, integration_time=1.04, calc_time=False):
        if calc_time:
            self._estimated_duration += (ncounts * integration_time * ESTIMATED_DURATION_FF)
            return

        self.ncounts = ncounts
        if self.abbreviated_count_ratio:
            ncounts *= self.abbreviated_count_ratio

        if not self._automated_run_call('py_data_collection',
                                        self,
                                        ncounts,
                                        self._time_zero,
                                        self._time_zero_offset,
                                        fit_series=self._fit_series_count,
                                        series=self._series_count):
            self.cancel()

        #        self._regress_id = self._series_count
        self._series_count += 2
        self._fit_series_count += 1

    @count_verbose_skip
    @command_register
    def baselines(self, ncounts=1, mass=None, detector='',
                  integration_time=1.04,
                  settling_time=4, calc_time=False):
        """
            if detector is not none then it is peak hopped
        """
        if self.abbreviated_count_ratio:
            ncounts *= self.abbreviated_count_ratio

        if calc_time:
            ns = ncounts
            d = ns * integration_time * ESTIMATED_DURATION_FF + settling_time
            self._estimated_duration += d
            return

        self.ncounts = ncounts
        if self._baseline_series:
            series = self._baseline_series
        else:
            series = self._series_count

        if not self._automated_run_call('py_baselines', ncounts,
                                        self._time_zero,
                                        self._time_zero_offset,
                                        mass,
                                        detector,
                                        fit_series=self._fit_series_count,
                                        settling_time=settling_time,
                                        series=series):
            self.cancel()
        self._baseline_series = series
        self._series_count += 2
        self._fit_series_count += 1

    @count_verbose_skip
    @command_register
    def load_hops(self, p, *args, **kw):
        if not os.path.isfile(p):
            p = os.path.join(self.root, p)

        if os.path.isfile(p):
            with open(p, 'r') as fp:
                # hops = [eval(line) for line in fp if not line.strip().startswith('#')]
                hops = [eval(li) for li in fileiter(fp)]
                return hops

        else:
            self.warning_dialog('No such file {}'.format(p))

    @count_verbose_skip
    @command_register
    def define_detectors(self, isotope, det, *args, **kw):
        self._automated_run_call('py_define_detectors', isotope, det)

    @count_verbose_skip
    @command_register
    def define_hops(self, hops=None, **kw):
        if hops is None:
            return

        self._automated_run_call('py_define_hops', hops)

    @count_verbose_skip
    @command_register
    def peak_hop(self, ncycles=5, hops=None, calc_time=False):
        if hops is None:
            return

        integration_time = 1.1

        counts = sum([ci * integration_time + s for _h, ci, s in hops]) * ncycles
        if calc_time:
            # counts = sum of counts for each hop
            self._estimated_duration += (counts * ESTIMATED_DURATION_FF)
            return

        group = 'signal'
        self.ncounts = counts
        if not self._automated_run_call('py_peak_hop', ncycles,
                                        counts,
                                        hops,
                                        self._time_zero,
                                        self._time_zero_offset,
                                        self._series_count,
                                        fit_series=self._fit_series_count,
                                        group=group):
            self.cancel()
        self._series_count += 1
        self._fit_series_count += 1
        #self._series_count += 4

    #    @count_verbose_skip
    #    @command_register
    #    def peak_hop(self, detector=None, isotopes=None, cycles=5, integrations=5, calc_time=False):
    #        if calc_time:
    #            self._estimated_duration += (cycles * integrations * ESTIMATED_DURATION_FF)
    #            return
    #
    #        self._automated_run_call('py_peak_hop', detector, isotopes,
    #                                    cycles,
    #                                    integrations,
    #                                    self._time_zero,
    #                                    self._series_count)
    #        self._series_count += 3

    @count_verbose_skip
    @command_register
    def peak_center(self, detector='AX', isotope='Ar40', integration_time=1.04, save=True, calc_time=False):
        if calc_time:
            self._estimated_duration += 30 * integration_time
            return

        self._automated_run_call('py_peak_center', detector=detector,
                                 isotope=isotope, integration_time=integration_time,
                                 save=save)

    @verbose_skip
    @command_register
    def get_intensity(self, name):
        if self._detectors:
            try:
                return self._detectors[name]
            except KeyError:
                pass

    @verbose_skip
    @command_register
    def equilibrate(self, eqtime=20, inlet=None, outlet=None, do_post_equilibration=True, delay=3):
        evt = self._automated_run_call('py_equilibration', eqtime=eqtime,
                                       inlet=inlet,
                                       outlet=outlet,
                                       do_post_equilibration=do_post_equilibration,
                                       delay=delay)
        if not evt:
            self.cancel()
        else:
            # wait for inlet to open
            evt.wait()

    # @verbose_skip
    # @command_register
    # def regress(self, *fits):
    #     if not fits:
    #         fits = 'linear'
    #
    #     self._automated_run_call('py_set_regress_fits', fits)

    @verbose_skip
    @command_register
    def set_fits(self, *fits):
        if not fits:
            fits = 'linear'
        self._automated_run_call('py_set_fits', fits)

    @verbose_skip
    @command_register
    def set_baseline_fits(self, *fits):
        if not fits:
            fits = 'average_SEM'
        self._automated_run_call('py_set_baseline_fits', fits)

    @verbose_skip
    @command_register
    def activate_detectors(self, *dets, **kw):
        peak_center = kw.get('peak_center', False)

        if dets:
            self._detectors = dict()
            self._automated_run_call('py_activate_detectors', list(dets), peak_center=peak_center)
            for di in list(dets):
                self._detectors[di] = 0

    @verbose_skip
    @command_register
    def position_magnet(self, pos, detector='AX', dac=False):
        """
            position_magnet(4.54312, dac=True) # detector is not relevant
            position_magnet(39.962, detector='AX')
            position_magnet('Ar40', detector='AX') #Ar40 will be converted to 39.962 use mole weight dict

        """
        self._automated_run_call('py_position_magnet', pos, detector, dac=dac)

    @verbose_skip
    @command_register
    def coincidence(self):
        self._automated_run_call('py_coincidence_scan')

    #===============================================================================
    #
    #===============================================================================
    def _automated_run_call(self, func, *args, **kw):
    #         return True
    #         if func not in ('py_activate_detectors',):
    #             return True

        if self.automated_run is None:
            return

        if isinstance(func, str):
            func = getattr(self.automated_run, func)

        return func(*args, **kw)

    def _set_spectrometer_parameter(self, *args, **kw):
        self._automated_run_call('py_set_spectrometer_parameter', *args, **kw)

    def _get_spectrometer_parameter(self, *args, **kw):
        return self._automated_run_call('py_get_spectrometer_parameter', *args, **kw)

        #===============================================================================

    # set commands
    #===============================================================================

    @verbose_skip
    @command_register
    def is_last_run(self):
        return self._automated_run_call('py_is_last_run')

    @verbose_skip
    @command_register
    def clear_conditions(self):
        self._automated_run_call('py_clear_conditions')

    @verbose_skip
    @command_register
    def clear_terminations(self):
        self._automated_run_call('py_clear_terminations')

    @verbose_skip
    @command_register
    def clear_truncations(self):
        self._automated_run_call('py_clear_truncations')

    @verbose_skip
    @command_register
    def clear_actions(self):
        self._automated_run_call('py_clear_actions')

    @verbose_skip
    @command_register
    def add_termination(self, attr, comp, start_count=0, frequency=10):
        self._automated_run_call('py_add_termination', attr, comp,
                                 start_count=start_count,
                                 frequency=frequency)

    @verbose_skip
    @command_register
    def add_truncation(self, attr, comp, start_count=0, frequency=10,
                       abbreviated_count_ratio=1.0):
        self._automated_run_call('py_add_truncation', attr, comp,
                                 start_count=start_count,
                                 frequency=frequency,
                                 abbreviated_count_ratio=abbreviated_count_ratio)

    @verbose_skip
    @command_register
    def add_action(self, attr, comp, start_count=0, frequency=10,
                   action=None,
                   resume=False):

    #        if self._syntax_checking:
    #            if isinstance(action, str):
    #                self.execute_snippet(action)

        self._automated_run_call('py_add_action', attr, comp,
                                 start_count=start_count,
                                 frequency=frequency,
                                 action=action,
                                 resume=resume)

    @verbose_skip
    @command_register
    def set_ncounts(self, ncounts=0):
        try:
            ncounts = int(ncounts)
            self.ncounts = ncounts
        except Exception, e:
            print 'set_ncounts', e

    @verbose_skip
    @command_register
    def set_time_zero(self, offset=0):
        """
            set the time_zero value.
            add offset to time_zero
            e.g

                T_o= ion pump closes
                offset seconds after T_o. define time_zero

                T_eq= inlet closes

        """
        self._time_zero = time.time() + offset
        self._time_zero_offset = offset

    @verbose_skip
    @command_register
    def set_integration_time(self, v):
        self._automated_run_call('py_set_integration_time', v)

    @verbose_skip
    @command_register
    def set_ysymmetry(self, v):
        self._set_spectrometer_parameter('SetYSymmetry', v)

    @verbose_skip
    @command_register
    def set_zsymmetry(self, v):
        self._set_spectrometer_parameter('SetZSymmetry', v)

    @verbose_skip
    @command_register
    def set_zfocus(self, v):
        self._set_spectrometer_parameter('SetZFocus', v)

    @verbose_skip
    @command_register
    def set_extraction_lens(self, v):
        self._set_spectrometer_parameter('SetExtractionLens', v)

    @verbose_skip
    @command_register
    def set_deflection(self, detname, v=''):

        if v == '':
            v = self._get_deflection_from_file(detname)

        if v is not None:
            v = '{},{}'.format(detname, v)
            self._set_spectrometer_parameter('SetDeflection', v)
        else:
            self.debug('no deflection value for {} supplied or in the config file'.format(detname))

    @verbose_skip
    @command_register
    def get_deflection(self, detname):

        self._get_spectrometer_parameter('GetDeflection', detname)

    @verbose_skip
    @command_register
    def set_cdd_operating_voltage(self, v=''):
        """
            if v is None use value from file
        """
        if self.automated_run is None:
            return

        if v == '':
            config = self._get_config()
            v = config.getfloat('CDDParameters', 'OperatingVoltage')

        self._set_spectrometer_parameter('SetIonCounterVoltage', v)

    @verbose_skip
    @command_register
    def set_source_optics(self, **kw):
        ''' 
        set_source_optics(YSymmetry=10.0)
        set ysymmetry to 10 use config.cfg
        
        '''
        attrs = ['YSymmetry', 'ZSymmetry', 'ZFocus', 'ExtractionLens']
        self._set_from_file(attrs, 'SourceOptics', **kw)

    @verbose_skip
    @command_register
    def set_source_parameters(self, **kw):
        '''            
        '''
        attrs = ['IonRepeller', 'ElectronVolts']
        self._set_from_file(attrs, 'SourceParameters', **kw)

    @verbose_skip
    @command_register
    def set_deflections(self):
        func = self._set_spectrometer_parameter

        config = self._get_config()
        section = 'Deflections'
        dets = config.options(section)
        for dn in dets:
            v = config.getfloat(section, dn)
            if v is not None:
                func('SetDeflection', '{},{}'.format(dn, v))

    def _get_deflection_from_file(self, name):
        config = self._get_config()
        section = 'Deflections'
        dets = config.options(section)
        for dn in dets:
            if dn.lower() == name.lower():
                return config.getfloat(section, dn)

    def _set_from_file(self, attrs, section, **user_params):
        func = self._set_spectrometer_parameter
        config = self._get_config()
        for attr in attrs:
            if attr in user_params:
                v = user_params[attr]
            else:
                v = config.getfloat(section, attr)

            if v is not None:
                func('Set{}'.format(attr), v)

    def _get_config(self):
        config = ConfigParser()
        p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        config.read(p)

        return config

    @property
    def truncated(self):
        return self._automated_run_call(lambda: self.automated_run.truncated)

    @property
    def eqtime(self):
        if self.automated_run:
            return self._automated_run_call(lambda: self.automated_run.eqtime)
        else:
            r = 15
            cg = self._get_config()
            if cg.has_option('Default', 'eqtime'):
                r = cg.getfloat('Default', 'eqtime', )
            return r

#===============================================================================
# handler
#===============================================================================
#    @on_trait_change('automated_run:signals')
#    def update_signals(self, obj, name, old, new):
#        try:
#            det = self._detectors
#            for k, v in new.iteritems():
#                det[k].signal = v
#        except (AttributeError, KeyError):
#            pass

# if __name__ == '__main__':
#    from pychron.core.helpers.logger_setup import logging_setup
#    paths.build('_test')
#    logging_setup('m_pyscript')
#
#    d = AutomatedRun()
#    d.configure_traits()

#============= EOF =============================================
# from traits.api import HasTraits, Button, Dict
# from traitsui.api import View
# class AutomatedRun(HasTraits):
#    test = Button
#    traits_view = View('test')
#    signals = Dict
#    def _test_fired(self):
#        m = MeasurementPyScript(root=os.path.join(paths.scripts_dir, 'measurement'),
#                            name='measureTest.py',
#                            automated_run=self
#                            )
#        m.bootstrap()
#    #    print m._text
#        m.execute()
#
#    def do_sniff(self, ncounts, *args, **kw):
#        keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
#        for i in range(ncounts):
#            vals = [random.random() for _ in range(len(keys))]
#            self.signals = dict(zip(keys, vals))
#            time.sleep(0.1)
#
#    def set_spectrometer_parameter(self, *args, **kw):
#        pass
#    def set_magnet_position(self, *args, **kw):
#        pass
#    def activate_detectors(self, *args, **kw):
#        pass
#    def do_data_collection(self, *args, **kw):
#        pass
# class Detector(object):
#    name = None
#    mass = None
#    signal = None
#    def __init__(self, name, mass, signal):
#        self.name = name
#        self.mass = mass
#        self.signal = signal
