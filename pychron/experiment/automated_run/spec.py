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

import hashlib
import uuid
from datetime import datetime

# ============= enthought library imports =======================
from traits.api import (
    Str,
    Int,
    Bool,
    Float,
    Property,
    Enum,
    on_trait_change,
    CStr,
    Long,
    HasTraits,
    Instance,
)

from pychron.core.helpers.filetools import remove_extension
from pychron.core.helpers.logger_setup import new_logger
from pychron.core.helpers.strtools import csv_to_ints, to_csv_str
from pychron.core.utils import alphas, alpha_to_int
from pychron.experiment.automated_run.result import (
    AutomatedRunResult,
    AirResult,
    UnknownResult,
    BlankResult,
)
from pychron.experiment.utilities.identifier import (
    get_analysis_type,
    is_special,
    convert_extract_device,
)
from pychron.experiment.utilities.position_regex import XY_REGEX
from pychron.experiment.utilities.repository_identifier import (
    make_references_repository_identifier,
)
from pychron.experiment.utilities.runid import make_rid, make_runid
from pychron.pychron_constants import (
    SCRIPT_KEYS,
    SCRIPT_NAMES,
    DETECTOR_IC,
    DURATION,
    EXTRACT_VALUE,
    EXTRACT_UNITS,
    RAMP_RATE,
    RAMP_DURATION,
    BEAM_DIAMETER,
    PRECLEANUP,
    CLEANUP,
    POSTCLEANUP,
    DELAY_AFTER,
    PATTERN,
    LIGHT_VALUE,
    TRAY,
    MASS_SPECTROMETER,
    POSITION,
    USE_CDD_WARMING,
    EXTRACT_DEVICE,
    COLLECTION_TIME_ZERO_OFFSET,
    WEIGHT,
    COMMENT,
    PROJECT,
    SAMPLE,
    MATERIAL,
    REPOSITORY_IDENTIFIER,
    DISABLE_BETWEEN_POSITIONS,
    USERNAME,
    NULL_STR,
    CRYO_TEMP,
    CANCELED,
    FAILED,
    TRUNCATED,
    SUCCESS,
    EXTRACTION,
    MEASUREMENT,
    INVALID,
    NOT_RUN,
    ABORTED,
)

logger = new_logger("AutomatedRunSpec")


class AutomatedRunSpec(HasTraits):
    """
    this class is used to as a simple container and factory for
    an AutomatedRun. the AutomatedRun does the actual work. ie extraction and measurement
    """

    run_klass = "pychron.experiment.automated_run.automated_run.AutomatedRun"
    spectrometer_manager = Instance(
        "pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager"
    )

    result = Instance(AutomatedRunResult, ())
    state = Enum(
        NOT_RUN,
        EXTRACTION,
        MEASUREMENT,
        SUCCESS,
        FAILED,
        TRUNCATED,
        CANCELED,
        INVALID,
        "test",
        ABORTED,
    )

    skip = Bool(False)
    end_after = Bool(False)
    delay_after = Float
    # ===========================================================================
    # queue globals
    # ===========================================================================
    mass_spectrometer = Str
    extract_device = Str
    username = Str
    tray = Str
    load_name = Str
    load_holder = Str
    queue_conditionals_name = Str
    sensitivity_units = Str
    # ===========================================================================
    # run id
    # ===========================================================================
    labnumber = Str
    uuid = Str
    user_defined_aliquot = Int
    aliquot = Property(depends_on="_aliquot, user_defined_aliquot")
    _aliquot = Int

    step = Property(depends_on="_step")
    _step = Int(-1)

    analysis_dbid = Long
    analysis_timestamp = None
    # ===========================================================================
    # scripts
    # ===========================================================================
    measurement_script = Str
    post_measurement_script = Str
    post_equilibration_script = Str
    extraction_script = Str
    script_options = Str
    use_cdd_warming = Bool

    # ===========================================================================
    # extraction
    # ===========================================================================
    extract_value = Float
    extract_units = Str
    position = Str
    xyz_position = Str
    light_value = 0

    duration = Float
    cleanup = Float
    pre_cleanup = Float
    post_cleanup = Float
    cryo_temperature = Float
    post_analysis_delay = Float

    pattern = Str
    beam_diameter = CStr
    ramp_duration = Float
    ramp_rate = Float
    disable_between_positions = Bool(False)
    _overlap = Int
    _min_ms_pumptime = Int
    conditionals = Str
    syn_extraction = Str
    collection_time_zero_offset = Float
    repository_identifier = Str

    frequency_group = 0
    conflicts_checked = False
    identifier_error = Bool(False)

    executable = Property(depends_on="identifier_error, _executable")
    _executable = Bool(True)

    lab_temperature = 0
    lab_humidity = 0
    sensitivity = 0
    sensitivity_units = "mol/fA"

    # ===========================================================================
    # info
    # ===========================================================================
    weight = 0
    comment = ""

    # ===========================================================================
    # display only
    # ===========================================================================
    project = ""
    principal_investigator = ""
    sample = ""
    irradiation = ""
    irradiation_level = ""
    irradiation_position = ""
    material = ""
    grainsize = ""
    latitude = ""
    longitude = ""
    lithology = ""
    lithology_class = ""
    lithology_group = ""
    lithology_type = ""

    data_reduction_tag = ""
    result_str = ""

    branch = "master"

    position_j = 0
    position_jerr = 0
    uage = None
    v39 = None
    display_k3739_mode = ""

    _estimated_duration = 0
    _changed = False

    _step_heat = False
    _runid = None

    @property
    def acquisition_software(self):
        from pychron.experiment import __version__ as eversion
        from pychron.dvc import __version__ as dversion
        from pychron import __version__

        return "Pychron{}(Exp{},DVC{})".format(__version__, eversion, dversion)

    @property
    def data_reduction_software(self):
        from pychron import __version__
        from pychron.dvc import __version__ as dversion

        return "Pychron{}(DVC{})".format(__version__, dversion)

    def new_result(self, arun):
        klass = AutomatedRunResult
        if self.analysis_type == "air":
            klass = AirResult
        elif self.analysis_type == "unknown":
            klass = UnknownResult
        elif "blank" in self.analysis_type:
            klass = BlankResult

        result = klass()
        result.runid = self.runid
        result.analysis_timestamp = datetime.now()
        result.isotope_group = arun.isotope_group
        result.tripped_conditional = arun.tripped_conditional
        if arun.peak_center:
            result.centering_results = arun.peak_center.get_results()
        self.result = result

    def is_detector_ic(self):
        return self.analysis_type == DETECTOR_IC

    def is_step_heat(self):
        return bool(self.user_defined_aliquot) and not self.is_special()

    def is_special(self):
        return is_special(self.labnumber)

    def is_truncated(self):
        return self.state == "truncated"

    def is_default_repository(self, ms, curtag):
        return (
            make_references_repository_identifier(self.analysis_type, ms, curtag)
            == self.repository_identifier
        )

    def to_string(self):
        attrs = [
            "labnumber",
            "aliquot",
            "step",
            "extract_value",
            "extract_units",
            "ramp_duration",
            "position",
            "duration",
            "cleanup",
            "beam_diameter",
            "mass_spectrometer",
            "extract_device",
            "extraction_script",
            "measurement_script",
            "post_equilibration_script",
            "post_measurement_script",
        ]
        return to_csv_str(self.to_string_attrs(attrs))

    def test_scripts(self, script_context=None, warned=None, duration=True):
        if script_context is None:
            script_context = {}
        if warned is None:
            warned = []

        arun = None
        s = 0
        script_oks = []
        for si in SCRIPT_NAMES:
            name = getattr(self, si)
            if name in script_context:
                if name not in warned:
                    logger.debug(
                        "{} in script context. using previous estimated duration".format(
                            name
                        )
                    )
                    warned.append(name)

                script, ok = script_context[name]
                if ok and duration:
                    if si in ("measurement_script", "extraction_script"):
                        # ctx = dict(duration=self.duration,
                        # cleanup=self.cleanup,
                        #            analysis_type=self.analysis_type,
                        #            position=self.position)
                        # arun.setup_context(script)
                        ctx = self.make_script_context()
                        d = script.calculate_estimated_duration(ctx)
                        logger.debug(
                            "script duration name:{} seconds:{}".format(name, d)
                        )
                        s += d
                script_oks.append(ok)
            else:
                if arun is None:
                    arun = self.make_run(new_uuid=False)

                arun.refresh_scripts()
                # arun.invalid_script = False
                script = getattr(arun, si)
                if script is not None:
                    # if duration:
                    # arun.setup_context(script)

                    ok = script.syntax_ok()
                    script_oks.append(ok)
                    script_context[name] = script, ok
                    if ok and duration:
                        if si in ("measurement_script", "extraction_script"):
                            ctx = self.make_script_context()
                            d = script.calculate_estimated_duration(ctx)
                            logger.debug(
                                "script duration name:{} seconds:{}".format(name, d)
                            )
                            s += d
        if arun:
            arun.spec = None
            # set executable. if all scripts have OK syntax executable is True

        self._executable = all(script_oks)
        return s

    def get_position_list(self):
        pos = self.position
        if XY_REGEX[0].match(pos):
            ps = XY_REGEX[1](pos)
        elif "," in pos:
            # interpret as list of hole numbers
            ps = list(pos.split(","))
        else:
            ps = [pos]

        return ps

    def make_script_context(self):
        hdn = convert_extract_device(self.extract_device)
        an = self.analysis_type.split("_")[0]

        ctx = dict(
            position=self.get_position_list(), extract_device=hdn, analysis_type=an
        )

        for attr in (
            DISABLE_BETWEEN_POSITIONS,
            TRAY,
            DURATION,
            EXTRACT_VALUE,
            EXTRACT_UNITS,
            CLEANUP,
            PRECLEANUP,
            POSTCLEANUP,
            DELAY_AFTER,
            PATTERN,
            LIGHT_VALUE,
            BEAM_DIAMETER,
            RAMP_DURATION,
            RAMP_RATE,
        ):
            ctx[attr] = getattr(self, attr)

        return ctx

    def get_estimated_duration(self, script_context=None, warned=None, force=False):
        """
        use the pyscripts to calculate etd

        script_context is a dictionary of already loaded scripts

        this is a good point to set executable as well
        """
        if not self._estimated_duration or self._changed or force:
            s = self.test_scripts(script_context, warned)
            logger.debug("Script duration {}".format(s))
            db_save_time = 1
            self._estimated_duration = s + db_save_time

        self._changed = False
        logger.debug(
            "Run total estimated duration= {:0.3f}".format(self._estimated_duration)
        )
        return self._estimated_duration

    def make_run(self, new_uuid=True, run=None):
        if run is None:
            args = self.run_klass.split(".")
            md, klass = ".".join(args[:-1]), args[-1]

            md = __import__(md, fromlist=[klass])
            run = getattr(md, klass)()

        for si in SCRIPT_KEYS:
            setattr(
                run.script_info,
                "{}_script_name".format(si),
                getattr(self, "{}_script".format(si)),
            )

        if new_uuid:
            run.uuid = u = str(uuid.uuid4())
            self.uuid = u

        run.spec = self
        run.runid = self.runid
        run.spectrometer_manager = self.spectrometer_manager

        return run

    def get_delay_after(self, du, db, da):
        d = self.delay_after
        if not d:
            d = du
            if self.analysis_type == "air":
                d = da
            elif self.analysis_type.startswith("blank"):
                d = db

                # d = db if self.analysis_type.startswith('blank') else du

        return d

    def load(self, script_info, params):
        for k, v in script_info.items():
            k = k if k == "script_options" else "{}_script".format(k)
            setattr(self, k, v)

        for k, v in params.items():
            if hasattr(self, k):
                setattr(self, k, v)

        if self.light_value is None:
            self.light_value = params.get("default_lighting", 0)

        self._changed = False

    def to_string_attrs(self, attrs):
        def get_attr(attrname):
            if attrname == "labnumber":
                if self.user_defined_aliquot and not self.is_special():
                    v = make_rid(self.labnumber, self.aliquot)
                else:
                    v = self.labnumber
            elif attrname.endswith("script"):
                # remove mass spectrometer name
                v = getattr(self, attrname)
                # v = self._remove_mass_spectrometer_name(v)
                v = remove_extension(v)

            elif attrname == "overlap":
                o, m = self.overlap
                if m:
                    v = "{},{}".format(*self.overlap)
                else:
                    v = o
            else:
                try:
                    v = getattr(self, attrname)
                except AttributeError as e:
                    v = ""

            return v

        return [get_attr(ai) for ai in attrs]

    def reset(self):
        self.clear_step()
        self.conflicts_checked = False

    def clear_step(self):
        self._step = -1

    def tocopy(self, verbose=False):
        traits = [
            MASS_SPECTROMETER,
            EXTRACT_DEVICE,
            USERNAME,
            TRAY,
            "queue_conditionals_name",
            "labnumber",
            "user_defined_aliquot",
            "measurement_script",
            "post_measurement_script",
            "post_equilibration_script",
            "extraction_script",
            "script_options",
            USE_CDD_WARMING,
            EXTRACT_VALUE,
            EXTRACT_UNITS,
            POSITION,
            "xyz_position",
            DURATION,
            CLEANUP,
            PRECLEANUP,
            POSTCLEANUP,
            CRYO_TEMP,
            PATTERN,
            BEAM_DIAMETER,
            RAMP_DURATION,
            RAMP_RATE,
            DISABLE_BETWEEN_POSITIONS,
            "_overlap",
            "_min_ms_pumptime",
            "conditionals",
            "syn_extraction",
            COLLECTION_TIME_ZERO_OFFSET,
            WEIGHT,
            COMMENT,
            PROJECT,
            SAMPLE,
            "irradiation",
            "irradiation_level",
            "irradiation_position",
            MATERIAL,
            "data_reduction_tag",
            DELAY_AFTER,
        ]

        if self.is_step_heat():
            traits.append("aliquot")

        if not self.is_special():
            traits.append(REPOSITORY_IDENTIFIER)

        if verbose:
            for t in traits:
                print("{} ==> {}".format(t, getattr(self, t)))

        return self.clone_traits(traits)

    # ===============================================================================
    # handlers
    # ===============================================================================
    @on_trait_change(
        """measurement_script, post_measurement_script,
post_equilibration_script, extraction_script, script_options, position, duration, cleanup, pre_cleanup, post_cleanup"""
    )
    def _change_handler(self, name, new):
        if new == "None":
            self.trait_set(**{name: ""})
        else:
            self._changed = True

    def _state_changed(self, old, new):
        logger.debug("state changed from {} to {}".format(old, new))

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _set_aliquot(self, v):
        self._aliquot = v

    def _get_aliquot(self):
        if self.is_special():
            return self._aliquot
        else:
            if self.user_defined_aliquot:
                return self.user_defined_aliquot
        return self._aliquot

    def _set_step(self, v):
        if isinstance(v, str):
            if v:
                self._step = alpha_to_int(v)
        else:
            self._step = v

    def _get_step(self):
        return alphas(self._step)

    def _set_executable(self, v):
        self._executable = v

    def _get_executable(self):
        return self._executable and not self.identifier_error

    @property
    def analysis_type(self):
        return get_analysis_type(self.labnumber)

    @property
    def overlap(self):
        return self._overlap, self._min_ms_pumptime

    @overlap.setter
    def overlap(self, v):
        if isinstance(v, (list, tuple)):
            args = v
        else:
            try:
                args = csv_to_ints(v)
            except ValueError:
                logger.debug(
                    'Invalid overlap string "{}". Should be of the form "10,60" or "10" '.format(
                        v
                    )
                )
                return

        if len(args) == 1:
            self._overlap = args[0]
        elif len(args) == 2:
            self._overlap, self._min_ms_pumptime = args

    @property
    def runid(self):
        if self._runid:
            return self._runid
        else:
            return make_runid(self.labnumber, self.aliquot, self.step)

    @runid.setter
    def runid(self, v):
        self._runid = v

    @property
    def rundate(self):
        return datetime.now()

    # mirror labnumber for now. deprecate labnumber and replace with identifier
    @property
    def identifier(self):
        return self.labnumber

    @identifier.setter
    def identifier(self, v):
        self.labnumber = v

    @property
    def display_irradiation(self):
        ret = ""
        if self.irradiation:
            ret = "{} {}:{}".format(
                self.irradiation, self.irradiation_level, self.irradiation_position
            )
        return ret

    @property
    def increment(self):
        return None if self._step < 0 else self._step

    @property
    def extraction_script_name(self):
        return self.extraction_script

    @property
    def measurement_script_name(self):
        return self.measurement_script

    @property
    def sensitivity(self):
        return 0

    @property
    def sensitivity_units(self):
        return "mV/mol"

    # post
    @property
    def post_cleanup_duration(self):
        return self.post_cleanup

    @post_cleanup_duration.setter
    def post_cleanup_duration(self, v):
        self.post_cleanup = v

    # pre
    @property
    def pre_cleanup_duration(self):
        return self.pre_cleanup

    @pre_cleanup_duration.setter
    def pre_cleanup_duration(self, v):
        self.pre_cleanup = v

    # clean
    @property
    def pre_cleanup_duration(self):
        return self.pre_cleanup

    @pre_cleanup_duration.setter
    def pre_cleanup_duration(self, v):
        self.pre_cleanup = v

    @property
    def post_cleanup_duration(self):
        return self.post_cleanup

    @post_cleanup_duration.setter
    def post_cleanup_duration(self, v):
        self.post_cleanup = v

    @property
    def cleanup_duration(self):
        return self.cleanup

    @cleanup_duration.setter
    def cleanup_duration(self, v):
        self.cleanup = v

    # extract
    @property
    def extract_duration(self):
        return self.duration

    @extract_duration.setter
    def extract_duration(self, v):
        self.duration = v

    def make_truncated_script_hash(self):
        h = self._base_script_hash()
        h.update("truncated")
        h.update("True")
        return h.hexdigest()

    @property
    def has_conditionals(self):
        return bool(self.conditionals)

    @property
    def script_hash_truncated(self):
        h = self._base_script_hash()
        h.update("truncated")
        h.update(str(self.is_truncated()))
        return h.hexdigest()

    @property
    def script_hash(self):
        h = self._base_script_hash()
        return h.hexdigest()

    def _base_script_hash(self):
        # ctx should only contain values that affect the length of the analysis
        ctx = dict(
            nposition=len(self.get_position_list()),
            measurement=self.measurement_script,
            extraction=self.extraction_script,
        )

        for a in (
            DISABLE_BETWEEN_POSITIONS,
            DURATION,
            CLEANUP,
            PRECLEANUP,
            POSTCLEANUP,
            RAMP_RATE,
            PATTERN,
            RAMP_DURATION,
        ):
            ctx[a] = getattr(self, a)

        md5 = hashlib.md5()
        for k, v in sorted(ctx.items()):
            md5.update(str(k).encode("utf-8"))
            md5.update(str(v).encode("utf-8"))
        return md5

    def __getattr__(self, item):
        return NULL_STR


# ============= EOF =============================================
