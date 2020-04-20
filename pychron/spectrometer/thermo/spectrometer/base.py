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
import time

from numpy import array, argmin
from traits.api import Int, Property, List, \
    Str, DelegatesTo, Bool, Float

from pychron.core.helpers.strtools import csv_to_floats
from pychron.core.progress import open_progress
from pychron.core.ramper import StepRamper
from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.pychron_constants import QTEGRA_INTEGRATION_TIMES, \
    QTEGRA_DEFAULT_INTEGRATION_TIME
from pychron.spectrometer import get_spectrometer_config_path
from pychron.spectrometer.base_spectrometer import BaseSpectrometer


def normalize_integration_time(it):
    """
        find the integration time closest to "it"
    """
    try:
        x = array(QTEGRA_INTEGRATION_TIMES)
        return x[argmin(abs(x - it))]
    except TypeError:
        return 1.0


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
        d = dict(list(zip(keys, values)))

        key = 'ElectronEnergy'
        if key in d:
            d[key] = float('{:0.2f}'.format(d[key]))

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

            # this is a hail mary to potential make qtegra happier post setting integration time
            self.debug('sleeping 2 seconds after setting integration time')
            time.sleep(2)

        return it

    def set_parameter(self, name, v, post_delay=None):
        cmd = '{} {}'.format(name, v)
        self.ask(cmd)
        if post_delay:
            time.sleep(post_delay)

    def get_parameter(self, cmd):
        if hasattr(self.source, 'read_{}'.format(cmd.lower())):
            return getattr(self.source, 'read_{}'.format(cmd.lower()))()
        else:
            return self.ask('Get{}'.format(cmd))

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
        x = self.ask('GetDeflections {}'.format(','.join(keys)), verbose=False, quiet=True)
        x = self._parse_word(x)
        return x

    def read_parameter_word(self, keys):
        x = self.ask('GetParameters {}'.format(','.join(keys)), verbose=True, quiet=False)
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
        time.sleep(self.integration_time * 2)

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

            signals = [float(s) for s in signals]

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

    def _get_source_parameter_value(self, mk, k):
        try:
            ret = getattr(self.source, 'read_{}'.format(k.lower()))()
        except AttributeError:
            ret = self.get_parameter(mk[k.lower()])
        return ret

    def verify_configuration(self, **kw):
        self.debug('========= Verifying configuration =========')
        readout_comp, defl_comp = self._load_configuration_comparisons()
        mismatch = False
        if self.microcontroller:
            command_map = self.get_command_map()
            args = self._get_cached_config()
            if args is not None:
                specparams, defl, trap, magnet = args
                for k, v in defl.items():
                    comp = defl_comp.get(k, {})
                    if comp.get('compare', True):
                        current = self.get_deflection(k, current=True)
                        dev = self._get_config_dev(current, v, comp)
                        if dev:
                            self.warning('verify failed {}. current={}, config={}'.format(k, current, v))
                            mismatch = True

                print('asdffffff', readout_comp)
                for k, v in specparams.items():
                    try:
                        mk = command_map[k]
                    except KeyError:
                        self.debug('--- Not checking {}. Not in command_map'.format(k))
                        continue

                    comp = readout_comp.get(mk, {})
                    if comp.get('compare', True):
                        current = self._get_source_parameter_value(command_map, mk)
                        try:
                            current = float(current)
                        except ValueError:
                            self.warning('invalid float value {}, {}'.format(mk, current))
                            continue
                        print('asdf', mk, comp)
                        dev = self._get_config_dev(current, v, comp)
                        if dev:
                            self.warning('verify failed {}. current={}, config={}'.format(mk, current, v))
                            mismatch = True

                for tag in ('voltage', 'current'):
                    v = trap.get(tag)
                    if v is not None:
                        comp = readout_comp.get('Trap{}'.format(tag.capitalize()), {})
                        if comp.get('compare', True):
                            current = getattr(self.source, 'trap_{}'.format(tag))
                            dev = self._get_config_dev(current, v, comp)
                            if dev:
                                self.warning('verify failed trap {}. current={}, config={}'.format(tag, current, v))
                                mismatch = True

        self.debug('========= Verify complete ===========')
        return not mismatch

    # ===============================================================================
    # private
    # ===============================================================================
    def _parse_word(self, word):
        try:
            x = csv_to_floats(word)
        except (AttributeError, ValueError):
            x = []
        return x

    def _get_simulation_data(self):
        signals = [1, 100, 3, 0.01, 0.01, 0.01, 38, 38.5]  # + random(6)
        keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD', 'L2(CDD)', 'AX(CDD)']
        return keys, signals

    def _get_config_dev(self, current, v, comp):
        dev = False
        if comp.get('compare', True):

            tol = comp.get('percent_tol')
            if not tol:
                tol = comp.get('tolerance', 0.01)
                delta = abs(current-v)
                dev = delta > tol
                self.debug('abs tolerance={}, delta={}'.format(tol, delta))
            else:
                try:
                    delta = abs(current - v) / float(v)
                    dev = delta > tol
                    self.debug('percent tolerance={}, delta={}'.format(tol, delta))
                except ZeroDivisionError:
                    self.warning('zero division exception')
                    tol = comp.get('tolerance', 0.01)
                    delta = abs(current - v)
                    dev = delta > tol
                    self.debug('abs tolerance={}, delta={}'.format(tol, delta))

        return dev

    def _load_configuration_comparisons(self):
        path = os.path.join(paths.spectrometer_dir, 'readout.yaml')
        readouts = {}
        deflections = {}
        yt = yload(path)
        if yt:
            readouts, deflections = yt
            readouts = {r['name']: r for r in readouts}
            deflections = {r['name']: r for r in deflections}

        return readouts, deflections

    def _send_configuration(self, use_ramp=True):
        self.debug('======== Sending configuration ========')

        if self.force_send_configuration:
            readout_comp, defl_comp = {}, {}
        else:
            readout_comp, defl_comp = self._load_configuration_comparisons()

        def not_setting(k, c, v):
            self.debug('Not setting {:<20s} current={}, config={}'.format(k, c, v))

        if self.microcontroller:
            command_map = self.get_command_map()
            ret = self._get_cached_config()
            if ret is not None:
                specparams, defl, trap, magnet = ret
                for k, v in defl.items():
                    if not self.force_send_configuration:
                        comp = defl_comp.get(k, {})
                        if comp.get('compare', True):
                            current = self.get_deflection(k, current=True)
                            dev = self._get_config_dev(current, v, comp)
                            if not dev:
                                not_setting(k, current, v)
                                continue

                    cmd = 'SetDeflection'
                    v = '{},{}'.format(k, v)
                    self.set_parameter(cmd, v, post_delay=0.05)

                for k, v in specparams.items():
                    try:
                        mk = command_map[k]
                    except KeyError:
                        self.debug('--- Not setting {}. Not in command_map'.format(k))
                        continue

                    if not self.force_send_configuration:
                        comp = readout_comp.get(mk, {})
                        if comp.get('compare', True):
                            # cmd = 'Get{}'.format(mk)
                            # current = self.get_parameter(cmd)
                            current = self._get_source_parameter_value(mk, k)
                            try:
                                current = float(current)
                            except (ValueError, TypeError):
                                self.warning('invalid value {}, {}'.format(mk, current))
                                continue

                            dev = self._get_config_dev(current, v, comp)
                            if not dev:
                                not_setting(mk, current, v)
                                continue

                    cmd = 'Set{}'.format(mk)
                    self.set_parameter(cmd, v, post_delay=0.05)

                for tag, func in (('voltage', self.source.read_trap_voltage),
                                  ('current', self.source.read_trap_current)):
                    # set trap voltage
                    v = trap.get(tag)
                    ttag = 'Trap{}'.format(tag.capitalize())
                    self.debug('send trap {} {}'.format(tag, v))
                    if v is not None:
                        if not self.force_send_configuration:
                            comp = readout_comp.get(ttag, {})
                            if comp.get('compare', True):
                                current = func()
                                try:
                                    current = float(current)
                                    dev = self._get_config_dev(current, v, comp)
                                    if not dev:
                                        not_setting(ttag, current, v)
                                        v = None
                                except (ValueError, TypeError):
                                    self.warning('invalid value {}, {}'.format(ttag, current))
                            else:
                                v = None

                        if v is not None:
                            setattr(self.source, 'trap_{}'.format(tag), v)

                v = trap.get('current')
                if v is not None:
                    step = trap.get('ramp_step', 1)
                    period = trap.get('ramp_period', 1)
                    tol = trap.get('ramp_tolerance', 10)
                    self._ramp_trap_current(v, step, period, use_ramp, tol)

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
            self.debug('ramping trap current')
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
            else:
                self.debug('trap current is up-to-date')
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
