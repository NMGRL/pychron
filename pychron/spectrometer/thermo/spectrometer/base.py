# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import absolute_import
import os
import random
import time

from numpy import array, argmin
from traits.api import Int, Property, List, \
    Enum, Str, DelegatesTo, Bool, Float

from pychron.core.progress import open_progress
from pychron.core.ramper import StepRamper
from pychron.pychron_constants import QTEGRA_INTEGRATION_TIMES, \
    QTEGRA_DEFAULT_INTEGRATION_TIME
from pychron.spectrometer import get_spectrometer_config_path, \
    set_spectrometer_config_name
from pychron.spectrometer.base_spectrometer import BaseSpectrometer


def normalize_integration_time(it):
    """
        find the integration time closest to "it"
    """
    x = array(QTEGRA_INTEGRATION_TIMES)
    return x[argmin(abs(x - it))]


def calculate_radius(m_e, hv, mfield):
    """
        m_e= mass/charge
        hv= accelerating voltage (V)
        mfield= magnet field (H)
    """
    r = ((2 * m_e * hv) / mfield ** 2) ** 0.5

    return r


class ThermoSpectrometer(BaseSpectrometer):
    integration_time = Float
    integration_times = List(QTEGRA_INTEGRATION_TIMES)
    magnet_dac = DelegatesTo('magnet', prefix='dac')

    magnet_dacmin = DelegatesTo('magnet', prefix='dacmin')
    magnet_dacmax = DelegatesTo('magnet', prefix='dacmin')

    current_hv = DelegatesTo('source')

    sub_cup_configurations = List
    sub_cup_configuration = Property(depends_on='_sub_cup_configuration')
    _sub_cup_configuration = Str

    dc_start = Int(0)
    dc_stop = Int(500)
    dc_step = Int(50)
    dc_stepmin = Int(1)
    dc_stepmax = Int(1000)
    dc_threshold = Int(3)
    dc_npeak_centers = Int(3)

    send_config_on_startup = Bool

    max_deflection = Int(500)

    _debug_values = None

    _test_connect_command = 'GetIntegrationTime'

    def make_deflection_dict(self):
        names = self.detector_names
        values = self.read_deflection_word(names)
        return dict(list(zip(names, values)))

    def make_configuration_dict(self):
        keys = list(self.get_command_map().values())
        values = self.get_parameter_word(keys)
        return dict(list(zip(keys, values)))

    def make_gains_dict(self):
        return {di.name: di.get_gain() for di in self.detectors}

    def get_detector_active(self, dname):
        """
        return True if dname in the list of intensity keys
        e.g.

        keys, signals = get_intensities
        return dname in keys

        :param dname:
        :return:
        """
        keys, prev = self.get_intensities()
        return dname in keys

    def test_intensity(self):
        """
        test if intensity is changing. make 2 measurements if exactlly the same for all
        detectors make third measurement if same as 1,2 make fourth measurement if same
        all four measurements same then test fails
        :return:
        """
        ret, err = True, ''
        keys, one = self.get_intensities()
        it = 0.1 if self.simulation else self.integration_time

        time.sleep(it)
        keys, two = self.get_intensities()

        if all(one == two):
            time.sleep(it)
            keys, three = self.get_intensities()
            if all(two == three):
                time.sleep(it)
                keys, four = self.get_intensities()
                if all(three == four):
                    ret = False
        return ret, err

    def set_gains(self, history=None):
        """

        :param history:
        :return: list
        """
        if history:
            self.debug(
                'setting gains to {}, user={}'.format(history.create_date,
                                                      history.username))
        for di in self.detectors:
            di.set_gain()

        return {di.name: di.gain for di in self.detectors}

    def load_current_detector_gains(self):
        """
        load the detector gains from the spectrometer
        """
        for di in self.detectors:
            di.get_gain()

    def read_integration_time(self):
        return self.ask('GetIntegrationTime')

    def set_integration_time(self, it, force=False):
        """

        :param it: float, integration time
        :param force: set integration even if "it" is not different than self.integration_time
        :return: float, integration time
        """
        it = normalize_integration_time(it)
        if self.integration_time != it or force:
            self.debug('setting integration time = {}'.format(it))
            name = 'SetIntegrationTime'
            self.set_parameter(name, it)
            self.trait_setq(integration_time=it)

        return it

    def set_parameter(self, name, v):
        cmd = '{} {}'.format(name, v)
        self.ask(cmd)

    def get_parameter(self, cmd):
        return self.ask(cmd)

    def set_deflection(self, name, value):
        det = self.get_detector(name)
        if det:
            det.deflection = value
        else:
            self.warning('Could not find detector "{}". Deflection Not Possible'.format(name))

    def get_deflection(self, name, current=False):
        """
        get deflection by detector name

        :param name: str, detector name
        :param current: bool, if True query qtegra
        :return: float
        """
        deflection = 0
        det = self.get_detector(name)
        if det:
            if current:
                det.read_deflection()
            deflection = det.deflection
        else:
            self.warning('Failed getting deflection for detector ="{}"'.format(name))

        return deflection

    def read_deflection_word(self, keys):
        x = self.ask('GetDeflections {}'.format(','.join(keys)), verbose=False)
        x = self._parse_word(x)
        return x

    def read_parameter_word(self, keys):
        x = self.ask('GetParameters {}'.format(','.join(keys)), verbose=False)
        x = self._parse_word(x)
        return x

    def get_configuration_value(self, key):
        values = self._get_cached_config()
        if values is not None:
            for d in values:
                try:
                    return d[key]
                except KeyError:
                    try:
                        return d[key.lower()]
                    except KeyError:
                        pass
            else:
                return 0
        else:
            return 0

    def set_debug_configuration_values(self):
        if self.simulation:

            ret = self._get_cached_config()
            if ret is not None:
                d = ret[0]
                keys = ('ElectronEnergy', 'YSymmetry', 'ZSymmetry', 'ZFocus', 'IonRepeller', 'ExtractionLens')
                ds = [0] + [d[k.lower()] for k in keys]
                self._debug_values = ds

    # ===============================================================================
    # load
    # ===============================================================================
    def load_configurations(self):
        """
        load configurations from Qtegra
        :return:
        """
        # self.sub_cup_configurations = ['A', 'B', 'C']
        # self._sub_cup_configuration = 'B'
        #
        # scc = self.ask('GetSubCupConfigurationList Argon', verbose=False)
        # if scc:
        #     if 'ERROR' not in scc:
        #         self.sub_cup_configurations = scc.split('\r')
        #
        # n = self.ask('GetActiveSubCupConfiguration')
        # if n:
        #     if 'ERROR' not in n:
        #         self._sub_cup_configuration = n

        self.molecular_weight = 'Ar40'

    def load(self):
        """
        load detectors
        load setupfiles/spectrometer/config.cfg file
        load magnet
        load deflections coefficients

        :return:
        """
        config = super(ThermoSpectrometer, self).load()

        pd = 'Protection'
        if config.has_section(pd):

            self.magnet.use_beam_blank = self.config_get(config, pd, 'use_beam_blank',
                                                         cast='boolean',
                                                         default=False)
            self.magnet.use_detector_protection = self.config_get(config, pd, 'use_detector_protection',
                                                                  cast='boolean',
                                                                  default=False)
            self.magnet.beam_blank_threshold = self.config_get(config, pd, 'beam_blank_threshold',
                                                               cast='float',
                                                               default=0.1)

            # self.magnet.detector_protection_threshold = self.config_get(config, pd,
            # 'detector_protection_threshold',
            # cast='float', default=0.1)
            ds = self.config_get(config, pd, 'detectors')
            if ds:
                ds = ds.split(',')
                self.magnet.protected_detectors = ds
                for di in ds:
                    self.info('Making protection available for detector "{}"'.format(di))

        if config.has_section('Deflections'):
            if config.has_option('Deflections', 'max'):
                v = config.getint('Deflections', 'max')
                if v:
                    self.max_deflection = v

        self.debug('Detectors {}'.format(self.detectors))
        for d in self.detectors:
            d.load_deflection_coefficients()

    def start(self):
        self.debug('********** Spectrometer start. send configuration: {}'.format(self.send_config_on_startup))
        if self.send_config_on_startup:
            self.send_configuration(use_ramp=True)

    def settle(self):
        time.sleep(self.integration_time*2)

    # ===============================================================================
    # signals
    # ===============================================================================
    def read_intensities(self, tagged=True, *args, **kw):
        keys = []
        signals = []

        datastr = self.ask('GetData', verbose=False, quiet=True, use_error_mode=False)
        if datastr:
            if 'ERROR' not in datastr:
                data = datastr.split(',')
                if tagged:
                    keys = data[::2]
                    signals = data[1::2]
                else:
                    keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
                    signals = data

            signals = list(map(float, signals))

        # if not keys and globalv.communication_simulation:
        #     keys, signals = self._get_simulation_data()

        # for k, v in zip(keys, signals):
        #     det = self.get_detector(k)
        #     det.set_intensity(v)

        # signals = array(signals)

        # self._check_intensity_no_change(signals)

        return keys, signals

    def get_intensity(self, dkeys):
        """
            dkeys: str or tuple of strs

        """
        data = self.get_intensities()
        if data is not None:

            keys, signals = data

            def func(k):
                return signals[keys.index(k)] if k in keys else 0

            if isinstance(dkeys, (tuple, list)):
                return [func(key) for key in dkeys]
            else:
                return func(dkeys)
                # return signals[keys.index(dkeys)] if dkeys in keys else 0

    def clear_cached_config(self):
        self._config = None

    def update_config(self, **kw):
        # p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        p = get_spectrometer_config_path()
        config = self.get_configuration_writer(p)
        for k, v in kw.items():
            if not config.has_section(k):
                config.add_section(k)

            for option, value in v:
                config.set(k, option, value)

        with open(p, 'w') as wfile:
            config.write(wfile)

        self.clear_cached_config()

    # ===============================================================================
    # private
    # ===============================================================================
    def _parse_word(self, word):
        try:
            x = [float(v) for v in word.split(',')]
        except (AttributeError, ValueError):
            x = []
        return x

    def _get_simulation_data(self):
        signals = [1, 100, 3, 0.01, 0.01, 0.01, 38, 38.5]  # + random(6)
        keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD', 'L2(CDD)', 'AX(CDD)']
        return keys, signals

    def _send_configuration(self, use_ramp=True):
        self.debug('======== Sending configuration ========')
        command_map = self.get_command_map()

        if self.microcontroller:
            ret = self._get_cached_config()
            if ret is not None:
                specparams, defl, trap, magnet = ret
                for k, v in defl.items():
                    cmd = 'SetDeflection'
                    v = '{},{}'.format(k, v)
                    self.set_parameter(cmd, v)

                for k, v in specparams.items():
                    try:
                        cmd = 'Set{}'.format(command_map[k])
                        self.set_parameter(cmd, v)
                    except KeyError:
                        self.debug(
                            '$$$$$$$$$$ Not setting {}. Not in command_map'.format(
                                k))

                # set trap voltage
                v = trap.get('voltage')
                self.debug('send trap voltage {}'.format(v))
                if v is not None:
                    self.source.trap_voltage = v

                # set the trap current
                v = trap.get('current')
                self.debug('send trap current {}'.format(v))
                if v is not None:
                    step = trap.get('ramp_step', 1)
                    period = trap.get('ramp_period', 1)
                    tol = trap.get('ramp_tolerance', 10)
                    if not self._ramp_trap_current(v, step, period, use_ramp, tol):
                        self.source.trap_current = v
                        # self.set_parameter('SetParameter',
                        #                    'Trap Current Set,{}'.format(v))
                # set the mftable
                mftable_name = magnet.get('mftable')
                if mftable_name:
                    self.debug('updating mftable name {}'.format(mftable_name))

                    self.magnet.field_table.path = mftable_name
                    self.magnet.field_table.load_table(load_items=True)

                self.debug('======== Configuration Finished ========')
                self.source.sync_parameters()

    def _ramp_trap_current(self, v, step, period, use_ramp=False, tol=10):
        if use_ramp:
            current = self.source.read_trap_current()
            if current is None:
                self.debug('could not read current trap. skipping ramp')
                return

            if v - current >= tol:
                if self.confirmation_dialog('Would you like to ramp up the '
                                            'Trap current from {} to {}'.format(current, v)):
                    prog = open_progress(1)

                    def func(x):
                        prog.change_message('Set Trap Current {}'.format(x))
                        self.source.trap_current = x
                        if not prog.accepted and not prog.canceled:
                            return True

                    r = StepRamper()

                    steps = (v - current) / step
                    prog.max = int(steps)
                    r.ramp(func, current, v, step, period)
                    prog.close()
                    return True

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _integration_time_default(self):
        self.default_integration_time = QTEGRA_DEFAULT_INTEGRATION_TIME
        return QTEGRA_DEFAULT_INTEGRATION_TIME

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_sub_cup_configuration(self):
        return self._sub_cup_configuration

    def _set_sub_cup_configuration(self, v):
        self._sub_cup_configuration = v
        self.ask('SetSubCupConfiguration {}'.format(v))

# if __name__ == '__main__':
# s = Spectrometer()
# ss = ArgusSource()
# ss.current_hv = 4505
# s.source = ss
# corrected = s.get_hv_correction(100,current=False)
# uncorrected = s.get_hv_correction(corrected, uncorrect=True, current=False)
#
# print corrected, uncorrected

# ============= EOF =============================================
