# ===============================================================================
# Copyright 2014 Jake Ross
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
from __future__ import absolute_import

import os
import time
import uuid
from threading import Thread

from traits.api import HasTraits, Instance, Str, Dict, Property, Bool, Float, Any

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.core.yaml import yload
from pychron.experiment.utilities.runid import make_runid
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
from pychron.pyscripts.measurement.thermo_measurement_pyscript import (
    ThermoSynMeasurementPyScript,
)
from pychron.pyscripts.measurement_pyscript import MeasurementPyScript


class SynExtractionCTX:
    def __init__(self, run, syn_script):
        self.run = run
        self.oscript = run.measurement_script
        self.run.measurement_script = syn_script

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.run.measurement_script = self.oscript


class SynExtractionSpec(HasTraits):
    # mode = Str
    # duration = Float
    #
    config = Dict

    def __getattr__(self, item):
        default = None
        if item in self.config:
            if item in ("delay_between", "end_threshold"):
                default = 0
            return self.config.get(item, default)

    #
    # end_threshold = Property
    # script = Property
    # post_measurement_script = Property
    # identifier = Property
    # delay_between = Property
    #
    # def _get_script(self):
    #     return self._get_script_value("measurement")
    #
    # def _get_post_measurement_script(self):
    #     return self._get_script_value("post_measurement")
    #
    # def _get_script_value(self, attr):
    #     name = self._get_value(attr, "")
    #     p = add_extension(name, ".py")
    #     p = os.path.join(paths.scripts_dir, attr, p)
    #     return p
    #
    # def _get_delay_between(self):
    #     return self._get_value("delay_between", 0)
    #
    # def _get_end_threshold(self):
    #     return self._get_value("end_threshold", 0)
    #
    # def _get_identifier(self):
    #     return self._get_value("identifier")
    #
    # def _get_value(self, attr, default=None):
    #     if self.config:
    #         return self.config.get(attr, default)
    #     else:
    #         return default


class SynExtractionCollector(Loggable):
    arun = Instance("pychron.experiment.automated_run.automated_run.AutomatedRun")
    path = Str
    _alive = Bool(False)

    extraction_duration = Float
    persister = None
    persister_use_massspec_database = Bool(False)
    executor = Any

    def start(self):
        self.persister_use_massspec_database = self.arun.persister.use_massspec_database
        self.arun.persister.trait_set(use_massspec_database=False)

        yd = self._load_config()
        if yd:
            self.info("Start syn extraction {}".format(self.path))
            self._alive = True
            t = Thread(target=self._do_collection, args=(yd,))
            t.start()
        else:
            self.warning(
                "No configuration available for SynExtraction data collection. "
                "{} was not found".format(self.path)
            )

    def stop(self):
        self._alive = False
        # return the persister to its original configuration
        # if self.persister:
        #     self.arun.persister = self.persister
        if self.arun:
            self.arun.persister.trait_set(
                use_massspec_database=self.persister_use_massspec_database
            )

    def _do_collection(self, cfg):
        self.info("Starting syn extraction collection")

        # clone the persister
        # self.persister = self.arun.persister.clone_traits()

        spec = SynExtractionSpec(config=cfg)
        # script = self._setup_script(spec)
        script = self._setup_script(spec)
        if not script:
            return
        script, post_script = script
        if not self._do_syn_extract(spec, script, post_script):
            self.debug("do syn extraction failed")
            return

        self.info("Syn Extraction finished")

        # gen = self._spec_generator(cfg)
        # starttime = time.time()
        # while self._alive:
        #     et = time.time() - starttime
        #     spec = next(gen)
        #     if not spec:
        #         self.warning("Failed getting a syn extraction spec")
        #         break
        #
        #     script = self._setup_script(spec)
        #     if not script:
        #         break
        #
        #     script, post_script = script
        #
        #     if spec.mode == "static":
        #         rem = self.extraction_duration - spec.end_threshold - et
        #         if spec.duration > rem:
        #             self.debug(
        #                 "not enough time to start another static run."
        #                 "Run Duration={} Remaining={} "
        #                 "ExtDuration={} Threshold={} ElapsedTime={}".format(
        #                     spec.duration,
        #                     rem,
        #                     self.extraction_duration,
        #                     spec.end_threshold,
        #                     et,
        #                 )
        #             )
        #             break
        #         else:
        #             if not self._do_syn_extract(spec, script, post_script):
        #                 self.debug("do syn extraction failed")
        #                 break
        #     else:
        #         if et > self.extraction_duration - spec.end_threshold:
        #             self.debug(
        #                 "Syn Extraction finished"
        #                 "Run Duration={} Remaining={} "
        #                 "ExtDuration={} Threshold={} ElapsedTime={}".format(
        #                     spec.duration,
        #                     self.extraction_duration,
        #                     spec.end_threshold,
        #                     et,
        #                 )
        #             )
        #             break
        #         else:
        #             if not self._do_syn_extract(spec, script, post_script):
        #                 self.debug("do syn extraction failed")
        #                 break
        #
        # self.info("Syn Extraction finished")

    def _setup_script(self, spec):
        p = spec.measurement
        p = add_extension(p, ".py")
        for p in (p, os.path.join(paths.measurement_dir, p)):
            if p and os.path.isfile(p):
                self.debug('measurement script "{}"'.format(p))
                root = os.path.dirname(p)
                sname = os.path.basename(p)

                # setup the script
                ms = ThermoSynMeasurementPyScript(
                    root=root, name=sname, automated_run=self.arun
                )
                self.arun.baseline_modifiers = spec.baseline_modifiers
                if ms.bootstrap():
                    if ms.syntax_ok(warn=False):
                        # spec.duration = ms.get_estimated_duration()
                        pms = None
                        p = spec.post_measurement
                        if p and os.path.isfile(p):
                            self.debug('measurement script "{}"'.format(p))
                            pms = ExtractionPyScript(
                                root=os.path.dirname(p), name=os.path.basename(p)
                            )
                        return ms, pms
                    else:
                        self.debug("invalid syntax {}".format(ms.name))
        else:
            self.debug('invalid measurement script "{}"'.format(p))

    def _do_syn_extract(self, spec, script, post_script):
        self.debug('Executing SynExtraction mode="{}"'.format(spec.mode))

        # modify the persister. the original persister for the automated run is saved at self.persister
        # arun.persister reset to original when syn extraction stops
        # identifier = spec.identifier
        # last_aq = self.arun.persister.get_last_aliquot(identifier)
        # if last_aq is None:
        #     self.warning(
        #         'invalid identifier "{}". Does not exist in database'.format(identifier)
        #     )
        #
        # else:
        #     runid = make_runid(identifier, last_aq + 1)
        #     self.arun.info("Starting SynExtraction run {}".format(runid))
        #     self.arun.persister.trait_set(
        #         use_massspec_database=False, runid=runid, uuid=str(uuid.uuid4())
        #     )
        # oscript = self.arun.measurement_script
        # self.debug(f'oscript {oscript}')

        with SynExtractionCTX(self.arun, script):
            # self.arun.measurement_script = script
            try:
                if self.executor.syn_measure(self.arun, script):
                    # if self.arun.do_measurement(script=script, use_post_on_fail=False):
                    if post_script:
                        self.debug("starting post measurement")
                        if not self.arun.do_post_measurement(script=post_script):
                            return

                    # self.debug(
                    #     "delay between syn extractions {}".format(spec.delay_between)
                    # )
                    # self.arun.wait(spec.delay_between or 0)
                    # self.arun.measurement_script = oscript
                    # self.debug(f'setting {self.arun} {oscript}')
                    return True
                # else:
                #     self.arun.measurement_script = oscript

            except BaseException as e:
                self.debug(f"failed doing measurement {e}")
        # finally:
        #     self.arun.measurement_script = oscript

    # def _spec_generator(self, config):
    #     pattern = config.get("pattern", "S")
    #
    #     def gen():
    #         while 1:
    #             for p in pattern:
    #                 if p == "S":
    #                     yield self._static_spec_factory(config)
    #                 else:
    #                     yield self._dynamic_spec_factory(config)
    #
    #     return gen()

    def _load_config(self):
        p = self.path
        if os.path.isfile(p):
            return yload(p)

    # def _static_spec_factory(self, config):
    #     config = config.get("static")
    #     if config:
    #         s = SynExtractionSpec(mode="static", config=config)
    #         return s
    #     else:
    #         self.debug("no static in configuration file")
    #
    # def _dynamic_spec_factory(self, config):
    #     config = config.get("dynamic")
    #     if config:
    #         s = SynExtractionSpec(mode="dynamic", config=config)
    #         return s
    #     else:
    #         self.debug("no dynamic in configuration file")


# ============= EOF =============================================
