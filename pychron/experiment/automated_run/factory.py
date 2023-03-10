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


import os
import pickle

import yaml
from apptools.preferences.preference_binding import bind_preference
from traits.api import (
    String,
    Str,
    Property,
    Any,
    Float,
    Instance,
    Int,
    List,
    cached_property,
    on_trait_change,
    Bool,
    Button,
    Event,
    Enum,
    Dict,
)
from traits.trait_errors import TraitError
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.filetools import (
    list_directory,
    add_extension,
    remove_extension,
)
from pychron.core.helpers.iterfuncs import partition, groupby_key
from pychron.core.helpers.strtools import camel_case
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.yaml import yload
from pychron.dvc import prep_repo_name
from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.entry.entry_views.repository_entry import RepositoryIdentifierEntry
from pychron.envisage.view_util import open_view
from pychron.experiment.automated_run.factory_util import (
    UpdateSelectedCTX,
    EKlass,
    increment_value,
    increment_position,
    generate_positions,
    get_run_blocks,
    remove_file_extension,
)
from pychron.experiment.automated_run.factory_view import FactoryView
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.conditional.conditionals_edit_view import edit_conditionals
from pychron.experiment.datahub import Datahub
from pychron.experiment.queue.increment_heat_template import (
    LaserIncrementalHeatTemplate,
    BaseIncrementalHeatTemplate,
)
from pychron.experiment.queue.run_block import RunBlock
from pychron.experiment.script.script import Script, ScriptOptions
from pychron.experiment.utilities.comment_template import CommentTemplater
from pychron.experiment.utilities.frequency_edit_view import FrequencyModel
from pychron.experiment.utilities.identifier import (
    convert_special_name,
    ANALYSIS_MAPPING,
    NON_EXTRACTABLE,
    make_special_identifier,
    make_standard_identifier,
    SPECIAL_KEYS,
    get_analysis_type_shortname,
)
from pychron.experiment.utilities.position_regex import (
    SLICE_REGEX,
    PSLICE_REGEX,
    SSLICE_REGEX,
    TRANSECT_REGEX,
    POSITION_REGEX,
    XY_REGEX,
    SCAN_REGEX,
)
from pychron.lasers.pattern.pattern_maker_view import PatternMakerView
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceLoggable
from pychron.pychron_constants import (
    NULL_STR,
    SCRIPT_KEYS,
    SCRIPT_NAMES,
    LINE_STR,
    DVC_PROTOCOL,
    SPECIAL_IDENTIFIER,
    BLANK_UNKNOWN,
    BLANK_EXTRACTIONLINE,
    UNKNOWN,
    PAUSE,
    DEGAS,
    SIMPLE,
    NULL_EXTRACT_DEVICES,
    FUSIONS_CO2,
    FUSIONS_DIODE,
    CLEANUP,
    PRECLEANUP,
    POSTCLEANUP,
    EXTRACT_VALUE,
    EXTRACT_UNITS,
    DURATION,
    WEIGHT,
    POSITION,
    PATTERN,
    BEAM_DIAMETER,
    LIGHT_VALUE,
    COMMENT,
    DELAY_AFTER,
    EXTRACT_DEVICE,
    MATERIAL,
    PROJECT,
    SAMPLE,
    MASS_SPECTROMETER,
    COLLECTION_TIME_ZERO_OFFSET,
    USE_CDD_WARMING,
    SKIP,
    OVERLAP,
    REPOSITORY_IDENTIFIER,
    RAMP_DURATION,
    CRYO_TEMP,
    TEMPLATE,
    USERNAME,
    EDITABLE_RUN_CONDITIONALS,
    DISABLE_BETWEEN_POSITIONS,
)


class AutomatedRunFactory(DVCAble, PersistenceLoggable):
    datahub = Instance(Datahub)
    undoer = Any
    edit_event = Event
    mode = None

    # ============== scripts =============
    extraction_script = Instance(Script)
    measurement_script = Instance(Script)
    post_measurement_script = Instance(Script)
    post_equilibration_script = Instance(Script)

    script_options = Instance(ScriptOptions, ())
    load_defaults_button = Button("Default")

    default_fits_button = Button
    default_fits_enabled = Bool
    # ===================================

    factory_view = Instance(FactoryView)
    factory_view_klass = FactoryView

    set_labnumber = True
    set_position = True

    delay_after = Float
    labnumber = Str

    aliquot = EKlass(Int)
    special_labnumber = Str(SPECIAL_IDENTIFIER)

    db_refresh_needed = Event
    auto_save_needed = Event

    labnumbers = Property(depends_on="project, selected_level, _identifiers")
    display_labnumbers = Property(depends_on="project, selected_level, _identifiers")
    _identifiers = List

    use_project_based_repository_identifier = Bool(True)
    repository_identifier = Str
    repository_identifiers = Property(
        depends_on="repository_identifier_dirty, db_refresh_needed"
    )
    add_repository_identifier = Event
    repository_identifier_dirty = Event
    set_repository_identifier_button = Event
    clear_repository_identifier_button = Event

    irradiation_project_prefix = Str
    selected_irradiation = Str("Irradiation")
    irradiations = Property(depends_on="db, db_refresh_needed")
    selected_level = Str("Level")
    levels = Property(depends_on="selected_irradiation, db")

    flux = Property(Float, depends_on="refresh_flux_needed")
    flux_error = Property(Float, depends_on="refresh_flux_needed")
    refresh_flux_needed = Event

    _flux = None
    _flux_error = None
    save_flux_button = Button

    skip = Bool(False)
    end_after = Property(Bool, depends_on="_end_after")
    _end_after = Bool(False)

    weight = Float
    comment = String(auto_set=False, enter_set=True, maxlen=200)
    auto_fill_comment = Bool
    edit_comment_template = Button
    apply_comment_button = Event

    _comment_templater = None

    position = Property(depends_on="_position")
    _position = EKlass(String)

    # ===========================================================================
    # measurement
    # ===========================================================================
    use_cdd_warming = Bool
    collection_time_zero_offset = Float(0)

    # ===========================================================================
    # extract
    # ===========================================================================
    extract_value = EKlass(Float)
    extract_units = Str(NULL_STR)
    extract_units_names = List(["", "watts", "temp", "percent", "lumens"])
    _default_extract_units = "watts"

    ramp_duration = EKlass(Float)

    overlap = EKlass(String)
    duration = EKlass(Float)
    cleanup = EKlass(Float)
    pre_cleanup = EKlass(Float)
    post_cleanup = EKlass(Float)
    cryo_temperature = EKlass(Float)
    disable_between_positions = EKlass(Bool)
    light_value = EKlass(Float)
    beam_diameter = Property(EKlass(String), depends_on="_beam_diameter")
    _beam_diameter = String

    pattern = String("Pattern")
    patterns = List
    remote_patterns = List

    edit_pattern = Event
    edit_pattern_label = Property(depends_on="pattern")
    # ===========================================================================
    # templates
    # ===========================================================================
    template = String("Step Heat Template")
    templates = List

    edit_template = Event
    edit_template_label = Property(depends_on="template")
    apply_stepheat = Event
    # ===========================================================================
    # conditionals
    # ===========================================================================
    trunc_attr = String("age")
    trunc_attrs = List(
        [
            "age",
            "kca",
            "kcl",
            "age.std",
            "kca.std",
            "kcl.std",
            "radiogenic_yield",
            "Ar40",
            "Ar39",
            "Ar38",
            "Ar37",
            "Ar36",
        ]
    )
    trunc_comp = Enum(">", "<", ">=", "<=", "=")
    trunc_crit = Float(5000, enter_set=True, auto_set=False)
    trunc_start = Int(100, enter_set=True, auto_set=False)
    use_simple_truncation = Bool

    conditionals_str = Property(depends_on="trunc_+")
    conditionals_path = String
    conditionals = List
    clear_conditionals = Button
    edit_conditionals_button = Button
    new_conditionals_button = Button
    apply_conditionals_button = Button

    # ===========================================================================
    # blocks
    # ===========================================================================
    run_block = Str("RunBlock")
    run_blocks = List
    edit_run_blocks = Button

    # ===========================================================================
    # frequency
    # ===========================================================================
    # frequency = Int
    # freq_before = Bool(True)
    # freq_after = Bool(False)
    # freq_template = Str
    frequency_model = Instance(FrequencyModel, ())
    edit_frequency_button = Button
    # ===========================================================================
    # readonly
    # ===========================================================================
    sample = Str
    project = Str
    material = Str

    display_irradiation = Str
    irrad_level = Str
    irrad_hole = Int

    info_label = Property(depends_on="labnumber, display_irradiation, sample")
    extractable = Property(depends_on="labnumber")

    update_info_needed = Event
    refresh_table_needed = Event
    changed = Event
    suppress_update = False

    edit_mode = Bool(False)
    edit_mode_label = Property(depends_on="edit_mode")
    edit_enabled = Bool(True)

    mass_spectrometer = String
    extract_device = Str
    username = Str
    laboratory = Str

    persistence_name = "run_factory"
    pattributes = (
        "collection_time_zero_offset",
        "selected_irradiation",
        "selected_level",
        CLEANUP,
        PRECLEANUP,
        POSTCLEANUP,
        EXTRACT_VALUE,
        EXTRACT_UNITS,
        DURATION,
        WEIGHT,
        LIGHT_VALUE,
        BEAM_DIAMETER,
        RAMP_DURATION,
        CRYO_TEMP,
        OVERLAP,
        PATTERN,
        POSITION,
        COMMENT,
        TEMPLATE,
        "use_simple_truncation",
        "conditionals_path",
        "use_project_based_repository_identifier",
        "delay_after",
        DISABLE_BETWEEN_POSITIONS,
    )

    use_name_prefix = Bool
    name_prefix = Str
    # ===========================================================================
    # private
    # ===========================================================================
    _current_loaded_default_scripts_key = None
    _selected_runs = List
    _spec_klass = AutomatedRunSpec
    _set_defaults = True
    _no_clear_labnumber = False
    _meta_cache = Dict
    _suppress_special_labnumber_change = False

    def __init__(self, *args, **kw):
        bind_preference(self, "use_name_prefix", "pychron.pyscript.use_name_prefix")
        bind_preference(self, "name_prefix", "pychron.pyscript.name_prefix")
        bind_preference(self, "laboratory", "pychron.general.organization")

        bind_preference(
            self,
            "irradiation_project_prefix",
            "pychron.entry.irradiation_project_prefix",
        )

        if not self.irradiation_project_prefix:
            self.warning_dialog(
                'Please Set "Irradiation Project Prefix" in Preferences/Entry'
            )

        super(AutomatedRunFactory, self).__init__(*args, **kw)

    # def set_identifiers(self, v):
    #     self._identifiers = v

    def setup_files(self):
        self.load_templates()
        self.load_run_blocks()
        self.load_patterns()
        self.load_conditionals()

    def activate(self, load_persistence):
        self.conditionals_path = NULL_STR
        if load_persistence:
            self.load()

        self.setup_files()

    def deactivate(self):
        self.dump(verbose=True)

    def set_end_after(self, v):
        self._update_run_values("end_after", v)

    def update_selected_ctx(self):
        return UpdateSelectedCTX(self)

    def load_run_blocks(self):
        self.run_blocks = get_run_blocks()

    def load_templates(self):
        self.templates = self._get_templates()

    def load_patterns(self):
        self.patterns = self._get_patterns()

    def load_conditionals(self):
        self.conditionals = self._get_conditionals()

    def use_frequency(self):
        return self.labnumber in ANALYSIS_MAPPING and self.frequency_model.frequency

    def load_from_run(self, run):
        self._clone_run(run)

    def set_selected_runs(self, runs):
        self.debug("len selected runs {}".format(len(runs)))
        run = None

        self._selected_runs = runs

        if runs:
            run = runs[0]
            self._set_defaults = False
            self._clone_run(
                run, set_labnumber=self.set_labnumber, set_position=self.set_position
            )
            self._set_defaults = True

        # self.suppress_update = False

        if not runs:
            self.edit_mode = False
            # self.edit_enabled = False
        elif len(runs) == 1:
            pass
            # self.edit_enabled = True
            # self._aliquot_changed()
        else:
            # self.edit_enabled = False
            self.edit_mode = True

        if run and self.edit_mode:
            self._end_after = run.end_after

    def set_mass_spectrometer(self, new):
        new = new.lower()
        self.debug("setting mass spec to={}".format(new))
        self.mass_spectrometer = new
        for s in self._iter_scripts():
            s.mass_spectrometer = new
            s.refresh_lists = True

    def set_extract_device(self, new):
        new = new.lower()
        self.extract_device = new
        for s in self._iter_scripts():
            s.extract_device = new

    def new_run_simple(self, idn, position):
        rs = self._spec_klass(identifier=idn, position=position)
        return rs

    def new_runs(
        self,
        exp_queue,
        positions=None,
        auto_increment_position=False,
        auto_increment_id=False,
    ):
        """
        returns a list of runs even if its only one run
        also returns self.frequency if using special labnumber else None
        """
        self._auto_save()

        if self.run_block not in ("RunBlock", LINE_STR):
            arvs, freq = self._new_run_block()
        else:
            arvs, freq = self._new_runs(exp_queue, positions=positions)

        if auto_increment_id:
            v = increment_value(self.labnumber, increment=auto_increment_id)
            self.debug(
                "auto increment labnumber: prev={}, new={}".format(self.labnumber, v)
            )
            self.labnumber = v

        if auto_increment_position:
            pos = self.position
            if pos:
                self.position = increment_position(pos)

        self._auto_save()
        return arvs, freq

    def refresh(self):
        self.changed = True
        self.refresh_table_needed = True
        self._auto_save()

    def do_apply_stepheat(self, queue):
        dh = self.datahub
        aliquots = {}

        sruns = self._selected_runs
        aruns = queue.automated_runs

        for ln, runs in groupby_key(sruns, "identifier"):
            gal = dh.get_greatest_aliquot(ln)
            rgal = max([r.aliquot for r in aruns if r.identifier == ln])
            aliquot = max(gal, rgal)
            aliquots[ln] = aliquot

        template = self._new_template()
        new_runs = []
        for r in sruns:
            gal = aliquots[r.identifier]
            aliquot = gal + 1
            aliquots[r.identifier] = aliquot

            idx = aruns.index(r)
            i = 0
            for st in template.steps:
                if st.value and (st.duration or st.cleanup):
                    if i == 0:
                        arv = r
                    else:
                        arv = self._new_run(position=r.position, excludes=["position"])

                    arv.trait_set(
                        user_defined_aliquot=aliquot,
                        **st.make_dict(self.duration, self.cleanup)
                    )
                    new_runs.append((idx, arv))
                    i += 1

        for idx, r in reversed(new_runs):
            if r in aruns:
                aruns.remove(r)
            aruns.insert(idx, r)

    # ===============================================================================
    # private
    # ===============================================================================
    def _auto_save(self):
        self.auto_save_needed = True

    def _new_run_block(self):
        p = os.path.join(paths.run_block_dir, add_extension(self.run_block, ".txt"))
        block = RunBlock(
            extract_device=self.extract_device, mass_spectrometer=self.mass_spectrometer
        )
        return block.make_runs(p), self.frequency_model.frequency

    def _new_runs(self, exp_queue, positions):
        ln, special = self._make_short_labnumber()
        freq = self.frequency_model.frequency if special else None
        self.debug("Frequency={}".format(freq))
        if not special or ln == "dg":
            if not positions:
                positions = self.position

            template = self._use_template()  # and not freq
            arvs = self._new_runs_by_position(exp_queue, positions, template)
        else:
            arvs = [self._new_run()]

        return arvs, freq

    def _new_runs_by_position(self, exp_queue, pos, template=False):
        arvs = []
        positions = generate_positions(pos)
        for i, p in enumerate(positions):
            p = str(p)
            if template:
                arvs.extend(self._render_template(exp_queue, p, i))
            else:
                arvs.append(self._new_run(position=str(p), excludes=["position"]))
        return arvs

    def _make_irrad_level(self, ipos):
        il = ""
        if ipos is not None:
            try:
                level = ipos.level
            except AttributeError:
                level = ""

            if level:
                irrad = level.irradiation
                hole = ipos.position
                irradname = irrad.name
                self.irrad_hole = int(hole)
                self.irrad_level = irrad_level = str(level.name)
                if irradname == "NoIrradiation":
                    il = NULL_STR
                else:
                    il = "{} {}:{}".format(irradname, level.name, hole)
            else:
                irradname = ""
                irrad_level = ""

            self._no_clear_labnumber = True
            self.selected_irradiation = LINE_STR
            self.selected_irradiation = irradname
            self.selected_level = irrad_level
            self._no_clear_labnumber = False

        self.display_irradiation = il

    def _new_run(self, excludes=None, **kw):
        # need to set the labnumber now because analysis_type depends on it
        arv = self._spec_klass(labnumber=self.labnumber, **kw)

        if excludes is None:
            excludes = []

        if arv.analysis_type in (BLANK_UNKNOWN, PAUSE, BLANK_EXTRACTIONLINE):
            excludes.extend((EXTRACT_VALUE, EXTRACT_UNITS, PATTERN, BEAM_DIAMETER))
            if arv.analysis_type == PAUSE:
                excludes.extend((CLEANUP, PRECLEANUP, POSTCLEANUP, POSITION))
        elif arv.analysis_type not in (UNKNOWN, DEGAS):
            excludes.extend(
                (
                    POSITION,
                    EXTRACT_VALUE,
                    EXTRACT_UNITS,
                    PATTERN,
                    CLEANUP,
                    PRECLEANUP,
                    POSTCLEANUP,
                    DURATION,
                    BEAM_DIAMETER,
                )
            )

        self._set_run_values(arv, excludes=excludes)
        return arv

    def _get_clonable_attrs(self):
        return [
            "labnumber",
            EXTRACT_VALUE,
            EXTRACT_UNITS,
            CLEANUP,
            PRECLEANUP,
            POSTCLEANUP,
            CRYO_TEMP,
            DURATION,
            LIGHT_VALUE,
            PATTERN,
            BEAM_DIAMETER,
            POSITION,
            COLLECTION_TIME_ZERO_OFFSET,
            USE_CDD_WARMING,
            WEIGHT,
            COMMENT,
            DELAY_AFTER,
        ]

    def _get_run_attr(self):
        return [
            BEAM_DIAMETER,
            DELAY_AFTER,
            DURATION,
            CLEANUP,
            COMMENT,
            "conditionals_str",
            COLLECTION_TIME_ZERO_OFFSET,
            EXTRACT_DEVICE,
            EXTRACT_VALUE,
            EXTRACT_UNITS,
            LIGHT_VALUE,
            MASS_SPECTROMETER,
            MATERIAL,
            PATTERN,
            POSITION,
            POSTCLEANUP,
            PRECLEANUP,
            CRYO_TEMP,
            PROJECT,
            RAMP_DURATION,
            "repository_identifier",
            SAMPLE,
            "skip",
            USE_CDD_WARMING,
            USERNAME,
            WEIGHT,
        ]

    def _set_run_values(self, arv, excludes=None):
        """
        if run is not an unknown and not a degas then don't copy evalue, eunits and pattern
        if runs is an unknown but is part of an extract group dont copy the evalue
        """
        if excludes is None:
            excludes = []

        for attr in self._get_run_attr():
            if attr in excludes:
                continue

            sattr = attr
            if attr == "conditionals_str":
                sattr = "conditionals"

            v = getattr(self, attr)
            if attr == "pattern":
                if not self._use_pattern():
                    v = ""

            setattr(arv, sattr, v)
            setattr(arv, "_prev_{}".format(sattr), v)

        arv.irradiation = self.selected_irradiation
        arv.irradiation_level = self.selected_level
        arv.irradiation_position = int(self.irrad_hole)

        if self.aliquot:
            self.debug("setting user defined aliquot")
            arv.user_defined_aliquot = int(self.aliquot)

        for si in SCRIPT_KEYS:
            name = "{}_script".format(si)
            if name in excludes or si in excludes:
                continue

            s = getattr(self, name)
            setattr(arv, name, s.name)

    def _clone_run(self, run, excludes=None, set_labnumber=True, set_position=True):
        self.debug(
            "cloning run {}. set_labnumber={}, set_position={}".format(
                run.runid, set_labnumber, set_position
            )
        )
        if excludes is None:
            excludes = []

        if not set_labnumber:
            excludes.append("labnumber")
        if not set_position:
            excludes.append("position")
        if self.auto_fill_comment:
            excludes.append("comment")

        for attr in self._get_clonable_attrs():
            if attr in excludes:
                continue
            try:
                v = getattr(run, attr)
                # self.debug('setting {}={}'.format(attr, v))
                setattr(self, attr, v)
            except TraitError as e:
                self.debug("clone_run", e)

        for si in SCRIPT_KEYS:
            skey = "{}_script".format(si)
            if skey in excludes or si in excludes:
                continue

            ms = getattr(self, skey)
            sname = getattr(run, skey)
            ms.name = sname

        self.script_options.name = run.script_options

    def _new_pattern(self):
        pm = PatternMakerView()

        if self._use_pattern():
            if pm.load_pattern(self.pattern):
                return pm
        else:
            return pm

    def _new_template(self):
        if self.extract_device in (FUSIONS_CO2, FUSIONS_DIODE):
            klass = LaserIncrementalHeatTemplate
        else:
            klass = BaseIncrementalHeatTemplate

        template = klass()
        if self._use_template():
            t = os.path.join(
                paths.incremental_heat_template_dir, add_extension(self.template)
            )
            template.load(t)

        return template

    def _render_template(self, exp_queue, position, offset):
        arvs = []
        template = self._new_template()
        self.debug("rendering template {}".format(template.name))

        al = self.datahub.get_greatest_aliquot(self.labnumber)
        if al is not None:
            c = exp_queue.count_labnumber(self.labnumber)
            for st in template.steps:
                if st.value or st.duration or st.cleanup:
                    arv = self._new_run(position=position, excludes=["position"])

                    arv.trait_set(
                        user_defined_aliquot=al + 1 + offset + c,
                        **st.make_dict(self.duration, self.cleanup)
                    )
                    arvs.append(arv)

            self._increment_iht_count(template.name)
        else:
            self.debug("missing aliquot_pychron in mass spec secondary db")
            self.warning_dialog(
                "Missing aliquot_pychron in mass spec secondary db. seek help"
            )

        return arvs

    def _increment_iht_count(self, temp):
        p = os.path.join(paths.hidden_dir, "iht_counts.{}".format(self.username))

        ucounts = {}
        if os.path.isfile(p):
            with open(p, "rb") as rfile:
                ucounts = pickle.load(rfile)

        c = ucounts.get(temp, 0) + 1
        ucounts[temp] = c
        self.debug(
            "incrementing users step_heat template count for {}. count= {}".format(
                temp, c
            )
        )
        with open(p, "wb") as wfile:
            pickle.dump(ucounts, wfile)

    def _make_short_labnumber(self, labnumber=None):
        if labnumber is None:
            labnumber = self.labnumber
        if "-" in labnumber:
            labnumber = labnumber.split("-")[0]

        special = labnumber in ANALYSIS_MAPPING
        return labnumber, special

    def _load_extraction_info(self, script=None):
        if script is None:
            script = self.extraction_script

        mod = None
        if "##" in self.labnumber:
            defaults = self._load_default_file()
            if defaults:
                ln = self.labnumber.split("-")[0]
                if ln in defaults:
                    grp = defaults[ln]
                    mod = grp.get("modifier")

            if mod is None:
                mod = script.get_parameter("modifier")
            if mod is not None:
                if isinstance(mod, int):
                    mod = "{:02d}".format(mod)

                self.labnumber = self.labnumber.replace("##", str(mod))

    def _clear_labnumber(self):
        if not self._no_clear_labnumber:
            self.debug("clear labnumber")
            self.labnumber = ""
            self.display_irradiation = ""
            self.sample = ""
            self._suppress_special_labnumber_change = True
            self.special_labnumber = SPECIAL_IDENTIFIER
            self._suppress_special_labnumber_change = False

    def _template_closed(self, obj, name, new):
        self.template = obj.name
        invoke_in_main_thread(self.load_templates)

    def _pattern_closed(self):
        invoke_in_main_thread(self.load_patterns)

    def _use_pattern(self):
        return self.pattern and self.pattern not in (
            LINE_STR,
            "None",
            "",
            "Pattern",
            "Local Patterns",
            "Remote Patterns",
        )

    def _use_template(self):
        return self.template and self.template not in (
            "Step Heat Template",
            LINE_STR,
            "None",
        )

    def _update_run_values(self, attr, v):
        if self.edit_mode and self._selected_runs and not self.suppress_update:
            self._auto_save()

            self.edit_event = dict(
                attribute=attr,
                value=v,
                previous_state=[(ri, getattr(ri, attr)) for ri in self._selected_runs],
            )

            for si in self._selected_runs:
                setattr(si, attr, v)
            self.refresh()

    def _save_flux(self):
        if self._flux is None and self._flux_error is None:
            return

        if self._flux is None:
            self._flux = self.flux
        if self._flux_error is None:
            self._flux_error = self.flux_error

        if self._flux != self.flux or self._flux_error != self.flux_error:
            v, e = self._flux, self._flux_error
            if self.dvc:
                self.dvc.save_flux(self.labnumber, v, e)

    # ===============================================================================
    #
    # ===============================================================================
    def _load_defaults(self, ln, attrs=None, overwrite=True):
        if attrs is None:
            attrs = (
                EXTRACT_VALUE,
                EXTRACT_UNITS,
                CLEANUP,
                PRECLEANUP,
                POSTCLEANUP,
                DURATION,
                BEAM_DIAMETER,
                LIGHT_VALUE,
                CRYO_TEMP,
            )

        self.debug(
            "loading defaults for {}. ed={} attrs={}".format(
                ln, self.extract_device, attrs
            )
        )
        defaults = self._load_default_file()
        if defaults:
            if ln in defaults:
                grp = defaults[ln]
                ed = self.extract_device.replace(" ", "")
                if ed in grp:
                    grp = grp[ed]

                for attr in attrs:
                    if overwrite or not getattr(self, attr):
                        v = grp.get(attr)
                        if v is not None:
                            setattr(self, attr, v)
            else:
                self.unique_warning("L# {} not in defaults.yaml".format(ln))
        else:
            self.unique_warning("No defaults.yaml")

    def _load_scripts(self, old, new):
        """
        load default scripts if
            1. labnumber is special
            2. labnumber was a special and now unknown

        dont load if was unknown and now unknown
        this preserves the users changes
        """
        tag = new
        # tag = 2000-01 or  ba-01..
        if "-" in new:
            tag = new.split("-")[0]
            # tag = 2000 or ba

        abit = tag in ANALYSIS_MAPPING

        # if abit or bbit:  # or old in ANALYSIS_MAPPING or not old and new:
        if abit or old in ANALYSIS_MAPPING or not old:
            # set default scripts
            self._load_default_scripts(tag, new)

    def _load_default_scripts(self, labnumber_tag, labnumber):
        # if labnumber is int use key='U'
        try:
            _ = int(labnumber_tag)
            tags = [labnumber_tag, "u"]
            labnumber_tag = "u"
        except ValueError:
            tags = [labnumber_tag]

        extract_device = self.extract_device.replace(" ", "")

        is_extractable = (
            labnumber_tag in ("u", "bu", "dg")
            and extract_device not in NULL_EXTRACT_DEVICES
            and extract_device != "ExternalPipette"
        )

        # labnumber_tag = str(labnumber_tag).lower()
        if self._current_loaded_default_scripts_key in tags:
            self.debug("Scripts for {} already loaded".format(labnumber))
            return

        self.debug("load default scripts for {}".format(tags))

        self._current_loaded_default_scripts_key = None
        defaults = self._load_default_file()
        if defaults:
            labnumber_tag = next((lt for lt in tags if lt in defaults), None)
            if labnumber_tag:
                default_scripts = defaults[labnumber_tag]
                self._current_loaded_default_scripts_key = labnumber_tag
                keys = ["extraction"] if labnumber_tag == "dg" else SCRIPT_KEYS

                # set options
                self.script_options.name = default_scripts.get("options", "")

                for skey in keys:
                    new_script_name = default_scripts.get(skey, "")
                    new_script_name = remove_file_extension(new_script_name)
                    if is_extractable:
                        if skey == "extraction":
                            new_script_name = extract_device
                            try:
                                d = default_scripts[extract_device]
                                new_script_name = d["extraction"]
                            except KeyError:
                                pass
                        elif skey == "post_equilibration":
                            new_script_name = default_scripts.get(
                                skey, "pump_{}".format(extract_device)
                            )

                    script = getattr(self, "{}_script".format(skey))
                    script.name = new_script_name or ""

    def _load_default_file(self):
        # open the yaml config file
        p = os.path.join(paths.scripts_dir, "defaults.yaml")
        if not os.path.isfile(p):
            self.warning("Script defaults file does not exist {}".format(p))
            return

        defaults = yload(p)

        # convert keys to lowercase
        defaults = dict([(k.lower(), v) for k, v in defaults.items()])
        return defaults

    def _load_labnumber_meta(self, labnumber):
        if "-##-" in labnumber:
            return True

        if labnumber in self._meta_cache:
            self.debug("using cached meta values for {}".format(labnumber))
            d = self._meta_cache[labnumber]
            for attr in (
                "sample",
                "comment",
                "repository_identifier",
                "display_irradiation",
            ):
                try:
                    setattr(self, attr, d[attr])
                except KeyError:
                    self.debug(
                        "failed setting attr from cache: key={}, labnumber={}".format(
                            attr, labnumber
                        )
                    )
                    self.debug("cache={}".format(d))

            if self.mode != SIMPLE:
                self._no_clear_labnumber = True
                self.selected_irradiation = LINE_STR
                self.selected_irradiation = d["irradiation"]
                self.selected_level = d["irradiation_level"]
                self.irrad_hole = d["irradiation_position"]
                self._no_clear_labnumber = False

            if self.use_project_based_repository_identifier:
                ipp = self.irradiation_project_prefix
                project_name = d["project"]
                if ipp and project_name.startswith(ipp):
                    repo = project_name
                    if repo == "REFERENCES":
                        repo = ""
                else:
                    repo = camel_case(project_name)
                self.repository_identifier = repo

            return True
        else:
            # get a default repository_identifier
            d = dict(sample="", display_irradiation="")
            db = self.get_database()
            # convert labnumber (a, bg, or 10034 etc)
            self.debug("load meta for {}".format(labnumber))
            with db.session_ctx():
                ip = db.get_identifier(labnumber)
                if ip:
                    pos = ip.position
                    # set sample and irrad info
                else:
                    self.warning_dialog(
                        "{} does not exist.\n\n"
                        'Add using "Entry>>Labnumber"\n'
                        'or "Utilities>>Import"\n'
                        "or manually".format(labnumber)
                    )
                    return

                self.sample = ip.sample.name

                project = ip.sample.project
                project_name = project.name
                try:
                    pi_name = project.principal_investigator.name
                except (AttributeError, TypeError):
                    print("project has pi issue. {}".format(project_name))
                    pass

                ipp = self.irradiation_project_prefix
                d["project"] = project_name
                d["repository_identifier"] = ""
                self.debug(
                    "trying to set repository based on project name={}".format(
                        project_name
                    )
                )
                # if project_name == 'J-Curve':
                #     irrad = ip.level.irradiation.name
                #     self.repository_identifier = '{}{}'.format(ipp, irrad)
                if project_name != "REFERENCES":
                    if self.use_project_based_repository_identifier:
                        if ipp and project_name.startswith(ipp):
                            repo = project_name
                        else:
                            repo = camel_case(project_name)

                        self.debug("unprepped repo={}".format(repo))
                        repo = prep_repo_name(repo)
                        self.debug("setting repository to {}".format(repo))

                        self.repository_identifier = repo
                        if not self.dvc.check_remote_repository_exists(repo):
                            self.repository_identifier = ""
                            if self.confirmation_dialog(
                                'Repository Identifier "{}" does not exist. Would you '
                                "like to add it?".format(repo)
                            ):
                                m = 'Repository "{}({})"'.format(repo, pi_name)
                                # this will set self.repository_identifier
                                if self._add_repository(repo, pi_name):
                                    self.information_dialog(
                                        "{} added successfully".format(m)
                                    )
                                else:
                                    self.warning_dialog(
                                        "Failed to add {}."
                                        "\nResolve issue before proceeding!!".format(m)
                                    )

                d["repository_identifier"] = self.repository_identifier

                if self.mode != SIMPLE:
                    self._make_irrad_level(ip)
                    d["irradiation"] = self.selected_irradiation
                    d["irradiation_position"] = pos
                    d["irradiation_level"] = self.selected_level
                    d["display_irradiation"] = self.display_irradiation

                d["sample"] = self.sample
                if self.auto_fill_comment:
                    self._set_auto_comment()
                d["comment"] = self.comment
                self._meta_cache[labnumber] = d
                return True

    def _load_labnumber_defaults(self, old, labnumber, special):
        self.debug("load labnumber defaults {} {}".format(labnumber, special))
        kw = {}
        if special:
            ln = labnumber.split("-")[0]
            if ln == "dg":
                kw["attrs"] = (EXTRACT_VALUE, EXTRACT_UNITS)
            else:
                kw["attrs"] = (CLEANUP, PRECLEANUP, POSTCLEANUP, DURATION)
                kw["overwrite"] = False
        else:
            ln = "u"

        self._load_defaults(ln, **kw)
        self._load_scripts(old, labnumber)
        self._load_extraction_info()

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_edit_mode_label(self):
        return "Editing" if self.edit_mode else ""

    def _get_extractable(self):
        ln = self.labnumber
        if "-" in ln:
            ln = ln.split("-")[0]

        return ln not in NON_EXTRACTABLE

    @cached_property
    def _get_repository_identifiers(self):
        db = self.get_database()
        ids = [""]
        if db and db.connect():
            with db.session_ctx(use_parent_session=False):
                repoids = db.get_repository_identifiers()
                if repoids:
                    ids.extend(repoids)
        return ids

    @cached_property
    def _get_irradiations(self):
        db = self.get_database()
        if db is None or not db.connect():
            return []
        with db.session_ctx(use_parent_session=False):
            irradiations = db.get_irradiation_names()
        return ["Irradiation", LINE_STR] + irradiations

    @cached_property
    def _get_levels(self):
        levels = []
        db = self.get_database()
        if db is None or not db.connect():
            return []

        if self.selected_irradiation not in ("IRRADIATION", LINE_STR):
            with db.session_ctx(use_parent_session=False):
                irrad = db.get_irradiation(self.selected_irradiation)
                if irrad:
                    levels = sorted([li.name for li in irrad.levels])
        if levels:
            self.selected_level = levels[0] if levels else "LEVEL"

        return ["Level", LINE_STR] + levels

    @cached_property
    def _get_labnumbers(self):
        if self._identifiers:
            lns = self._identifiers
        else:
            lns = []
            db = self.get_database()
            if db is None or not db.connect():
                return []

            if self.selected_level and self.selected_level not in ("Level", LINE_STR):
                with db.session_ctx(use_parent_session=False):
                    lns = db.get_level_identifiers(
                        self.selected_irradiation, self.selected_level
                    )

        return lns

    @cached_property
    def _get_display_labnumbers(self):
        lns = {}
        if self.selected_level and self.selected_level not in ("Level", LINE_STR):
            db = self.get_database()
            if db is not None and db.connect():
                with db.session_ctx(use_parent_session=False):
                    lns = db.get_level_identifiers(
                        self.selected_irradiation,
                        self.selected_level,
                        with_summary=True,
                    )
                if lns:
                    lns = dict(lns)

        return lns

    def _get_position(self):
        return self._position

    def _set_position(self, pos):
        self._position = pos

    def _get_info_label(self):
        return "{} {} {}".format(self.labnumber, self.display_irradiation, self.sample)

    def _validate_position(self, pos):
        if not pos.strip():
            return ""

        for r, _, _, name in (
            SLICE_REGEX,
            SSLICE_REGEX,
            PSLICE_REGEX,
            TRANSECT_REGEX,
            POSITION_REGEX,
            XY_REGEX,
            SCAN_REGEX,
        ):
            if r.match(pos):
                self.debug("matched {} to {}".format(name, pos))
                return pos
        else:
            for po in pos.split(","):
                try:
                    int(po)
                except ValueError:
                    ok = False
                    break
            else:
                ok = True

        if ok:
            return pos

    def _get_edit_pattern_label(self):
        return "Edit" if self._use_pattern() else "New"

    def _get_edit_template_label(self):
        return "Edit" if self._use_template() else "New"

    def _get_patterns(self):
        return ["Pattern", LINE_STR] + self.remote_patterns

    def _get_templates(self):
        p = paths.incremental_heat_template_dir
        extension = ".txt"
        temps = list_directory(p, extension)

        # filter temps
        # sort by user_counts
        # sort top ten alphabetically
        # place separator between top ten and the rest

        top_ten, rest = self._filter_templates(temps)
        if top_ten:
            top_ten.append(LINE_STR)
            top_ten.extend(rest)
            temps = top_ten
        else:
            temps = rest

        if self.template in temps:
            self.template = temps[temps.index(self.template)]
        else:
            self.template = "Step Heat Template"

        return ["Step Heat Template", LINE_STR] + temps

    def _filter_templates(self, temps):
        """
        filter templates based on user counts
        :return:
        """
        p = os.path.join(paths.hidden_dir, "iht_counts.{}".format(self.username))
        if os.path.isfile(p):
            with open(p, "rb") as rfile:
                ucounts = pickle.load(rfile)

            cs = [(ti, ucounts.get(ti, 0)) for ti in temps]
            cs = sorted(cs, key=lambda x: x[1], reverse=True)
            top_ten, rest = cs[:10], cs[10:]
            top_ten, rs = partition(top_ten, lambda x: x[1] > 0)

            rest.extend(rs)
            top_ten = [ti[0] for ti in top_ten]
            rest = [ri[0] for ri in rest]

        else:
            rest = temps
            top_ten = None
        return top_ten, rest

    def _get_conditionals(self):
        p = paths.conditionals_dir
        extension = ".yaml"
        temps = list_directory(p, extension, remove_extension=True)
        self.debug("loading conditionals from {}".format(p))

        return [NULL_STR] + temps

    def _get_beam_diameter(self):
        bd = ""
        if self._beam_diameter is not None:
            bd = self._beam_diameter
        return bd

    def _set_beam_diameter(self, v):
        try:
            self._beam_diameter = float(v)
            self._update_run_values("beam_diameter", self._beam_diameter)
        except (ValueError, TypeError):
            pass

    def _get_conditionals_str(self):
        r = ""
        if self.conditionals_path != NULL_STR:
            r = os.path.basename(self.conditionals_path)
        elif (
            self.use_simple_truncation
            and self.trunc_attr is not None
            and self.trunc_comp is not None
            and self.trunc_crit is not None
        ):
            r = "{}{}{}, {}".format(
                self.trunc_attr, self.trunc_comp, self.trunc_crit, self.trunc_start
            )
        return r

    @cached_property
    def _get_flux(self):
        return self._get_flux_from_datastore()

    @cached_property
    def _get_flux_error(self):
        return self._get_flux_from_datastore(attr="err")

    def _get_flux_from_datastore(self, attr="j"):
        j = 0

        identifier = self.labnumber

        if "-##-" not in identifier:
            if identifier and self.irrad_hole:
                j = (
                    self.dvc.get_flux(
                        self.selected_irradiation,
                        self.selected_level,
                        int(self.irrad_hole),
                    )
                    or 0
                )
                if attr == "err":
                    j = std_dev(j)
                else:
                    j = nominal_value(j)

        return j

    def _set_flux(self, a):
        if self.labnumber and a is not None:
            self._flux = a

    def _set_flux_error(self, a):
        if self.labnumber and a is not None:
            self._flux_error = a

    def _get_end_after(self):
        return self._end_after

    def _set_end_after(self, v):
        self.set_end_after(v)
        self._end_after = v

    def _set_auto_comment(self, temp=None):
        if temp is None:
            temp = self._comment_templater

        if temp is None:
            from pychron.experiment.utilities.comment_template import CommentTemplater

            temp = CommentTemplater()
            self._comment_templater = temp

        c = temp.render(self)
        self.debug("Comment template rendered = {}".format(c))
        self.comment = c

    def _set_conditionals(self, t):
        for s in self._selected_runs:
            s.conditionals = t

        self.changed = True
        self.refresh_table_needed = True

    def _update_script_lists(self):
        self.debug("update script lists")
        for si in SCRIPT_NAMES:
            si = getattr(self, si)
            si.refresh_lists = True

    def _iter_scripts(self):
        return (getattr(self, s) for s in SCRIPT_NAMES)

    def _add_repository(self, name=None, pi_name=None):
        if self.dvc:
            a = RepositoryIdentifierEntry(dvc=self.dvc)

            with self.dvc.session_ctx(use_parent_session=False):
                # a.available = self.dvc.get_repository_identifiers()
                a.principal_investigators = self.dvc.get_principal_investigator_names()

            if name:
                a.value = name
            if pi_name:
                a.principal_investigator = pi_name

            if a.do():
                self.debug('set repo identifier to ="{}"'.format(a.value))
                self.repository_identifier_dirty = True
                self.repository_identifier = a.value
                return True
        else:
            self.warning_dialog("DVC Plugin not enabled")

    def _apply_comment_template(self):
        ct = self._comment_templater
        if not ct:
            ct = CommentTemplater()

        for idn, runs in groupby_key(self._selected_runs, "identifier"):
            with self.dvc.session_ctx():
                ipos = self.dvc.get_identifier(idn)

                if ipos:
                    level = ipos.level
                    if level:
                        pos = ipos.position

                        obj = {"irrad_level": level.name, "irrad_hole": pos}
                        cmt = ct.render(obj)
                        for ri in runs:
                            ri.comment = cmt

    def _edit_run_blocks(self):
        from pychron.experiment.queue.run_block import RunBlockEditView

        rbev = RunBlockEditView()
        rbev.edit_traits()

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _extract_value_changed(self, new):
        if new:
            if self.extract_units == NULL_STR:
                self.extract_units = self._default_extract_units

    def _clear_repository_identifier_button_fired(self):
        self.debug("clear repository identifiier")

        self.repository_identifier = ""
        self.repository_identifier_dirty = True

    def _set_repository_identifier_button_fired(self):
        self.debug("set repository identifier={}".format(self.repository_identifier))
        if self._selected_runs:
            for si in self._selected_runs:
                si.repository_identifier = self.repository_identifier
            self.refresh_table_needed = True

    def _add_repository_identifier_fired(self):
        self._add_repository()

    @on_trait_change("use_name_prefix, name_prefix")
    def _handle_prefix(self, name, new):
        for si in self._iter_scripts():
            setattr(si, name, new)

    def _edit_frequency_button_fired(self):
        from pychron.experiment.utilities.frequency_edit_view import FrequencyEditView

        fev = FrequencyEditView(model=self.frequency_model)
        fev.edit_traits(kind="modal")

    def _edit_comment_template_fired(self):
        from pychron.experiment.utilities.comment_template import CommentTemplater
        from pychron.experiment.utilities.template_view import CommentTemplateView

        if self._comment_templater is None:
            ct = CommentTemplater()
            self._comment_templater = ct

        ctv = CommentTemplateView(model=ct)
        info = ctv.edit_traits()
        if info.result:
            self._set_auto_comment(ct)

    def _use_simple_truncation_changed(self, new):
        if new:
            self.conditionals_path = NULL_STR

    def _conditionals_path_changed(self, new):
        if not new == NULL_STR:
            self.use_simple_con = False

    @on_trait_change(
        "[measurement_script, post_measurement_script, "
        "post_equilibration_script, extraction_script]:[edit_event, default_event]"
    )
    def _handle_script_events(self, obj, name, old, new):
        self._auto_save()
        if name == "edit_event":
            app = self.application
            task = app.open_task("pychron.pyscript.task")
            path, kind = new
            task.kind = kind
            task.open(path=path)
            task.set_on_save_as_handler(self._update_script_lists)
            task.set_on_close_handler(self._update_script_lists)
        elif name == "default_event":
            if not self.labnumber:
                self.information_dialog(
                    "Please select a labnumber/identifier before trying to set default scripts"
                )
                return

            at = get_analysis_type_shortname(self.labnumber)
            self.debug("{}".format(self.labnumber, at))
            self._set_default_file(at, new[0], new[1])

    def _set_default_file(self, at, name, scriptlabel):
        defaults = self._load_default_file()
        try:
            for ai in (at, at.capitalize(), at.upper(), at.lower()):
                atd = defaults[ai]
        except KeyError:
            pass

        atd[scriptlabel.lower()] = name

        p = os.path.join(paths.scripts_dir, "defaults.yaml")
        with open(p, "w") as wfile:
            yaml.dump(defaults, wfile)

    def _load_defaults_button_fired(self):
        if self.labnumber:
            self._load_default_scripts(self.labnumber)

    def _default_fits_button_fired(self):
        # from pychron.experiment.fits.measurement_fits_selector import MeasurementFitsSelector, \
        #     MeasurementFitsSelectorView
        from pychron.pyscripts.tasks.pyscript_editor import PyScriptEdit
        from pychron.pyscripts.context_editors.measurement_context_editor import (
            MeasurementContextEditor,
        )
        from pychron.core.fits.measurement_fits_selector import MeasurementFitsSelector
        from pychron.core.fits.measurement_fits_selector import (
            MeasurementFitsSelectorView,
        )

        m = MeasurementFitsSelector()
        sp = self.measurement_script.script_path()
        m.open(sp)

        f = MeasurementFitsSelectorView(model=m)
        info = f.edit_traits(kind="livemodal")
        if info.result:
            # update the default_fits entry in the docstr
            ed = PyScriptEdit()
            ed.context_editor = MeasurementContextEditor()
            ed.open_script(sp)
            ed.context_editor.default_fits = str(m.name)
            ed.update_docstr()

    def _new_conditionals_button_fired(self):
        name = edit_conditionals(
            self.conditionals_path,
            root=paths.conditionals_dir,
            save_as=True,
            title="Edit Run Conditionals",
            kinds=EDITABLE_RUN_CONDITIONALS,
        )
        if name:
            self.load_conditionals()
            self.conditionals_path = os.path.splitext(name)[0]

    def _edit_conditionals_button_fired(self):
        if self.conditionals_path and self.conditionals_path != NULL_STR:
            edit_conditionals(
                self.conditionals_path,
                root=paths.conditionals_dir,
                title="Edit Run Conditionals",
                kinds=EDITABLE_RUN_CONDITIONALS,
            )
            self.load_conditionals()
        else:
            self.information_dialog("Please select conditionals to edit")

    @on_trait_change("trunc_+, conditionals_path, apply_conditionals_button")
    def _handle_conditionals(self, obj, name, old, new):
        if self.edit_mode and self._selected_runs and not self.suppress_update:
            self._auto_save()
            t = self.conditionals_str
            self._set_conditionals(t)

    # @on_trait_change('''
    # cleanup,
    # collection_time_zero_offset,
    # comment,
    # delay_after
    # duration,
    # extract_value,
    # extract_units,
    # light_value,
    # overlap,
    # pattern,
    # pre_cleanup,
    # position,
    # post_cleanup,
    # ramp_duration,
    # repository_identifier,
    # skip,
    # use_cdd_warming,
    # weight
    # ''')
    @on_trait_change(
        ",".join(
            (
                CLEANUP,
                COLLECTION_TIME_ZERO_OFFSET,
                COMMENT,
                DELAY_AFTER,
                DURATION,
                EXTRACT_VALUE,
                EXTRACT_UNITS,
                LIGHT_VALUE,
                OVERLAP,
                PATTERN,
                PRECLEANUP,
                POSITION,
                POSTCLEANUP,
                CRYO_TEMP,
                RAMP_DURATION,
                REPOSITORY_IDENTIFIER,
                SKIP,
                USE_CDD_WARMING,
                WEIGHT,
                DISABLE_BETWEEN_POSITIONS,
            )
        )
    )
    def _edit_handler(self, name, new):
        if name == PATTERN:
            if not self._use_pattern():
                new = ""
        self._update_run_values(name, new)

    @on_trait_change(
        """measurement_script:name, 
extraction_script:name, 
post_measurement_script:name,
post_equilibration_script:name"""
    )
    def _edit_script_handler(self, obj, name, new):
        self.debug(
            "name={}, new={}, suppress={}".format(obj.label, new, self.suppress_update)
        )
        if obj.label == "Measurement":
            self.default_fits_enabled = bool(new and new not in (NULL_STR,))

        if self.edit_mode and not self.suppress_update:
            self._auto_save()
            if obj.label == "Extraction":
                self._load_extraction_info(obj)
            if self._selected_runs:
                for si in self._selected_runs:
                    name = "{}_script".format(obj.label.lower().replace(" ", "_"))
                    setattr(si, name, new)
                self.refresh()

    @on_trait_change("script_options:name")
    def _edit_script_options_handler(self, new):
        self._auto_save()
        if self.edit_mode and not self.suppress_update:
            if self._selected_runs:
                for si in self._selected_runs:
                    si.script_options = new
                self.changed = True
                self.refresh_table_needed = True

    def _skip_changed(self):
        self.update_info_needed = True

    def _labnumber_changed(self, old, new):
        self.debug("labnumber changed old:{}, new:{}".format(old, new))
        if new:
            special = False
            try:
                _ = int(new)
            except ValueError:
                special = True

            if not special:
                sname = SPECIAL_IDENTIFIER
            else:
                tag = new.split("-")[0]
                sname = ANALYSIS_MAPPING.get(tag, SPECIAL_IDENTIFIER)

            self._suppress_special_labnumber_change = True
            self.special_labnumber = sname
            self._suppress_special_labnumber_change = False

            if self._load_labnumber_meta(new):
                self.refresh_flux_needed = True
                if self._set_defaults:
                    self._load_labnumber_defaults(old, new, special)
        else:
            self.sample = ""

    def _project_changed(self):
        self.debug("project changed")
        self._clear_labnumber()

    def _selected_irradiation_changed(self):
        self.debug("irradiation changed")
        self._clear_labnumber()
        self.selected_level = "Level"

    def _selected_level_changed(self):
        self.debug("level changed")
        self._clear_labnumber()

    def _special_labnumber_changed(self):
        if self._suppress_special_labnumber_change:
            return

        if self.special_labnumber not in (SPECIAL_IDENTIFIER, LINE_STR, ""):
            ln = convert_special_name(self.special_labnumber)
            self.debug("special ln changed {}, {}".format(self.special_labnumber, ln))
            if ln:
                if ln not in ("dg", "pa"):
                    msname = self.mass_spectrometer[0].capitalize()
                    if ln in SPECIAL_KEYS and not ln.startswith("bu"):
                        ln = make_standard_identifier(ln, "##", msname)
                    else:
                        edname = ""
                        ed = self.extract_device
                        if ed not in ("Extract Device", LINE_STR):
                            edname = "".join([x[0].capitalize() for x in ed.split(" ")])
                        ln = make_special_identifier(ln, edname, msname)

                self._labnumber_changed(self.labnumber, ln)
                self.labnumber = ln

            self._frequency_enabled = True

            if not self._selected_runs:
                self.edit_mode = True
        else:
            self.debug("special labnumber changed else")
            self.labnumber = ""
            self._frequency_enabled = False

    def _auto_fill_comment_changed(self):
        if self.auto_fill_comment:
            self._set_auto_comment()
        else:
            self.comment = ""

    def _edit_template_fired(self):
        temp = self._new_template()
        temp.names = list_directory(
            paths.incremental_heat_template_dir, extension=".txt"
        )
        temp.on_trait_change(self._template_closed, "close_event")
        open_view(temp)

    def _edit_pattern_fired(self):
        pat = self._new_pattern()
        pat.on_trait_change(self._pattern_closed, "close_event")
        open_view(pat)

    def _edit_mode_button_fired(self):
        self.edit_mode = not self.edit_mode

    def _clear_conditionals_fired(self):
        if self.edit_mode and self._selected_runs and not self.suppress_update:
            self._set_conditionals("")

    def _aliquot_changed(self):
        if self.suppress_update:
            return

        if self.edit_mode:
            a = int(self.aliquot)
            for si in self._selected_runs:
                si.user_defined_aliquot = a

            self.refresh_table_needed = True
            self.changed = True

    def _save_flux_button_fired(self):
        self._save_flux()

    def _edit_mode_changed(self):
        self.suppress_update = True
        self.aliquot = 0
        self.suppress_update = False

    def _apply_comment_button_fired(self):
        if self._selected_runs and self.edit_mode:
            self._apply_comment_template()
        else:
            self.warning_dialog("Please select one or more runs")

    # ===============================================================================
    # defaults
    # ================================================================================
    def _script_factory(self, label, name=NULL_STR, kind="ExtractionLine"):
        s = Script(
            label=label,
            use_name_prefix=self.use_name_prefix,
            name_prefix=self.name_prefix,
            mass_spectrometer=self.mass_spectrometer,
            name=name,
            kind=kind,
        )
        return s

    def _extraction_script_default(self):
        return self._script_factory("Extraction", "extraction")

    def _measurement_script_default(self):
        return self._script_factory("Measurement", "measurement", kind="Measurement")

    def _post_measurement_script_default(self):
        return self._script_factory("Post Measurement", "post_measurement")

    def _post_equilibration_script_default(self):
        return self._script_factory("Post Equilibration", "post_equilibration")

    def _remove_file_extension(self, name):
        if not name:
            return name

        if name is NULL_STR:
            return NULL_STR

        name = remove_extension(name)
        return name

    def _factory_view_default(self):
        return self.factory_view_klass(model=self)

    def _datahub_default(self):
        dh = Datahub()
        dh.mainstore = self.application.get_service(DVC_PROTOCOL)
        dh.bind_preferences()
        return dh

    @property
    def run_block_enabled(self):
        return self.run_block not in ("RunBlock", LINE_STR)


# ============= EOF =============================================
