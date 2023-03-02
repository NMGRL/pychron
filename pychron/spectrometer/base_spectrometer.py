# ===============================================================================
# Copyright 2017 ross
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
import os
from random import random

import yaml
from numpy import array
from traits.api import Any, cached_property, List, TraitError, Str, Property, Bool
from yaml import SafeLoader

from pychron.core.helpers.filetools import glob_list_directory
from pychron.core.yaml import yload
from pychron.globals import globalv
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from pychron.spectrometer import (
    get_spectrometer_config_path,
    get_spectrometer_config_name,
    set_spectrometer_config_name,
)
from pychron.spectrometer.base_detector import BaseDetector
from pychron.spectrometer.spectrometer_device import SpectrometerDevice


class NoIntensityChange(BaseException):
    pass


class BaseSpectrometer(SpectrometerDevice):
    integration_time = Any
    default_integration_time = 1
    magnet = Any
    source = Any
    magnet_klass = Any
    source_klass = Any
    detector_klass = Any
    microcontroller_klass = Any
    detectors = List
    molecular_weights = None

    reference_detector = Str("H1")
    molecular_weight = Str("Ar40")
    isotopes = Property

    spectrometer_configuration = Str
    spectrometer_configurations = List

    force_send_configuration = Bool(True)

    use_deflection_correction = Bool(True)
    use_hv_correction = Bool(True)
    _connection_status = False
    _saved_integration = None
    _debug_values = None

    _test_connect_command = ""

    _config = None

    _prev_signals = None
    _no_intensity_change_cnt = 0
    active_detectors = List

    def set_data_pump_mode(self, mode):
        pass

    def halted(self):
        pass

    def sink_data(self, writer, n):
        pass

    def cancel(self):
        pass

    def convert_to_axial(self, det, v):
        return v

    def make_deflection_dict(self):
        raise NotImplementedError

    def make_configuration_dict(self):
        raise NotImplementedError

    def make_gains_dict(self):
        raise NotImplementedError

    def make_settings(self):
        return self._get_cached_config()

    def start(self):
        pass

    def load_configurations(self):
        pass

    def finish_loading(self):
        """
        finish loading magnet
        send configuration if self.send_config_on_startup set in Preferences
        :return:
        """
        self.info("finish loading")
        if self.microcontroller:
            self.name = self.microcontroller.name

        ret, err = self.test_connection()
        if ret:
            self.magnet.finish_loading()
            self.source.finish_loading()

    def test_connection(self, force=True):
        """
            if not in simulation mode send a GetIntegrationTime to the spectrometer
            if in simulation mode and the globalv.communication_simulation is disabled
            then return False

        :return: bool
        """
        self.info("testing connnection")
        ret, err = False, ""
        if not self.simulation:
            if force:
                ret = self.ask(self._test_connect_command, verbose=True) is not None
            else:
                ret = self._connection_status
        elif globalv.communication_simulation:
            ret = True

        self._connection_status = ret
        self.microcontroller.set_simulation(not ret)
        return ret, err

    def get_integration_time(self, current=True):
        """
        return current or cached integration time, i.e time between intensity measurements

        :param current: bool, if True retrieve value from qtegra
        :return: float
        """
        if current:
            resp = self.read_integration_time()
            if resp:
                try:
                    self.integration_time = float(resp)
                    self.info("Integration Time {}".format(self.integration_time))

                except (TypeError, ValueError, TraitError):
                    self.warning("Invalid integration time. resp={}".format(resp))
                    self.integration_time = self.default_integration_time

        return self.integration_time

    def save_integration(self):
        self._saved_integration = self.integration_time

    def restore_integration(self):
        if self._saved_integration:
            self.set_integration_time(self._saved_integration)
            self._saved_integration = None

    def get_update_period(self, it=None, *args, **kw):
        if it is None:
            it = self.integration_time
        return it

    def correct_dac(self, det, dac, current=True):
        """
        correct for deflection
        correct for hv
        """
        # correct for deflection
        if self.use_deflection_correction:
            dev = det.get_deflection_correction(current=current)
            dac += dev
            self.debug(
                "doing deflection correction.  dev: {}, new dac: {}".format(dev, dac)
            )

        # correct for hv
        if self.use_hv_correction:
            cor = self.get_hv_correction(current=current)
            dac *= cor
            self.debug("doing hv correction. factor: {}, new dac: {}".format(cor, dac))

        return dac

    def uncorrect_dac(self, det, dac, current=True):
        """
        inverse of correct_dac
        """

        if self.use_hv_correction:
            cor = self.get_hv_correction(uncorrect=True, current=current)
            dac *= cor
            self.debug(
                "doing hv uncorrection. factor: {}, new dac: {}".format(cor, dac)
            )

        if self.use_deflection_correction:
            dac -= det.get_deflection_correction(current=current)
        return dac

    def get_hv_correction(self, uncorrect=False, current=False):
        """
        ion optics correction::

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

        # dac *= cor
        return cor

    def get_deflection_word(self, keys):
        if self.simulation:
            x = [random.random() for i in keys]
        else:
            x = self.read_deflection_word(keys)
        return x

    def get_parameter_word(self, keys):
        if self.simulation:
            if self._debug_values:
                x = self._debug_values
            else:
                x = [random() for i in keys]
        else:
            x = self.read_parameter_word(keys)

        return x

    def map_isotope(self, mass):
        """
        map a mass to an isotope
        @param mass:
        @return:
        """
        molweights = self.molecular_weights

        found = None
        mi = 1
        for k, v in molweights.items():
            d = abs(v - mass)
            if d < 0.15 and d < mi:
                mi = d
                found = k
                # self.debug('map isotope {:0.3f} {} {:0.3f} {:0.3f} {} {}'.format(mass, k, v, d, mi, found))

        if found is None:
            found = "Iso{:0.4f}".format(mass)

        return found

    def map_mass(self, isotope):
        """
        map an isotope to a mass
        @param isotope:
        @return:
        """
        try:
            return self.molecular_weights[isotope]
        except KeyError:
            self.warning(
                "Invalid isotope. Cannot map to a mass. {} not in molecular_weights".format(
                    isotope
                )
            )

    def update_isotopes(self, isotope, detector):
        """
        update the isotope name for each detector

        called by AutomatedRun._define_detectors

        :param isotope: str
        :param detector: str or Detector
        :return:
        """
        if isotope != NULL_STR:
            det = self.get_detector(detector)
            if not det:
                self.debug('cannot update detector "{}"'.format(detector))
            else:
                det.isotope = isotope
                try:
                    det.mass = self.map_mass(isotope)
                except TraitError:
                    self.warning(
                        "isotope={} molweights={}".format(
                            isotope, self.molecular_weights
                        )
                    )

                try:
                    self._update_isotopes_hook(isotope, det.index)
                except BaseException as e:
                    self.warning(
                        "Cannot update isotopes. isotope={}, detector={}. error:{}".format(
                            isotope, detector, e
                        )
                    )

    def _update_isotopes_hook(self, isotope, index):
        dets = self.active_detectors
        if not dets:
            dets = self.detectors

        nmass = self.map_mass(isotope)
        for di in dets:
            mass = nmass - di.index + index
            isotope = self.map_isotope(mass)
            self.debug("setting detector {} to {} ({})".format(di.name, isotope, mass))
            di.isotope = isotope
            di.mass = mass

        # old version
        # this version of the update isotope function was developed with Stephen cox in 3/20/19
        # however potentially the issue was not with the code but not having detectors.cfg setup correctly
        # e.g. not having the "index" value set correctly for each detector
        # H2 index=0, H1 index=1, H2(CDD) index=0.1, H1(CDD) index=1.1 etc

        # def _update_isotope_hook(self, isotope, index):
        #     dets = self.active_detectors
        #     if not dets:
        #         dets = self.detectors
        #         idxs = [di.index for di in dets]
        #     else:
        #         idxs = range(len(dets))
        #         index = next((i for i, d in enumerate(dets) if d.index == index), 0)
        #
        #     nmass = self.map_mass(isotope)
        #     for di, didx in zip(dets, idxs):
        #         mass = nmass - didx + index
        #         isotope = self.map_isotope(mass)
        #         self.debug('setting detector {} to {} ({})'.format(di.name, isotope, mass))
        #         di.isotope = isotope
        #         di.mass = mass

    def verify_configuration(self, **kw):
        return True

    def send_configuration(self, **kw):
        """
        send the configuration values to the device
        """
        self._send_configuration(**kw)

    def _send_configuration(self, **kw):
        raise NotImplementedError

    def _get_cached_config(self):
        if self._config is None:
            p = get_spectrometer_config_path()
            if not os.path.isfile(p):
                self.warning_dialog(
                    "Spectrometer configuration file {} not found".format(p)
                )
                return

            self.debug("caching configuration from {}".format(p))
            config = self.get_configuration_writer(p)
            d = {}
            defl = {}
            trap = {}
            for section in config.sections():
                if section in ("Default", "Protection", "General", "Trap", "Magnet"):
                    continue

                for attr in config.options(section):
                    v = config.getfloat(section, attr)
                    if v is not None:
                        if section == "Deflections":
                            defl[attr.upper()] = v
                        else:
                            d[attr] = v

            section = "Trap"
            if config.has_section(section):
                for attr in (
                    "current",
                    "ramp_step",
                    "ramp_period",
                    "ramp_tolerance",
                    "voltage",
                ):
                    if config.has_option(section, attr):
                        trap[attr] = config.getfloat(section, attr)

            section = "Magnet"
            magnet = {}
            if config.has_section(section):
                for attr in ("mftable",):
                    if config.has_option(section, attr):
                        magnet[attr] = config.get(section, attr)

            if "hv" in d:
                self.source.nominal_hv = d["hv"]

            self._config = dict(source=d, deflection=defl, trap=trap, magnet=magnet)

        return self._config

    def load(self):
        self.load_molecular_weights()
        self.load_detectors()

        # does this ever do anything? I don't think any magnet defines a `load` method
        self.magnet.load()

        # load local configurations
        self.spectrometer_configurations = glob_list_directory(
            paths.spectrometer_config_dir, remove_extension=True, extension=".cfg"
        )

        name = get_spectrometer_config_name()
        sc, _ = os.path.splitext(name)
        self.spectrometer_configuration = sc

        p = get_spectrometer_config_path(name)
        config = self.get_configuration_writer(p)

        return config

    def load_molecular_weights(self):
        import csv

        # load the molecular weights dictionary

        p = os.path.join(paths.spectrometer_dir, "molecular_weights.csv")
        yp = os.path.join(paths.spectrometer_dir, "molecular_weights.yaml")
        mws = None
        if os.path.isfile(p):
            self.info('loading "molecular_weights.csv" file. {}'.format(p))
            with open(p, "r") as f:
                reader = csv.reader(f, delimiter="\t")
                try:
                    mws = {l[0]: float(l[1]) for l in reader}
                except BaseException:
                    mws = None
        elif os.path.isfile(yp):
            self.info('loading "molecular_weights.yaml" file. {}'.format(yp))
            try:
                mws = yload(yp)
            except BaseException:
                mws = None

        if mws is None:
            self.info('writing a default "molecular_weights.csv" file')
            # make a default molecular_weights.csv file
            from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS as mws

            with open(p, "w") as f:
                writer = csv.writer(f, delimiter="\t")
                data = sorted(mws.items(), key=lambda x: x[1])
                for row in data:
                    writer.writerow(row)

        self.debug("Mol weights {}".format(mws))
        self.molecular_weights = mws

    def load_detectors(self):
        """
        load setupfiles/spectrometer/detectors.cfg
        populates self.detectors
        :return:
        """
        ypath = os.path.join(paths.spectrometer_dir, "detectors.yaml")
        if not os.path.isfile(ypath):
            cpath = os.path.join(paths.spectrometer_dir, "detectors.cfg")
            if not os.path.isfile(cpath):
                self.warning_dialog(
                    'Could not find a detectors file. Please add "{}"'.format(ypath)
                )
                return
            else:
                self._load_detectors_cfg(cpath)
                self._dump_detectors_yaml(ypath)
        else:
            self._load_detectors_yaml(ypath)

    def _dump_detectors_yaml(self, ypath):
        self.information_dialog(
            'Automatically migrating "detectors.cfg" to "detectors.yaml"'
        )
        with open(ypath, "w") as wfile:
            dets = [di.toyaml() for di in self.detectors]
            yaml.dump(dets, wfile)

    def _load_detectors_yaml(self, ypath):
        self.debug("loading detectors yaml {}".format(ypath))
        with open(ypath, "r") as rfile:
            for i, det in enumerate(yaml.load(rfile, Loader=SafeLoader)):
                name = det.get("name")
                software_gain = float(det.get("software_gain", 1.0))

                color = det.get("color", "black")
                default_state = bool(det.get("default_state", True))
                isotope = det.get("isotope", "")
                kind = det.get("kind", "Faraday")
                pt = det.get("protection_threshold", 0)
                serial_id = str(det.get("serial_id", "00000"))
                index = float(det.get("index", i))
                units = det.get("units", "fA")

                use_deflection = bool(det.get("use_deflection", True))
                deflection_correction_sign = 1
                if use_deflection:
                    deflection_correction_sign = det.get(
                        "deflection_correction_sign", 1
                    )

                deflection_name = det.get("deflection_name", name)
                ypadding = str(det.get("ypadding", "0.1"))

                self._add_detector(
                    name=name,
                    index=index,
                    software_gain=software_gain,
                    serial_id=serial_id,
                    use_deflection=use_deflection,
                    protection_threshold=pt,
                    deflection_correction_sign=deflection_correction_sign,
                    deflection_name=deflection_name,
                    color=color,
                    active=default_state,
                    isotope=isotope,
                    kind=kind,
                    units=units,
                    ypadding=ypadding,
                )

    def _load_detectors_cfg(self, path):
        try:
            config = self.get_configuration(path=path)
        except BaseException:
            self.warning_dialog(
                'There is an issue with your detectors file. Please fix "{}"'.format(
                    path
                )
            )
            return

        for i, name in enumerate(config.sections()):
            relative_position = self.config_get(
                config, name, "relative_position", cast="float"
            )
            software_gain = self.config_get(
                config, name, "software_gain", cast="float", default=1.0
            )

            color = self.config_get(config, name, "color", default="black")
            default_state = self.config_get(
                config, name, "default_state", default=True, cast="boolean"
            )
            isotope = self.config_get(config, name, "isotope")
            kind = self.config_get(
                config, name, "kind", default="Faraday", optional=True
            )
            pt = self.config_get(
                config,
                name,
                "protection_threshold",
                default=None,
                optional=True,
                cast="float",
            )
            serial_id = self.config_get(config, name, "serial_id", default="00000")

            index = self.config_get(config, name, "index", cast="float")
            if index is None:
                index = i

            use_deflection = self.config_get(
                config, name, "use_deflection", cast="boolean", optional=True
            )
            if use_deflection is None:
                use_deflection = True

            deflection_correction_sign = 1
            if use_deflection:
                deflection_correction_sign = self.config_get(
                    config, name, "deflection_correction_sign", cast="int"
                )

            deflection_name = self.config_get(
                config, name, "deflection_name", optional=True, default=name
            )
            ypadding = self.config_get(
                config, name, "ypadding", optional=True, default="0.1"
            )

            self._add_detector(
                name=name,
                index=index,
                software_gain=software_gain,
                serial_id=serial_id,
                relative_position=relative_position,
                use_deflection=use_deflection,
                protection_threshold=pt,
                deflection_correction_sign=deflection_correction_sign,
                deflection_name=deflection_name,
                color=color,
                active=default_state,
                isotope=isotope,
                kind=kind,
                ypadding=ypadding,
            )

    def get_intensities(
        self, tagged=True, trigger=False, integrated_intensity=False, **kw
    ):
        """
        keys, list of strings
        signals, list of floats::

            keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
            signals = [10,100,1,0.1,1,0.001]

        :param tagged:
        :return: keys, signals
        """
        keys = []
        signals = []
        t = None
        inc = True
        if self.microcontroller and not self.microcontroller.simulation:
            while 1:
                keys, signals, t, inc = self.read_intensities(trigger=trigger, **kw)
                if integrated_intensity:
                    if inc:
                        break
                else:
                    break

        if not keys and globalv.communication_simulation:
            keys, signals, t = self._get_simulation_data()

        signals = array(signals)

        self._check_intensity_no_change(signals)

        gsignals = []
        for k, v in zip(keys, signals):
            det = self.get_detector(k)
            det.set_intensity(v)
            gsignals.append(v * det.software_gain)

        return keys, array(gsignals), t, inc

    def _handle_no_intensity_change(self):
        pass

    def _check_intensity_no_change(self, signals):
        if self.simulation:
            return

        if self._no_intensity_change_cnt > 25:
            self._no_intensity_change_cnt = 0
            self._prev_signals = None
            raise NoIntensityChange()

        if signals is None:
            self._no_intensity_change_cnt += 1
            self._handle_no_intensity_change()

        elif self._prev_signals is not None:
            try:
                test = (signals == self._prev_signals).all()
            except (AttributeError, TypeError):
                test = True

            if test:
                self.debug(
                    "no intensity change cnt= {}".format(self._no_intensity_change_cnt)
                )
                self.debug("signals={}".format(signals))
                self.debug("prev_signals={}".format(self._prev_signals))

                self._no_intensity_change_cnt += 1
            else:
                if self._no_intensity_change_cnt > 0:
                    self.debug("resetting no_intensity_change_cnt")
                    self.debug("signals={}".format(signals))
                    self.debug("prev_signals={}".format(self._prev_signals))

                self._no_intensity_change_cnt = 0
                self._prev_signals = None

        self._prev_signals = signals

    def settle(self):
        import time

        time.sleep(self.integration_time)

    def get_intensity(self, dkeys, integrated_intensity=True, **kw):
        """
        dkeys: str or tuple of strs

        """
        try:
            keys, signals, t, inc = self.get_intensities(
                integrated_intensity=integrated_intensity
            )
        except ValueError:
            self.debug("failed getting intensities")
            self.debug_exception()
            return

        def func(k):
            return signals[keys.index(k)] if k in keys else 0

        if isinstance(dkeys, (tuple, list)):
            return [func(key) for key in dkeys]
        else:
            return func(dkeys)

    def get_detector(self, name):
        """
        get Detector object by name

        :param name: str
        :return: Detector
        """

        if isinstance(name, BaseDetector):
            return name
        else:
            if name.endswith("_"):
                name = "{})".format(name[:-1])
                name = name.replace("_", "(")

            return next((det for det in self.detectors if det.name == name), None)

    def read_intensities(self):
        raise NotImplementedError

    def read_deflection_word(self, *args, **kw):
        return []

    def get_configuration_value(self, *args, **kw):
        pass

    def get_hardware_name(self, *args, **kw):
        pass

    def read_parameter_word(self):
        pass

    def clear_cached_config(self):
        self._config = None

    # private
    def _spectrometer_configuration_changed(self, new):
        if new:
            set_spectrometer_config_name(new)
            self.clear_cached_config()

    def _add_detector(self, **kw):
        d = self.detector_klass(
            spectrometer=self, microcontroller=self.microcontroller, **kw
        )
        d.load()
        self.detectors.append(d)

    def _magnet_default(self):
        return self.magnet_klass(
            spectrometer=self, microcontroller=self.microcontroller
        )

    def _source_default(self):
        return self.source_klass(
            spectrometer=self, microcontroller=self.microcontroller
        )

    def _microcontroller_default(self):
        mc = self.microcontroller_klass(name="spectrometer_microcontroller")
        mc.bootstrap()
        return mc

    @cached_property
    def _get_isotopes(self):
        return sorted(self.molecular_weights.keys())

    @property
    def detector_names(self):
        return [di.name for di in self.detectors]


# ============= EOF =============================================
