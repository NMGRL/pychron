# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import Instance, Int, Property, List, \
    Any, Enum, Str, DelegatesTo, Bool, TraitError, cached_property
# ============= standard library imports ========================
import os
from numpy import array, argmin
# ============= local library imports  ==========================
from pychron.globals import globalv
from pychron.spectrometer.thermo.source import ArgusSource
from pychron.spectrometer.thermo.magnet import ArgusMagnet
from pychron.spectrometer.thermo.detector import Detector
from pychron.spectrometer.thermo.spectrometer_device import SpectrometerDevice
from pychron.pychron_constants import NULL_STR, DETECTOR_ORDER, QTEGRA_INTEGRATION_TIMES, DEFAULT_INTEGRATION_TIME
from pychron.paths import paths


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


class Spectrometer(SpectrometerDevice):
    magnet = Instance(ArgusMagnet)
    source = Instance(ArgusSource)

    detectors = List(Detector)

    microcontroller = Any
    integration_time = Enum(QTEGRA_INTEGRATION_TIMES)

    reference_detector = Str('H1')

    magnet_dac = DelegatesTo('magnet', prefix='dac')

    magnet_dacmin = DelegatesTo('magnet', prefix='dacmin')
    magnet_dacmax = DelegatesTo('magnet', prefix='dacmin')

    current_hv = DelegatesTo('source')

    molecular_weight = Str('Ar40')
    molecular_weights = None
    isotopes = Property
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

    def test_connection(self):
        """
            if not in simulation mode send a GetIntegrationTime to the spectrometer
            if in simulation mode and the globalv.communication_simulation is disabled
            then return False

        :return: bool
        """
        ret = False
        if not self.simulation:
            ret = self.ask('GetIntegrationTime', verbose=True) is not None
        elif globalv.communication_simulation:
            ret = True
        return ret

    def set_gains(self, history=None):
        if history:
            self.debug('setting gains to {}, user={}'.format(history.create_date,
                                                             history.username))
        for di in self.detectors:
            di.set_gain()

        return [(di.name, di.gain) for di in self.detectors]

    def load_current_detector_gains(self):
        for di in self.detectors:
            di.get_gain()

    def get_integration_time(self, current=True):
        if current:
            resp = self.ask('GetIntegrationTime')
            if resp:
                try:
                    self.integration_time = float(resp)
                    self.info('Integration Time {}'.format(self.integration_time))

                except (TypeError, ValueError, TraitError):
                    self.warning('Invalid integration time. resp={}'.format(resp))
                    self.integration_time = DEFAULT_INTEGRATION_TIME

        return self.integration_time

    def set_integration_time(self, it, force=False):
        it = normalize_integration_time(it)
        if self.integration_time != it or force:
            self.debug('setting integration time = {}'.format(it))
            name = 'SetIntegrationTime'
            self.set_parameter(name, it)
            self.trait_setq(integration_time=it)

        return it

    def send_configuration(self):
        """
            send the configuration values to the device
        """
        self._send_configuration()

    def set_parameter(self, name, v):
        cmd = '{} {}'.format(name, v)
        self.ask(cmd)

    def get_parameter(self, cmd):
        return self.ask(cmd)

    def set_microcontroller(self, m):
        self.debug('set microcontroller {}'.format(m))
        self.magnet.microcontroller = m
        self.source.microcontroller = m
        self.microcontroller = m
        for d in self.detectors:
            d.microcontroller = m
            d.load()

    def get_deflection(self, name, current=False):
        deflection = 0
        det = self.get_detector(name)
        if det:
            if current:
                det.read_deflection()
            deflection = det.deflection

        return deflection

    def get_detector(self, name):
        if not isinstance(name, str):
            name = str(name)

        return next((det for det in self.detectors if det.name == name), None)

    def update_isotopes(self, isotope, detector):

        if isotope != NULL_STR:
            det = self.get_detector(detector)
            if not det:
                self.debug('cannot update detector "{}"'.format(detector))
            else:
                det.isotope = isotope
                index = self.detectors.index(det)

                nmass = int(isotope[2:])
                for i, di in enumerate(self.detectors):
                    mass = nmass - (i - index)
                    di.isotope = 'Ar{}'.format(mass)

    # ===============================================================================
    # load
    # ===============================================================================
    def load_configurations(self):
        self.sub_cup_configurations = ['A', 'B', 'C']
        self._sub_cup_configuration = 'B'

        scc = self.ask('GetSubCupConfigurationList Argon', verbose=False)
        if scc:
            if 'ERROR' not in scc:
                self.sub_cup_configurations = scc.split('\r')

        n = self.ask('GetActiveSubCupConfiguration')
        if n:
            if 'ERROR' not in n:
                self._sub_cup_configuration = n

        self.molecular_weight = 'Ar40'

    def load(self):

        self.load_detectors()

        p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        config = self.get_configuration_writer(p)
        pd = 'Protection'

        if config.has_section(pd):

            self.magnet.use_beam_blank = self.config_get(config, pd, 'use_beam_blank',
                                                         cast='boolean', default=False)
            self.magnet.use_detector_protection = self.config_get(config, pd,
                                                                  'use_detector_protection',
                                                                  cast='boolean', default=False)
            self.magnet.beam_blank_threshold = self.config_get(config, pd,
                                                               'beam_blank_threshold', cast='float', default=0.1)
            self.magnet.detector_protection_threshold = self.config_get(config, pd,
                                                                        'detector_protection_threshold',
                                                                        cast='float', default=0.1)
            ds = self.config_get(config, pd, 'detectors')
            if ds:
                ds = ds.split(',')
                self.magnet.protected_detectors = ds
                for di in ds:
                    self.info('Making protection available for detector "{}"'.format(di))

        self.magnet.load()

        self.debug('Detectors {}'.format(self.detectors))
        for d in self.detectors:
            d.load_deflection_coefficients()

    def finish_loading(self):
        if self.microcontroller:
            self.name = self.microcontroller.name

        self.magnet.finish_loading()

        if self.send_config_on_startup:
            # write configuration to spectrometer
            self._send_configuration()

    def load_detectors(self):
        config = self.get_configuration(path=os.path.join(paths.spectrometer_dir, 'detectors.cfg'))
        for name in config.sections():
            #relative_position = self.config_get(config, name, 'relative_position', cast='float')
            deflection_corrrection_sign = self.config_get(config, name, 'deflection_correction_sign', cast='int')

            color = self.config_get(config, name, 'color', default='black')
            default_state = self.config_get(config, name, 'default_state', default=True, cast='boolean')
            isotope = self.config_get(config, name, 'isotope')
            kind = self.config_get(config, name, 'kind', default='Faraday', optional=True)
            pt = self.config_get(config, name, 'protection_threshold', default=None, optional=True)

            self.add_detector(name=name,
                              #relative_position=relative_position,
                              protection_threshold=pt,
                              deflection_corrrection_sign=deflection_corrrection_sign,
                              color=color,
                              active=default_state,
                              isotope=isotope,
                              kind=kind)

    def add_detector(self, **kw):
        d = Detector(spectrometer=self, **kw)
        self.detectors.append(d)

    # ===============================================================================
    # signals
    # ===============================================================================

    def get_intensities(self, tagged=True):
        keys = []
        signals = []
        if self.microcontroller and not self.microcontroller.simulation:
            # if self.microcontroller.simulation and globalv.communication_simulation:
            #     keys, signals = self._get_simulation_data()
            # else:
            datastr = self.ask('GetData', verbose=False, quiet=True)
            if datastr:
                if not 'ERROR' in datastr:
                    data = datastr.split(',')
                    if tagged:
                        keys = data[::2]
                        signals = data[1::2]
                    else:
                        keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
                        signals = data

                signals = map(float, signals)

        if not keys and globalv.communication_simulation:
            keys, signals = self._get_simulation_data()

        for k, v in zip(keys, signals):
            det = self.get_detector(k)
            det.set_intensity(v)

        return keys, signals

    def get_intensity(self, dkeys):
        """
            dkeys: str or tuple of strs

        """
        data = self.get_intensities()
        if data is not None:
            keys, signals = data
            if isinstance(dkeys, (tuple, list)):
                return [signals[keys.index(key)] for key in dkeys]
            else:
                return signals[keys.index(dkeys)]

    def get_hv_correction(self, dac, uncorrect=False, current=False):
        """
        ion optics correction

        r=M*v_o/(q*B_o)
        r=M*v_c/(q*B_c)

        E=m*v^2/2
        v=(2*E/m)^0.5

        v_o/B_o = v_c/B_c
        B_c = B_o*v_c/v_o

        B_c = B_o*(E_c/E_o)^0.5

        B_o = B_c*(E_o/E_c)^0.5

        E_o = nominal hv
        E_c = current hv
        B_o = nominal dac
        B_c = corrected dac
        """
        source = self.source
        cur = source.current_hv
        if current:
            cur = source.read_hv()

        if cur is None:
            cor = 1
        else:
            try:
                # cor = source.nominal_hv / cur
                if uncorrect:
                    cor = source.nominal_hv / cur
                else:
                    cor = cur / source.nominal_hv

                cor **= 0.5

            except ZeroDivisionError:
                cor = 1

        dac *= cor
        return dac

    def correct_dac(self, det, dac, current=True):
        """
            correct for deflection
            correct for hv
        """
        #correct for deflection
        dev = det.get_deflection_correction(current=current)
        dac += dev

        #correct for hv
        # dac *= self.get_hv_correction(current=current)
        dac = self.get_hv_correction(dac, current=current)
        return dac

    def uncorrect_dac(self, det, dac, current=True):
        """
            inverse of correct_dac
        """
        dac = self.get_hv_correction(dac, uncorrect=True, current=current)
        dac -= det.get_deflection_correction(current=current)
        return dac

    # ===============================================================================
    # private
    # ===============================================================================
    def _get_simulation_data(self):
        from numpy.random import random

        signals = [1, 100, 3, 0.01, 0.01, 0.01] + random(6)
        keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
        return keys, signals

    def _send_configuration(self):
        command_map = dict(ionrepeller='IonRepeller',
                           electronenergy='ElectronEnergy',
                           ysymmetry='YSymmetry',
                           zsymmetry='ZSymmetry',
                           zfocus='ZFocus',
                           extractionlens='ExtractionLens',
                           ioncountervoltage='IonCounterVoltage')

        if self.microcontroller:

            p = os.path.join(paths.spectrometer_dir, 'config.cfg')
            if not os.path.isfile(p):
                self.warning('Spectrometer configuration file {} not found'.format(p))
                return

            self.info('Sending configuration "{}" to spectrometer'.format(p))
            config = self.get_configuration_writer(p)

            for section in config.sections():
                if section in ['Default', 'Protection']:
                    continue

                for attr in config.options(section):
                    v = config.getfloat(section, attr)
                    if v is not None:

                        if section == 'Deflections':
                            cmd = 'SetDeflection'
                            v = '{},{}'.format(attr.upper(), v)
                        else:
                            cmd = 'Set{}'.format(command_map[attr])

                        self.set_parameter(cmd, v)

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _magnet_default(self):
        return ArgusMagnet(spectrometer=self)

    def _source_default(self):
        return ArgusSource(spectrometer=self)

    def _integration_time_default(self):
        return DEFAULT_INTEGRATION_TIME

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_detectors(self):
        ds = []
        for di in DETECTOR_ORDER:
            ds.append(self._detectors[di])
        return ds

    def _get_sub_cup_configuration(self):
        return self._sub_cup_configuration

    def _set_sub_cup_configuration(self, v):
        self._sub_cup_configuration = v
        self.ask('SetSubCupConfiguration {}'.format(v))

    @cached_property
    def _get_isotopes(self):
        return sorted(self.molecular_weights.keys(), key=lambda x: int(x[2:]))

    @property
    def detector_names(self):
        return [di.name for di in self.detectors]

# ============= EOF =============================================
