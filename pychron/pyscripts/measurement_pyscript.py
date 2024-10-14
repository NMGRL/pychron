# ===============================================================================
# Copyright 2012 Jake Ross
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
# ============= standard library imports ========================

import ast
import os
import time
from configparser import ConfigParser

import yaml

from pychron.core.helpers.filetools import fileiter
from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.pychron_constants import MEASUREMENT_COLOR
from pychron.pyscripts.contexts import MeasurementCTXObject
from pychron.pyscripts.decorators import verbose_skip, count_verbose_skip, makeRegistry
from pychron.pyscripts.valve_pyscript import ValvePyScript
from pychron.spectrometer import (
    get_spectrometer_config_path,
    set_spectrometer_config_name,
)

ESTIMATED_DURATION_FF = 1.0

command_register = makeRegistry()

from pychron.pyscripts.automated_run_pyscript import AutomatedRunPyScript


class MeasurementPyScript(AutomatedRunPyScript):
    """
    MeasurementPyScripts are used to collect isotopic data
    """

    ncounts = 0
    info_color = MEASUREMENT_COLOR
    abbreviated_count_ratio = None

    hops_name = ""
    hops_blob = ""
    _time_zero = None
    _time_zero_offset = 0

    _series_count = 0
    _baseline_series = None

    _fit_series_count = 0

    def abort(self):
        if not self.is_aborted():
            super(MeasurementPyScript, self).abort()
            self._automated_run_call("abort_run", do_post_equilibration=False)

    def gosub(self, *args, **kw):
        kw["automated_run"] = self.automated_run
        s = super(MeasurementPyScript, self).gosub(*args, **kw)
        if s:
            s.automated_run = None
        return s

    def reset(self, arun):
        """
        Reset the script with a new automated run

        :param arun: A new ``AutomatedRun``
        :type arun: ``AutomatedRun``
        """
        self.debug("%%%%%%%%%%%%%%%%%% setting automated run {}".format(arun.runid))
        self.automated_run = arun
        self._reset()

    def get_command_register(self):
        cs = super().get_command_register()
        return cs + list(command_register.commands.items())

    def truncate(self, style=None):
        if style == "quick":
            self.abbreviated_count_ratio = 0.25
        super(MeasurementPyScript, self).truncate(style=style)

    def get_variables(self):
        return [
            "truncated",
            "eqtime",
            "use_cdd_warming",
            "analysis_type",
            "identifier",
            "runid",
        ]

    def increment_series_counts(self, s, f):
        self._series_count += s
        self._fit_series_count += f

    def reset_series(self):
        self._series_count = 0
        self._fit_series_count = 0

    # ===============================================================================
    # commands
    # ===============================================================================
    @verbose_skip
    @command_register
    def sink_data(self, n=100, delay=1, root=None, buffer_delay=5, calc_time=False):
        """

        @param n: number of measurements
        @param period: delay between measurements
        @param calc_time:
        @return:
        """
        if calc_time:
            return n * delay
        self._automated_run_call(
            "py_sink_data", n=n, delay=delay, root=root, buffer_delay=buffer_delay
        )

    @verbose_skip
    @command_register
    def measurement_delay(self, duration=None, message=None):
        if duration:
            try:
                self.automated_run.plot_panel.total_counts += round(duration)
            except AttributeError:
                pass

            self.sleep(duration, message=message)

    @verbose_skip
    @command_register
    def generate_ic_mftable(
        self, detectors, refiso="Ar40", peak_center_config="", n=1, calc_time=False
    ):
        """
        Generate an IC MFTable. Use this when doing a Detector Intercalibration.
        peak centers the ``refiso`` on a list of ``detectors``. MFTable saved as ic_mftable

        cancel script if generating mftable fails

        :param detectors: list of detectors to peak center
        :type detectors: list
        :param refiso: isotope to peak center
        :type refiso: str
        """

        if calc_time:
            self._estimated_duration += (len(detectors) * 30) * n
            return

        if not self._automated_run_call(
            "py_generate_ic_mftable", detectors, refiso, peak_center_config, n
        ):
            self.cancel()

    @verbose_skip
    @command_register
    def generate_peakhop_mftable(
        self, pairs, peak_center_config="", n=1, calc_time=False
    ):
        """
        Generate an Peakhop MFTable.

        cancel script if generating mftable fails

        :param detectors: list of detectors to peak center
        :type detectors: list
        :param refiso: isotope to peak center
        :type refiso: str
        """

        if calc_time:
            self._estimated_duration += (len(pairs) * 30) * n
            return

        if not self._automated_run_call(
            "py_generate_peakhop_mftable", pairs, peak_center_config, n
        ):
            self.cancel()

    @verbose_skip
    @command_register
    def extraction_gosub(self, *args, **kw):
        kw["klass"] = "ExtractionPyScript"
        super(MeasurementPyScript, self).gosub(*args, **kw)

    @count_verbose_skip
    @command_register
    def measure_equilibration(self, *args, **kw):
        self.sniff(*args, **kw)

    @count_verbose_skip
    @command_register
    def sniff(self, ncounts=0, calc_time=False, integration_time=1.04, block=True):
        """
        collect a sniff measurement. Sniffs are the measurement of the equilibration gas.

        :param ncounts: Number of counts
        :type ncounts: int
        :param integration_time: integration time in seconds
        :type integration_time: float
        :param block: Is this call blocking or should it return immediately
        :type block: bool
        """

        if calc_time:
            self._estimated_duration += (
                ncounts * integration_time * ESTIMATED_DURATION_FF
            )
            return
        self.ncounts = ncounts
        if not self._automated_run_call(
            "py_sniff",
            ncounts,
            self._time_zero,
            self._time_zero_offset,
            series=self._series_count,
            block=block,
        ):
            self.cancel()

    @count_verbose_skip
    @command_register
    def multicollect(self, ncounts=200, integration_time=1.04, calc_time=False):
        """
        Do a multicollection. Measure all detectors setup using ``activate_detectors``

        :param ncounts: Number of counts
        :type ncounts: int
        :param integration_time: integration time in seconds
        :type integration_time: float
        """

        if self.abbreviated_count_ratio:
            ncounts *= self.abbreviated_count_ratio

        if calc_time:
            self._estimated_duration += (
                ncounts * integration_time * ESTIMATED_DURATION_FF
            )
            return

        self.ncounts = ncounts
        # set self.ncounts before applying abbreviated_count_ratio
        # if self.abbreviated_count_ratio:
        #    ncounts *= self.abbreviated_count_ratio

        if not self._automated_run_call(
            "py_data_collection",
            self,
            ncounts,
            self._time_zero,
            self._time_zero_offset,
            fit_series=self._fit_series_count,
            series=self._series_count,
            integration_time=integration_time,
        ):
            self.cancel()

    @count_verbose_skip
    @command_register
    def baselines(
        self,
        ncounts=1,
        mass=None,
        detector="",
        use_dac=False,
        integration_time=1.04,
        settling_time=4,
        check_conditionals=True,
        calc_time=False,
    ):
        """
        Measure the baseline for all detectors. Position ion beams using mass and detector

        :param ncounts: Number of counts
        :type ncounts: int
        :param mass: Mass to measure baseline in amu
        :type mass: float
        :param detector: name of detector
        :type detector: str
        :param use_dac: If True interpret mass as a DAC value instead of amu
        :type use_dac: bool
        :param integration_time: integration time in seconds
        :type integration_time: float
        :param settling_time: delay between magnet positioning and measurement in seconds
        :type settling_time: float

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

        if not self._automated_run_call(
            "py_baselines",
            ncounts,
            self._time_zero,
            self._time_zero_offset,
            mass,
            detector,
            check_conditionals=check_conditionals,
            use_dac=use_dac,
            fit_series=self._fit_series_count,
            settling_time=settling_time,
            series=series,
            integration_time=integration_time,
        ):
            self.cancel()
        self._baseline_series = series

    @count_verbose_skip
    @command_register
    def load_hops(self, p, *args, **kw):
        """
        load the hops definition from a file

        :param p: path. absolute or relative to this scripts root
        :return: hops
        :rtype: list of tuples
        """
        if not os.path.isfile(p):
            p = os.path.join(self.root, p)

        if os.path.isfile(p):
            self.hops_name = os.path.basename(p)

            with open(p, "r") as rfile:
                self.hops_blob = rfile.read()

            with open(p, "r") as rfile:
                head, ext = os.path.splitext(p)
                if ext in (".yaml", ".yml"):
                    hops = yload(rfile)
                elif ext in (".txt",):

                    def hop_factory(l):
                        pairs, counts, settle = eval(l)

                        # isos, dets = zip(*(p.split(':') for p in pairs.split(',')))
                        # items = (p.split(':') for p in pairs.split(','))
                        items = []
                        for p in pairs.split(","):
                            args = p.split(":")
                            defl = args[2] if len(args) == 3 else None
                            items.append((args[0], args[1], defl))

                        # n = len(isos)
                        cc = [
                            {
                                "isotope": i,
                                "detector": d,
                                "active": True,
                                "deflection": de,
                                "is_baseline": False,
                                "protect": False,
                            }
                            for i, d, de in items
                        ]

                        h = {
                            "counts": counts,
                            "settle": settle,
                            "cup_configuration": cc,
                            "positioning": {
                                "detector": cc[0]["detector"],
                                "isotope": cc[0]["isotope"],
                            },
                        }
                        return h

                    hops = [hop_factory(li) for li in fileiter(rfile)]
                return hops

        else:
            self.warning_dialog("No such file {}".format(p))

    @count_verbose_skip
    @command_register
    def define_detectors(self, isotope, det, *args, **kw):
        self._automated_run_call("py_define_detectors", isotope, det)

    @count_verbose_skip
    @command_register
    def define_hops(self, hops=None, **kw):
        if not hops:
            return

        self._automated_run_call("py_define_hops", hops)

    @count_verbose_skip
    @command_register
    def peak_hop(self, ncycles=5, hops=None, mftable=None, calc_time=False):
        """
        Peak hop ion beams. Hops usually defined in a separate file.
        if mftable == 'ic_mftable' use the ic_mftable generated during detector intercalibration.


        :param ncycles: int, number of cycles
        :param hops: list of tuples, defined in a hops file
        :param mftable: str
        """
        if not hops:
            return

        integration_time = 1.1

        counts = (
            sum([h["counts"] * integration_time + h["settle"] for h in hops]) * ncycles
        )
        if calc_time:
            # counts = sum of counts for each hop
            self._estimated_duration += counts * ESTIMATED_DURATION_FF
            return

        group = "signal"
        self.ncounts = counts
        if not self._automated_run_call(
            "py_peak_hop",
            ncycles,
            counts,
            hops,
            mftable,
            self._time_zero,
            self._time_zero_offset,
            self._series_count,
            fit_series=self._fit_series_count,
            group=group,
        ):
            self.cancel()
            # self._series_count += 2
            # self._fit_series_count += 1

    @verbose_skip
    @command_register
    def peak_center(
        self,
        detector="",
        isotope="",
        integration_time=1.04,
        save=True,
        calc_time=False,
        directions="Increase",
        config_name="default",
    ):
        """
        Calculate the peak center for ``isotope`` on ``detector``.

        :param detector: str
        :param isotope: str
        :param integration_time: float
        :param save: bool
        """

        if calc_time:
            n = 31
            self._estimated_duration += n * integration_time * 2
            return

        self._automated_run_call(
            "py_peak_center",
            detector=detector,
            isotope=isotope,
            integration_time=integration_time,
            directions=directions,
            save=save,
            config_name=config_name,
        )

    @verbose_skip
    @command_register
    def get_intensity(self, name):
        v = self._automated_run_call("py_get_intensity", detector=name)

        # ensure the script always gets a number
        return 0 or v

    @verbose_skip
    @command_register
    def whiff(self, ncounts=0, conditionals=None):
        """
        Do a whiff measurement.

        Whiff's are quick measurements with conditionals. use them to take action at
        the beginning of a measurement. For example do a whiff to determine if intensity
        to great.

        :param ncounts: int
        :param conditionals: list of dicts

        """
        self.ncounts = ncounts
        ret = self._automated_run_call(
            "py_whiff",
            ncounts,
            conditionals,
            self._time_zero,
            self._time_zero_offset,
            fit_series=self._fit_series_count,
            series=self._series_count,
        )
        return ret

    @verbose_skip
    @command_register
    def reset_measurement(self, detectors=None):
        if detectors:
            self.reset_data()
            self.activate_detectors(*detectors)
            try:
                self.automated_run.plot_panel.total_counts = 0
                self.automated_run.plot_panel.total_seconds = 0
            except AttributeError:
                pass

            self._reset()

    @verbose_skip
    @command_register
    def reset_data(self):
        self._automated_run_call("py_reset_data")

    @verbose_skip
    @command_register
    def post_equilibration(self, block=False):
        """
        Run the post equilibration script.

        """

        self._automated_run_call("py_post_equilibration", block=block)

    @verbose_skip
    @command_register
    def equilibrate(
        self,
        eqtime=20,
        inlet=None,
        outlet=None,
        do_post_equilibration=True,
        close_inlet=True,
        delay=3,
    ):
        """
        equilibrate the extraction line with the mass spectrometer

        inlet or outlet can be a single valve name or a list of valve names. ::

            'A', ('A','B'), ['A','B'], 'A,B'

        :param eqtime: int, equilibration duration in seconds
        :param inlet: str, tuple or list, inlet valve
        :param outlet: str, tuple or list, ion pump valve
        :param do_post_equilibration: bool
        :param close_inlet: bool
        :param delay: int, delay in seconds between close of outlet and open of inlet

        """
        ok = self._automated_run_call(
            "py_equilibration",
            eqtime=eqtime,
            inlet=inlet,
            outlet=outlet,
            do_post_equilibration=do_post_equilibration,
            close_inlet=close_inlet,
            delay=delay,
        )

        if not ok:
            self.cancel()
        # else:
        # wait for inlet to open
        # evt.wait()

    @verbose_skip
    @command_register
    def set_fits(self, *fits):
        """
        set time vs intensity regression fits for isotopes

        :param fits: str, list, or tuple

        """
        self._automated_run_call("py_set_fits", fits)

    @verbose_skip
    @command_register
    def set_baseline_fits(self, *fits):
        """
        set baseline fits for detectors

        :param fits:
        """
        self._automated_run_call("py_set_baseline_fits", fits)

    @verbose_skip
    @command_register
    def activate_detectors(self, *dets, **kw):
        """
        set the active detectors

        :param dets: list

        """
        peak_center = kw.get("peak_center", False)

        if dets:
            self._automated_run_call(
                "py_activate_detectors", list(dets), peak_center=peak_center
            )

    @verbose_skip
    @command_register
    def position_hv(self, pos, detector="AX"):
        self._automated_run_call("py_position_hv", pos, detector)

    @verbose_skip
    @command_register
    def position_magnet(self, pos, detector="AX", use_dac=False, for_collection=True):
        """

        :param pos: location to set magnetic field
        :type pos: str, float
        :param detector: detector to position ``pos``
        :type pos: str
        :param use_dac: is the ``pos`` a DAC voltage
        :type use_dac: bool

        examples::

            position_magnet(4.54312, use_dac=True) # detector is not relevant
            position_magnet(39.962, detector='AX')
            position_magnet('Ar40', detector='AX') #Ar40 will be converted to 39.962 use mole weight dict

        """
        self._automated_run_call(
            "py_position_magnet",
            pos,
            detector,
            use_dac=use_dac,
            for_collection=for_collection,
        )

    @verbose_skip
    @command_register
    def coincidence(self):
        """
        Do a coincidence scan. Peak center all active detectors simulatenously.
        calculate required deflection corrections to bring all detectors into
        coincidence

        """
        self._automated_run_call("py_coincidence_scan")

    # ===============================================================================
    #
    # ===============================================================================

    # ===============================================================================
    # set commands
    # ===============================================================================

    @verbose_skip
    @command_register
    def is_last_run(self):
        return self._automated_run_call("py_is_last_run")

    @verbose_skip
    @command_register
    def clear_conditionals(self):
        self._automated_run_call("py_clear_conditionals")

    @verbose_skip
    @command_register
    def clear_terminations(self):
        self._automated_run_call("py_clear_terminations")

    @verbose_skip
    @command_register
    def clear_truncations(self):
        self._automated_run_call("py_clear_truncations")

    @verbose_skip
    @command_register
    def clear_actions(self):
        self._automated_run_call("py_clear_actions")

    @verbose_skip
    @command_register
    def add_termination(
        self, attr, teststr, start_count=0, frequency=10, window=0, mapper="", ntrips=1
    ):
        self._automated_run_call(
            "py_add_termination",
            attr=attr,
            teststr=teststr,
            start_count=start_count,
            frequency=frequency,
            window=window,
            mapper=mapper,
            ntrips=ntrips,
        )

    @verbose_skip
    @command_register
    def add_cancelation(
        self, attr, teststr, start_count=0, frequency=10, window=0, mapper="", ntrips=1
    ):
        self._automated_run_call(
            "py_add_cancelation",
            attr=attr,
            teststr=teststr,
            start_count=start_count,
            frequency=frequency,
            window=window,
            mapper=mapper,
            ntrips=ntrips,
        )

    @verbose_skip
    @command_register
    def add_truncation(
        self,
        attr,
        teststr,
        start_count=0,
        frequency=10,
        ntrips=1,
        abbreviated_count_ratio=1.0,
    ):
        self._automated_run_call(
            "py_add_truncation",
            attr=attr,
            teststr=teststr,
            start_count=start_count,
            frequency=frequency,
            abbreviated_count_ratio=abbreviated_count_ratio,
            ntrips=ntrips,
        )

    @verbose_skip
    @command_register
    def add_action(
        self,
        attr,
        teststr,
        start_count=0,
        frequency=10,
        ntrips=1,
        action=None,
        resume=False,
    ):
        self._automated_run_call(
            "py_add_action",
            attr=attr,
            teststr=teststr,
            start_count=start_count,
            frequency=frequency,
            action=action,
            resume=resume,
            ntrips=ntrips,
        )

    @verbose_skip
    @command_register
    def set_ncounts(self, ncounts=0):
        try:
            ncounts = int(ncounts)
            self.ncounts = ncounts
        except Exception as e:
            print("set_ncounts", e)

    @verbose_skip
    @command_register
    def set_time_zero(self, offset=0):
        """
        set the time_zero value.
        add offset to time_zero ::

            T_o= ion pump closes
            offset seconds after T_o. define time_zero

            T_eq= inlet closes

        """
        self._time_zero = time.time() + offset
        self._time_zero_offset = offset

    @verbose_skip
    @command_register
    def set_integration_time(self, v):
        """
        Set the integration time

        :param v: integration time in seconds
        :type v: float
        """
        self._automated_run_call("py_set_integration_time", v)

    @verbose_skip
    @command_register
    def raw_spectrometer_command(self, command):
        self._automated_run_call("py_raw_spectrometer_command", command)

    @verbose_skip
    @command_register
    def set_spectrometer_configuration(self, name):
        set_spectrometer_config_name(name)
        self._automated_run_call("py_clear_cached_configuration")
        self._automated_run_call("py_send_spectrometer_configuration")

    @verbose_skip
    @command_register
    def set_isotope_group(self, name):
        self._automated_run_call("py_set_isotope_group", name)

    @property
    def runid(self):
        return self.automated_run.runid

    @property
    def identifier(self):
        return self.automated_run.spec.labnumber

    @property
    def analysis_type(self):
        return self.automated_run.spec.analysis_type

    @property
    def truncated(self):
        """
        Property. True if run was truncated otherwise False

        :return: bool
        """
        return (
            self._automated_run_call(lambda: self.automated_run.truncated)
            or self.is_truncated()
        )

    @property
    def eqtime(self):
        """
        Property. Equilibration time. Get value from ``AutomatedRun``.

        :return: float, int
        """
        r = 20
        if self.automated_run:
            r = self.automated_run.eqtime

            if r == -1:
                r = 20
                cg = self._get_config()
                if cg.has_option("Default", "eqtime"):
                    r = cg.getfloat(
                        "Default",
                        "eqtime",
                    )
        return r

    @property
    def time_zero_offset(self):
        """
        Property. Substract ``time_zero_offset`` from time value for all data points

        :return: float, int
        """
        if self.automated_run:
            return self.automated_run.time_zero_offset
            # return self._automated_run_call(lambda: self.automated_run.time_zero_offset)
        else:
            return 0

    @property
    def use_cdd_warming(self):
        """
        Property. Use CDD Warming. Get value from ``AutomatedRunSpec``

        :return: bool
        """
        if self.automated_run:
            return self.automated_run.spec.use_cdd_warming
            # return self._automated_run_call(lambda: self.automated_run.spec.use_cdd_warming)

    def set_default_context(self, **kw):
        if "analysis_type" not in kw:
            kw["analysis_type"] = ""

        self.setup_context(**kw)

    # private
    def _get_deflection_from_file(self, name):
        config = self._get_config()
        section = "Deflections"
        dets = config.options(section)
        for dn in dets:
            if dn.lower() == name.lower():
                return config.getfloat(section, dn)

    def _set_from_file(self, section, **user_params):
        func = self._set_spectrometer_parameter
        config = self._get_config()
        for name, value in config.items(section):
            if name in user_params:
                value = user_params[name]
            func(name, value)

        # for attr in attrs:
        #     if attr in user_params:
        #         v = user_params[attr]
        #     else:
        #         v = config.getfloat(section, attr)
        #
        #     if v is not None:
        #         func('SetParameter {}'.format(attr), v)

    def _get_config(self):
        config = ConfigParser()
        try:
            p = get_spectrometer_config_path()
        except IOError:
            p = os.path.join(paths.spectrometer_dir, "config.cfg")

        config.read(p)

        return config

    def _set_spectrometer_parameter(self, *args, **kw):
        self._automated_run_call("py_set_spectrometer_parameter", *args, **kw)

    def _get_spectrometer_parameter(self, *args, **kw):
        return self._automated_run_call("py_get_spectrometer_parameter", *args, **kw)

    def _setup_docstr_context(self):
        """
        add a context object to the global script context
        e.g access measurement configuration values such as counts using
            mx.counts

        """
        try:
            m = ast.parse(self.text)
            try:
                yd = yload(ast.get_docstring(m))
                if yd:
                    mx = MeasurementCTXObject()
                    mx.create(yd)
                    self._ctx["mx"] = mx

            except yaml.YAMLError as e:
                self.debug("failed loading docstring context. {}".format(e))
        except AttributeError:
            pass

    def _reset(self):
        self._baseline_series = None
        self._series_count = 0
        self._fit_series_count = 0
        self._time_zero = None

        self.abbreviated_count_ratio = None
        self.ncounts = 0


# ============= EOF =============================================
