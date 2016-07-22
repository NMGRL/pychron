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
from apptools.preferences.preference_binding import bind_preference
from traits.api import String, Str, Property, Any, Float, Instance, Int, List, \
    cached_property, on_trait_change, Bool, Button, Event, Enum, Dict
from traits.trait_errors import TraitError
# ============= standard library imports ========================
import pickle
import yaml
import os
from uncertainties import nominal_value, std_dev
# ============= local library imports  ==========================

from pychron.core.helpers.iterfuncs import partition
from pychron.core.helpers.strtools import camel_case
from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.entry.entry_views.repository_entry import RepositoryIdentifierEntry
from pychron.envisage.view_util import open_view
from pychron.experiment.conditional.conditionals_edit_view import edit_conditionals
from pychron.experiment.datahub import Datahub
from pychron.experiment.queue.run_block import RunBlock
from pychron.experiment.utilities.frequency_edit_view import FrequencyModel
from pychron.persistence_loggable import PersistenceLoggable
from pychron.experiment.utilities.position_regex import SLICE_REGEX, PSLICE_REGEX, \
    SSLICE_REGEX, TRANSECT_REGEX, POSITION_REGEX, CSLICE_REGEX, XY_REGEX
from pychron.pychron_constants import NULL_STR, SCRIPT_KEYS, SCRIPT_NAMES, LINE_STR
from pychron.experiment.automated_run.factory_view import FactoryView
from pychron.experiment.utilities.identifier import convert_special_name, ANALYSIS_MAPPING, NON_EXTRACTABLE, \
    make_special_identifier, make_standard_identifier, SPECIAL_KEYS
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.paths import paths
from pychron.experiment.script.script import Script, ScriptOptions
from pychron.experiment.queue.increment_heat_template import LaserIncrementalHeatTemplate, BaseIncrementalHeatTemplate
from pychron.experiment.utilities.human_error_checker import HumanErrorChecker
from pychron.core.helpers.filetools import list_directory, add_extension, list_directory2, remove_extension
from pychron.lasers.pattern.pattern_maker_view import PatternMakerView
from pychron.core.ui.gui import invoke_in_main_thread


class EditEvent(Event):
    pass


class UpdateSelectedCTX(object):
    _factory = None

    def __init__(self, factory):
        self._factory = factory

    def __enter__(self):
        self._factory.set_labnumber = False
        self._factory.set_position = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._factory.set_labnumber = True
        self._factory.set_position = True


def EKlass(klass):
    return klass(enter_set=True, auto_set=False)


def increment_value(m, increment=1):
    s = ','
    if s not in m:
        m = (m,)
        s = ''
    else:
        m = m.split(s)

    ms = []
    for mi in m:
        try:
            ms.append(str(int(mi) + increment))
        except ValueError:
            return s.join(m)

    return s.join(ms)


def increment_position(pos):
    for regex, sfunc, ifunc, _ in (SLICE_REGEX, SSLICE_REGEX,
                                   PSLICE_REGEX, CSLICE_REGEX, TRANSECT_REGEX):
        if regex.match(pos):
            return ifunc(pos)
    else:
        m = map(int, pos.split(','))
        ms = []
        offset = max(m) - min(m)
        inc = 1
        for i, mi in enumerate(m):
            try:
                inc = m[i + 1] - mi
            except IndexError:
                pass
            ms.append(mi + offset + inc)
        return ','.join(map(str, ms))


def generate_positions(pos):
    for regex, func, ifunc, _ in (SLICE_REGEX, SSLICE_REGEX,
                                  PSLICE_REGEX, CSLICE_REGEX, TRANSECT_REGEX):
        if regex.match(pos):
            return func(pos)
    else:
        return [pos]


def get_run_blocks():
    p = paths.run_block_dir
    blocks = list_directory2(p, '.txt', remove_extension=True)
    return ['RunBlock', LINE_STR] + blocks


def get_comment_templates():
    p = paths.comment_templates
    templates = list_directory(p)
    return templates


def remove_file_extension(name, ext='.py'):
    if not name:
        return name

    if name is NULL_STR:
        return NULL_STR

    if name.endswith('.py'):
        name = name[:-3]

    return name


class AutomatedRunFactory(DVCAble, PersistenceLoggable):
    datahub = Instance(Datahub)
    undoer = Any
    edit_event = Event

    # ============== scripts =============
    extraction_script = Instance(Script)
    measurement_script = Instance(Script)
    post_measurement_script = Instance(Script)
    post_equilibration_script = Instance(Script)

    script_options = Instance(ScriptOptions, ())
    load_defaults_button = Button('Default')

    default_fits_button = Button
    default_fits_enabled = Bool
    # ===================================

    human_error_checker = Instance(HumanErrorChecker, ())
    factory_view = Instance(FactoryView)
    factory_view_klass = FactoryView

    set_labnumber = True
    set_position = True

    labnumber = String(enter_set=True, auto_set=False)
    update_labnumber = Event

    aliquot = EKlass(Int)
    special_labnumber = Str('Special Labnumber')

    db_refresh_needed = Event
    auto_save_needed = Event

    labnumbers = Property(depends_on='project, selected_level')

    repository_identifier = Str
    repository_identifiers = Property(depends_on='repository_identifier_dirty, db_refresh_needed')
    add_repository_identifier = Event
    repository_identifier_dirty = Event
    set_repository_identifier_button = Event


    selected_irradiation = Str('Irradiation')
    irradiations = Property(depends_on='db, db_refresh_needed')
    selected_level = Str('Level')
    levels = Property(depends_on='selected_irradiation, db')

    flux = Property(Float, depends_on='labnumber')
    flux_error = Property(Float, depends_on='labnumber')

    _flux = None
    _flux_error = None
    save_flux_button = Button

    skip = Bool(False)
    end_after = Property(Bool, depends_on='_end_after')
    _end_after = Bool(False)

    weight = Float
    comment = String(auto_set=False, enter_set=True)
    auto_fill_comment = Bool
    comment_template = Str
    comment_templates = List
    edit_comment_template = Button

    position = Property(depends_on='_position')
    _position = String

    # ===========================================================================
    # measurement
    # ===========================================================================
    use_cdd_warming = Bool
    collection_time_zero_offset = Float(0)

    # ===========================================================================
    # extract
    # ===========================================================================
    # extract_value = Property(
    # EKlass(Float),
    # depends_on='_extract_value')
    # _extract_value = Float
    extract_value = EKlass(Float)
    extract_units = Str(NULL_STR)
    extract_units_names = List(['', 'watts', 'temp', 'percent'])
    _default_extract_units = 'watts'

    ramp_duration = EKlass(Float)

    overlap = EKlass(String)
    duration = EKlass(Float)
    cleanup = EKlass(Float)
    beam_diameter = Property(EKlass(String), depends_on='_beam_diameter')
    _beam_diameter = String

    pattern = String('Pattern')
    patterns = List
    remote_patterns = List

    edit_pattern = Event
    edit_pattern_label = Property(depends_on='pattern')
    # ===========================================================================
    # templates
    # ===========================================================================
    template = String('Step Heat Template')
    templates = List

    edit_template = Event
    edit_template_label = Property(depends_on='template')

    # ===========================================================================
    # conditionals
    # ===========================================================================
    trunc_attr = String('age')
    trunc_attrs = List(['age',
                        'kca',
                        'kcl',
                        'age.std',
                        'kca.std',
                        'kcl.std',
                        'rad40_percent',
                        'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36'])
    trunc_comp = Enum('>', '<', '>=', '<=', '=')
    trunc_crit = Float(5000, enter_set=True, auto_set=False)
    trunc_start = Int(100, enter_set=True, auto_set=False)
    use_simple_truncation = Bool

    conditionals_str = Property(depends_on='trunc_+')
    conditionals_path = String
    conditionals = List
    clear_conditionals = Button
    edit_conditionals_button = Button
    new_conditionals_button = Button

    # ===========================================================================
    # blocks
    # ===========================================================================
    run_block = Str('RunBlock')
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
    irrad_hole = Str

    info_label = Property(depends_on='labnumber, display_irradiation, sample')
    extractable = Property(depends_on='labnumber')

    update_info_needed = Event
    refresh_table_needed = Event
    changed = Event
    suppress_update = False

    edit_mode = Bool(False)
    edit_mode_label = Property(depends_on='edit_mode')
    edit_enabled = Bool(False)

    mass_spectrometer = String
    extract_device = Str
    username = Str

    pattributes = ('collection_time_zero_offset',
                   'selected_irradiation', 'selected_level',
                   'extract_value', 'extract_units', 'cleanup',
                   'duration', 'beam_diameter', 'ramp_duration', 'overlap',
                   'pattern', 'labnumber', 'position',
                   'weight', 'comment', 'template',
                   'use_simple_truncation', 'conditionals_path')

    suppress_meta = False

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
        bind_preference(self, 'use_name_prefix', 'pychron.pyscript.use_name_prefix')
        bind_preference(self, 'name_prefix', 'pychron.pyscript.name_prefix')
        super(AutomatedRunFactory, self).__init__(*args, **kw)

    def setup_files(self):
        self.load_templates()
        self.load_run_blocks()
        # self.remote_patterns = self._get_patterns()
        self.load_patterns()
        self.load_conditionals()
        # self.load_comment_templates()

    def activate(self, load_persistence):

        # self.load_run_blocks()
        self.conditionals_path = NULL_STR
        if load_persistence:
            self.load()

        self.setup_files()

        # db = self.db
        # with db.session_ctx():
        # ms = db.get_mass_spectrometer(self.mass_spectrometer)
        # ed = db.get_extraction_device(self.extract_device)
        #     self._mass_spectrometers = ms
        #     self._extract_devices = ed

    def deactivate(self):
        self.dump(verbose=True)

    def set_end_after(self, v):
        self._update_run_values('end_after', v)

    def update_selected_ctx(self):
        return UpdateSelectedCTX(self)

    def check_run_addition(self, runs, load_name):
        """
            check if its ok to add runs to the queue.
            ie. do they have any missing values.
                does the labnumber match the loading

            return True if ok to add runs else False
        """
        hec = self.human_error_checker
        ret = hec.check_runs(runs, test_all=True)
        if ret:
            hec.report_errors(ret)
            return False

        return True

    # def load_comment_templates(self):
    # self.comment_templates = self._get_comment_templates()

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
        self.debug('len selected runs {}'.format(len(runs)))
        run = None

        self._selected_runs = runs

        if runs:
            run = runs[0]
            self._set_defaults = False
            self._clone_run(run, set_labnumber=self.set_labnumber,
                            set_position=self.set_position)
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
        self.mass_spectrometer = new
        # print SCRIPT_NAMES
        for s in self._iter_scripts():
            # print s.kind, s, new
            s.mass_spectrometer = new
            s.refresh_lists = True

    def set_extract_device(self, new):
        new = new.lower()
        self.extract_device = new
        for s in self._iter_scripts():
            s.extract_device = new

    def new_runs(self, exp_queue, positions=None, auto_increment_position=False,
                 auto_increment_id=False):
        """
            returns a list of runs even if its only one run
            also returns self.frequency if using special labnumber else None
        """
        self._auto_save()

        if self.run_block not in ('RunBlock', LINE_STR):
            arvs, freq = self._new_run_block()
        else:
            arvs, freq = self._new_runs(exp_queue, positions=positions)

        if auto_increment_id:
            v = increment_value(self.labnumber)
            # invoke_in_main_thread(self.trait_set, _labnumber=v)
            invoke_in_main_thread(self.trait_set, labnumber=v)

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

    # ===============================================================================
    # private
    # ===============================================================================

    def _auto_save(self):
        self.auto_save_needed = True

    # def _new_runs(self, positions, extract_group_cnt=0):
    def _new_run_block(self):
        p = os.path.join(paths.run_block_dir, add_extension(self.run_block, '.txt'))
        block = RunBlock(extract_device=self.extract_device,
                         mass_spectrometer=self.mass_spectrometer)
        return block.make_runs(p), self.frequency_model.frequency

    def _new_runs(self, exp_queue, positions):
        ln, special = self._make_short_labnumber()
        freq = self.frequency_model.frequency if special else None
        self.debug('Frequency={}'.format(freq))
        if not special or ln == 'dg':
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
        # print positions, 'fff'
        for i, p in enumerate(positions):
            # if set_pos:
            p = str(p)
            if template:
                arvs.extend(self._render_template(exp_queue, p, i))
            else:
                arvs.append(self._new_run(position=str(p),
                                          excludes=['position']))
        return arvs

    def _make_irrad_level(self, ipos):
        il = ''
        if ipos is not None:
            level = ipos.level
            if level:
                irrad = level.irradiation
                hole = ipos.position
                irradname = irrad.name
                self.irrad_hole = str(hole)
                self.irrad_level = irrad_level = str(level.name)
                if irradname == 'NoIrradiation':
                    il = NULL_STR
                else:
                    il = '{} {}:{}'.format(irradname, level.name, hole)
            else:
                irradname = ''
                irrad_level = ''

            self._no_clear_labnumber = True
            self.selected_irradiation = irradname
            self.selected_level = irrad_level
            self._no_clear_labnumber = False

        self.display_irradiation = il

    def _new_run(self, excludes=None, **kw):

        # need to set the labnumber now because analysis_type depends on it
        arv = self._spec_klass(labnumber=self.labnumber, **kw)

        if excludes is None:
            excludes = []

        if arv.analysis_type in ('blank_unknown', 'pause', 'blank_extractionline'):
            excludes.extend(('extract_value', 'extract_units', 'pattern', 'beam_diameter'))
            if arv.analysis_type == 'pause':
                excludes.extend(('cleanup', 'position'))
        elif arv.analysis_type not in ('unknown', 'degas'):
            excludes.extend(('position', 'extract_value', 'extract_units', 'pattern',
                             'cleanup', 'duration', 'beam_diameter'))

        self._set_run_values(arv, excludes=excludes)
        return arv

    def _get_run_attr(self):
        return ['position',
                'extract_value', 'extract_units', 'cleanup', 'duration',
                'use_cdd_warming',
                'conditionals_str',
                'collection_time_zero_offset',
                'pattern', 'beam_diameter',
                'weight', 'comment',
                'sample','project','material', 'username',
                'ramp_duration',
                'skip', 'mass_spectrometer', 'extract_device', 'repository_identifier']

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
            if attr == 'conditionals_str':
                sattr = 'conditionals'

            v = getattr(self, attr)
            if attr == 'pattern':
                if not self._use_pattern():
                    v = ''

            setattr(arv, sattr, v)
            setattr(arv, '_prev_{}'.format(sattr), v)

        arv.irradiation = self.selected_irradiation
        arv.irradiation_level = self.selected_level
        arv.irradiation_position = int(self.irrad_hole)

        if self.aliquot:
            self.debug('setting user defined aliquot')
            arv.user_defined_aliquot = int(self.aliquot)

        for si in SCRIPT_KEYS:
            name = '{}_script'.format(si)
            if name in excludes or si in excludes:
                continue

            s = getattr(self, name)
            setattr(arv, name, s.name)

    def _clone_run(self, run, excludes=None, set_labnumber=True, set_position=True):
        self.debug('cloning run {}. set_labnumber={}, set_position={}'.format(run.runid, set_labnumber, set_position))
        if excludes is None:
            excludes = []

        if not set_labnumber:
            excludes.append('labnumber')
        if not set_position:
            excludes.append('position')

        for attr in ('labnumber',
                     'extract_value', 'extract_units', 'cleanup', 'duration',
                     'pattern', 'beam_diameter',
                     'position',
                     'collection_time_zero_offset',
                     'use_cdd_warming',
                     'weight', 'comment'):

            if attr in excludes:
                continue
            try:
                v = getattr(run, attr)
                # self.debug('setting {}={}'.format(attr, v))
                setattr(self, attr, v)
            except TraitError, e:
                self.debug(e)

                # if run.user_defined_aliquot:
                # self.aliquot = int(run.aliquot)

        for si in SCRIPT_KEYS:
            skey = '{}_script'.format(si)
            if skey in excludes or si in excludes:
                continue

            ms = getattr(self, skey)
            sname = getattr(run, skey)
            # print sname
            ms.name = sname
            # ss = self._script_factory(label=si, name=s)
            # setattr(self, name, ss)
            # setattr(self, name, Script(name=s,
            # label=si,
            #                            mass_spectrometer=self.mass_spectrometer))
        self.script_options.name = run.script_options

    def _new_pattern(self):
        pm = PatternMakerView()

        if self._use_pattern():
            if pm.load_pattern(self.pattern):
                return pm
        else:
            return pm

    def _new_template(self):

        if self.extract_device in ('FusionsCO2', 'FusionsDiode'):
            klass = LaserIncrementalHeatTemplate
        else:
            klass = BaseIncrementalHeatTemplate

        template = klass()
        if self._use_template():
            t = os.path.join(paths.incremental_heat_template_dir, add_extension(self.template))
            template.load(t)

        return template

    def _render_template(self, exp_queue, position, offset):
        arvs = []
        template = self._new_template()
        self.debug('rendering template {}'.format(template.name))

        al = self.datahub.get_greatest_aliquot(self.labnumber)
        if al is not None:
            c = exp_queue.count_labnumber(self.labnumber)
            for st in template.steps:
                if st.value or st.duration or st.cleanup:
                    arv = self._new_run(position=position,
                                        excludes=['position'])

                    arv.trait_set(user_defined_aliquot=al + 1 + offset + c,
                                  **st.make_dict(self.duration, self.cleanup))
                    arvs.append(arv)

            self._increment_iht_count(template.name)
        else:
            self.debug('missing aliquot_pychron in mass spec secondary db')
            self.warning_dialog('Missing aliquot_pychron in mass spec secondary db. seek help')

        return arvs

    def _increment_iht_count(self, temp):
        p = os.path.join(paths.hidden_dir, 'iht_counts.{}'.format(self.username))

        ucounts = {}
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                ucounts = pickle.load(rfile)

        c = ucounts.get(temp, 0) + 1
        ucounts[temp] = c
        self.debug('incrementing users step_heat template count for {}. count= {}'.format(temp, c))
        with open(p, 'w') as wfile:
            pickle.dump(ucounts, wfile)

    def _make_short_labnumber(self, labnumber=None):
        if labnumber is None:
            labnumber = self.labnumber
        if '-' in labnumber:
            labnumber = labnumber.split('-')[0]

        special = labnumber in ANALYSIS_MAPPING
        return labnumber, special

    def _load_extraction_info(self, script=None):
        if script is None:
            script = self.extraction_script

        if '##' in self.labnumber:
            mod = script.get_parameter('modifier')
            if mod is not None:
                if isinstance(mod, int):
                    mod = '{:02d}'.format(mod)

                self.labnumber = self.labnumber.replace('##', str(mod))

    def _clear_labnumber(self):
        self.debug('clear labnumber')
        if not self._no_clear_labnumber:
            self.labnumber = ''
            self.display_irradiation = ''
            self.sample = ''
            self._suppress_special_labnumber_change=True
            self.special_labnumber = 'Special Labnumber'
            self._suppress_special_labnumber_change=False

    def _template_closed(self, obj, name, new):
        self.template = obj.name
        invoke_in_main_thread(self.load_templates)

    def _pattern_closed(self):
        invoke_in_main_thread(self.load_patterns)

    def _use_pattern(self):
        return self.pattern and self.pattern not in (LINE_STR, 'None', '',
                                                     'Pattern',
                                                     'Local Patterns',
                                                     'Remote Patterns')

    def _use_template(self):
        return self.template and self.template not in ('Step Heat Template',
                                                       LINE_STR, 'None')

    def _update_run_values(self, attr, v):
        if self.edit_mode and \
                self._selected_runs and \
                not self.suppress_update:

            self._auto_save()

            self.edit_event = dict(attribute=attr, value=v,
                                   previous_state=[(ri, getattr(ri, attr)) for ri in self._selected_runs])

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
            elif self.iso_db_man:
                self.iso_db_man.save_flux(self.labnumber, v, e)

    # ===============================================================================
    #
    # ===============================================================================
    def _load_defaults(self, ln, attrs=None, overwrite=True):
        if attrs is None:
            attrs = ('extract_value', 'extract_units',
                     'cleanup', 'duration', 'beam_diameter')

        self.debug('loading defaults for {}. ed={} attrs={}'.format(ln, self.extract_device, attrs))
        defaults = self._load_default_file()
        if defaults:
            if ln in defaults:
                grp = defaults[ln]
                ed = self.extract_device.replace(' ', '')
                if ed in grp:
                    grp = grp[ed]

                for attr in attrs:
                    if overwrite or not getattr(self, attr):
                        v = grp.get(attr)
                        if v is not None:
                            setattr(self, attr, v)
            else:
                self.unique_warning('L# {} not in defaults.yaml'.format(ln))
        else:
            self.unique_warning('No defaults.yaml')

    def _load_scripts(self, old, new):
        """
            load default scripts if
                1. labnumber is special
                2. labnumber was a special and now unknown

            dont load if was unknown and now unknown
            this preserves the users changes
        """
        tag = new
        if '-' in new:
            tag = new.split('-')[0]

        abit = tag in ANALYSIS_MAPPING
        bbit = False
        if not abit:
            try:
                int(tag)
                bbit = True
            except ValueError:
                pass

        if abit or bbit:  # or old in ANALYSIS_MAPPING or not old and new:
            # set default scripts
            self._load_default_scripts(tag, new)

    def _load_default_scripts(self, labnumber_tag, labnumber):

        # if labnumber is int use key='U'
        try:
            _ = int(labnumber_tag)
            labnumber_tag = 'u'
        except ValueError:
            pass

        labnumber_tag = str(labnumber_tag).lower()
        if self._current_loaded_default_scripts_key == labnumber:
            self.debug('Scripts for {} already loaded'.format(labnumber))
            return

        self.debug('load default scripts for {}'.format(labnumber_tag))

        self._current_loaded_default_scripts_key = None
        defaults = self._load_default_file()
        if defaults:
            if labnumber_tag in defaults:
                self._current_loaded_default_scripts_key = labnumber
                default_scripts = defaults[labnumber_tag]
                keys = SCRIPT_KEYS
                if labnumber_tag == 'dg':
                    keys = ['extraction']

                # set options
                self.script_options.name = default_scripts.get('options', '')

                for skey in keys:
                    new_script_name = default_scripts.get(skey) or ''

                    new_script_name = remove_file_extension(new_script_name)
                    if labnumber_tag in ('u', 'bu') and self.extract_device not in (NULL_STR, 'ExternalPipette'):

                        # the default value trumps pychron's
                        if self.extract_device:
                            if ' ' in self.extract_device:
                                e = self.extract_device.split(' ')[1].lower()
                                if skey == 'extraction':
                                    new_script_name = e
                                elif skey == 'post_equilibration':
                                    new_script_name = default_scripts.get(skey, 'pump_{}'.format(e))

                    elif labnumber_tag == 'dg':
                        e = self.extract_device.split(' ')[1].lower()
                        new_script_name = '{}_{}'.format(e, new_script_name)

                    script = getattr(self, '{}_script'.format(skey))
                    script.name = new_script_name

    def _load_default_file(self):
        # open the yaml config file
        p = os.path.join(paths.scripts_dir, 'defaults.yaml')
        if not os.path.isfile(p):
            self.warning('Script defaults file does not exist {}'.format(p))
            return

        with open(p, 'r') as rfile:
            defaults = yaml.load(rfile)

        # convert keys to lowercase
        defaults = dict([(k.lower(), v) for k, v in defaults.iteritems()])
        return defaults

    def _load_labnumber_meta(self, labnumber):
        if '-##-' in labnumber:
            return True

        if self.suppress_meta:
            return True

        # self._aliquot = 0
        if labnumber in self._meta_cache:
            self.debug('using cached meta values for {}'.format(labnumber))
            d = self._meta_cache[labnumber]
            for attr in ('sample', 'comment', 'repository_identifier'):
                setattr(self, attr, d[attr])

            self.selected_irradiation = d['irradiation']
            self.selected_level = d['irradiation_level']

            self.display_irradiation = d['display_irradiation']
            return True
        else:
            # get a default repository_identifier

            d = dict(sample='')
            db = self.get_database()
            # convert labnumber (a, bg, or 10034 etc)
            self.debug('load meta for {}'.format(labnumber))
            ip = db.get_identifier(labnumber)

            if ip:
                pos = ip.position
                # set sample and irrad info
                try:
                    self.sample = ip.sample.name
                    d['sample'] = self.sample

                    project = ip.sample.project
                    project_name = project.name
                    if project_name == 'J-Curve':
                        irrad = ip.level.irradiation.name
                        self.repository_identifier = 'Irradiation-{}'.format(irrad)
                    elif project_name != 'REFERENCES':
                        repo = camel_case(project_name)
                        self.repository_identifier = repo
                        if not db.get_repository(repo):
                            self.repository_identifier = ''
                            if self.confirmation_dialog('Repository Identifier "{}" does not exist. Would you '
                                                        'like to add it?'):
                                # this will set self.repository_identifier
                                self._add_repository_identifier_fired()

                except AttributeError, e:
                    print e

                d['repository_identifier'] = self.repository_identifier

                self._make_irrad_level(ip)
                d['irradiation'] = self.selected_irradiation
                d['irradiation_position'] = pos
                d['irradiation_level'] = self.selected_level

                d['display_irradiation'] = self.display_irradiation
                if self.auto_fill_comment:
                    self._set_auto_comment()
                d['comment'] = self.comment
                self._meta_cache[labnumber] = d
                return True
            else:
                self.warning_dialog('{} does not exist.\n\n'
                                    'Add using "Entry>>Labnumber"\n'
                                    'or "Utilities>>Import"\n'
                                    'or manually'.format(labnumber))

    def _load_labnumber_defaults(self, old, labnumber, special):
        self.debug('load labnumber defaults {} {}'.format(labnumber, special))
        if special:
            ln = labnumber.split('-')[0]
            if ln == 'dg':
                # self._load_extraction_defaults(ln)
                self._load_defaults(ln, attrs=('extract_value', 'extract_units'))
            else:
                self._load_defaults(ln, attrs=('cleanup', 'duration'), overwrite=False)
        else:
            self._load_defaults(labnumber if special else 'u')

        self._load_scripts(old, labnumber)
        self._load_extraction_info()

    # ===============================================================================
    # property get/set
    # ===============================================================================
    # def _get_default_fits_enabled(self):
    # return self.measurement_script.name not in ('None', '')

    def _get_edit_mode_label(self):
        return 'Editing' if self.edit_mode else ''

    def _get_extractable(self):
        ln = self.labnumber
        if '-' in ln:
            ln = ln.split('-')[0]

        return ln not in NON_EXTRACTABLE

    @cached_property
    def _get_repository_identifiers(self):
        db = self.get_database()
        ids = []
        if db and db.connect():
            ids = db.get_repository_identifiers()
        return ids

    @cached_property
    def _get_irradiations(self):
        db = self.get_database()
        if db is None or not db.connect():
            return []

        irradiations = db.get_irradiation_names()
        return ['Irradiation', LINE_STR] + irradiations

    @cached_property
    def _get_levels(self):
        levels = []
        db = self.get_database()
        if db is None or not db.connect():
            return []

        if self.selected_irradiation not in ('IRRADIATION', LINE_STR):
            irrad = db.get_irradiation(self.selected_irradiation)
            if irrad:
                levels = sorted([li.name for li in irrad.levels])
        if levels:
            self.selected_level = levels[0] if levels else 'LEVEL'

        return ['Level', LINE_STR] + levels

    # @cached_property
    # def _get_projects(self):
    #     db = self.get_database()
    #     if db is None or not db.connect():
    #         return dict()
    #
    #     keys = [(pi, pi.name) for pi in self.dvc.get_projects()]
    #     keys = [(NULL_STR, NULL_STR)] + keys
    #     return dict(keys)

    @cached_property
    def _get_labnumbers(self):
        lns = []
        db = self.get_database()
        if db is None or not db.connect():
            return []

        if self.selected_level and self.selected_level not in ('Level', LINE_STR):
            lns = db.get_level_identifiers(self.selected_irradiation, self.selected_level)

        return lns

    def _get_position(self):
        return self._position

    def _set_position(self, pos):
        self._position = pos

    def _get_info_label(self):
        return '{} {} {}'.format(self.labnumber, self.display_irradiation, self.sample)

    def _validate_position(self, pos):
        if not pos.strip():
            return ''

        for r, _, _, name in (SLICE_REGEX, SSLICE_REGEX, PSLICE_REGEX,
                              TRANSECT_REGEX, POSITION_REGEX, XY_REGEX):
            if r.match(pos):
                self.debug('matched {} to {}'.format(name, pos))
                return pos
        else:
            for po in pos.split(','):
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
        return 'Edit' if self._use_pattern() else 'New'

    def _get_edit_template_label(self):
        return 'Edit' if self._use_template() else 'New'

    def _get_patterns(self):
        return ['Pattern', LINE_STR] + self.remote_patterns
        # p = paths.pattern_dir
        # extension = '.lp'
        # patterns = list_directory(p, extension)
        # return ['Pattern', 'None', LINE_STR, 'Remote Patterns'] + self.remote_patterns + \
        #        [LINE_STR, 'Local Patterns'] + patterns

    def _get_templates(self):
        p = paths.incremental_heat_template_dir
        extension = '.txt'
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
            self.template = 'Step Heat Template'

        return ['Step Heat Template', LINE_STR] + temps

    def _filter_templates(self, temps):
        """
        filter templates based on user counts
        :return:
        """
        p = os.path.join(paths.hidden_dir, 'iht_counts.{}'.format(self.username))
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
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
        extension = '.yaml'
        temps = list_directory(p, extension, remove_extension=True)
        self.debug('loading conditionals from {}'.format(p))

        return [NULL_STR] + temps

    def _get_beam_diameter(self):
        bd = ''
        if self._beam_diameter is not None:
            bd = self._beam_diameter
        return bd

    def _set_beam_diameter(self, v):
        try:
            self._beam_diameter = float(v)
            self._update_run_values('beam_diameter', self._beam_diameter)
        except (ValueError, TypeError):
            pass

    def _get_conditionals_str(self):
        r = ''
        if self.conditionals_path != NULL_STR:
            r = os.path.basename(self.conditionals_path)
        elif self.use_simple_truncation and self.trunc_attr is not None and self.trunc_comp is not None \
                and self.trunc_crit is not None:
            r = '{}{}{}, {}'.format(self.trunc_attr, self.trunc_comp,
                                    self.trunc_crit, self.trunc_start)
        return r
        # elif self.truncation_path:
        #     return os.path.basename(self.truncation_path)

    @cached_property
    def _get_flux(self):
        return self._get_flux_from_datastore()

    @cached_property
    def _get_flux_error(self):
        return self._get_flux_from_datastore(attr='err')

    def _get_flux_from_datastore(self, attr='j'):
        j = 0

        identifier = self.labnumber
        if not (self.suppress_meta or '-##-' in identifier):
            if identifier and self.irrad_hole:
                j = self.dvc.get_flux(self.selected_irradiation, self.selected_level, int(self.irrad_hole)) or 0
                if attr == 'err':
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
        if not temp:
            from pychron.experiment.utilities.comment_template import CommentTemplater

            temp = CommentTemplater()

        c = temp.render(self)
        self.debug('Comment template rendered = {}'.format(c))
        self.comment = c

    def _set_conditionals(self, t):
        for s in self._selected_runs:
            s.conditionals = t

        self.changed = True
        self.refresh_table_needed = True

    def _update_script_lists(self):
        self.debug('update script lists')
        for si in SCRIPT_NAMES:
            si = getattr(self, si)
            si.refresh_lists = True

    def _iter_scripts(self):
        return (getattr(self, s) for s in SCRIPT_NAMES)

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _extract_value_changed(self, new):
        if new:
            if self.extract_units == NULL_STR:
                self.extract_units = self._default_extract_units

    def _set_repository_identifier_button_fired(self):
        self.debug('set repository identifier={}'.format(self.repository_identifier))
        if self._selected_runs:
            for si in self._selected_runs:
                si.repository_identifier = self.repository_identifier
            self.refresh_table_needed = True

    def _add_repository_identifier_fired(self):
        if self.dvc:
            a = RepositoryIdentifierEntry(dvc=self.dvc)
            a.available = self.dvc.get_repository_identifiers()
            a.principal_investigators = self.dvc.get_principal_investigator_names()
            if a.do():
                self.repository_identifier_dirty = True
                self.repository_identifier = a.name
                return True
        else:
            self.warning_dialog('DVC Plugin not enabled')

    @on_trait_change('use_name_prefix, name_prefix')
    def _handle_prefix(self, name, new):
        for si in self._iter_scripts():
            setattr(si, name, new)

    def _edit_run_blocks(self):
        from pychron.experiment.queue.run_block import RunBlockEditView

        rbev = RunBlockEditView()
        rbev.edit_traits()

    def _edit_frequency_button_fired(self):
        from pychron.experiment.utilities.frequency_edit_view import FrequencyEditView

        fev = FrequencyEditView(model=self.frequency_model)
        fev.edit_traits(kind='modal')

    def _edit_comment_template_fired(self):
        from pychron.experiment.utilities.comment_template import CommentTemplater
        from pychron.experiment.utilities.template_view import CommentTemplateView

        ct = CommentTemplater()

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

    @on_trait_change('[measurement_script, post_measurement_script, '
                     'post_equilibration_script, extraction_script]:edit_event')
    def _handle_edit_script(self, new):
        self._auto_save()

        app = self.application
        task = app.open_task('pychron.pyscript.task')
        path, kind = new
        task.kind = kind
        task.open(path=path)
        task.set_on_save_as_handler(self._update_script_lists)
        task.set_on_close_handler(self._update_script_lists)

    def _load_defaults_button_fired(self):
        if self.labnumber:
            self._load_default_scripts(self.labnumber)

    def _default_fits_button_fired(self):
        from pychron.experiment.automated_run.measurement_fits_selector import MeasurementFitsSelector, \
            MeasurementFitsSelectorView
        from pychron.pyscripts.tasks.pyscript_editor import PyScriptEdit
        from pychron.pyscripts.context_editors.measurement_context_editor import MeasurementContextEditor

        m = MeasurementFitsSelector()
        sp = self.measurement_script.script_path()
        m.open(sp)
        f = MeasurementFitsSelectorView(model=m)
        info = f.edit_traits(kind='livemodal')
        if info.result:
            # update the default_fits entry in the docstr
            ed = PyScriptEdit()
            ed.context_editor = MeasurementContextEditor()
            ed.open_script(sp)
            ed.context_editor.default_fits = str(m.name)
            ed.update_docstr()

    def _new_conditionals_button_fired(self):
        name = edit_conditionals(self.conditionals_path,
                                 app=self.application, root=paths.conditionals_dir,
                                 save_as=True,
                                 title='Edit Run Conditionals',
                                 kinds=('actions', 'cancelations', 'terminations', 'truncations'))
        if name:
            self.load_conditionals()
            self.conditionals_path = os.path.splitext(name)[0]

    def _edit_conditionals_button_fired(self):
        edit_conditionals(self.conditionals_path,
                          app=self.application, root=paths.conditionals_dir,
                          title='Edit Run Conditionals',
                          kinds=('actions', 'cancelations', 'terminations', 'truncations'))
        self.load_conditionals()

    @on_trait_change('trunc_+, conditionals_path')
    def _handle_conditionals(self, obj, name, old, new):
        if self.edit_mode and \
                self._selected_runs and \
                not self.suppress_update:
            # if name == 'truncation_path':
            #     t = new
            # t = add_extension(new, '.yaml') if new else None
            # else:
            self._auto_save()
            t = self.conditionals_str
            self._set_conditionals(t)

    @on_trait_change('''cleanup, duration, extract_value,ramp_duration,
collection_time_zero_offset,
use_cdd_warming,
extract_units,
pattern,
position,
weight, comment, skip, overlap, repository_identifier''')
    def _edit_handler(self, name, new):
        # self._auto_save()

        if name == 'pattern':
            if not self._use_pattern():
                new = ''
                # print name, new, self._use_pattern()
        self._update_run_values(name, new)

    @on_trait_change('''measurement_script:name, 
extraction_script:name, 
post_measurement_script:name,
post_equilibration_script:name''')
    def _edit_script_handler(self, obj, name, new):
        self.debug('name={}, new={}, suppress={}'.format(obj.label, new, self.suppress_update))
        if obj.label == 'Measurement':
            self.default_fits_enabled = bool(new and new not in (NULL_STR,))

        if self.edit_mode and not self.suppress_update:
            self._auto_save()
            if obj.label == 'Extraction':
                self._load_extraction_info(obj)
            if self._selected_runs:
                for si in self._selected_runs:
                    name = '{}_script'.format(obj.label.lower().replace(' ', '_'))
                    setattr(si, name, new)
                self.refresh()

    @on_trait_change('script_options:name')
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
        self.debug('labnumber changed old:{}, new:{}'.format(old, new))
        if new:
            special = False
            try:
                _ = int(new)
            except ValueError:
                special = True

            if not special:
                sname = 'Special Labnumber'
            else:
                tag = new.split('-')[0]
                sname = ANALYSIS_MAPPING.get(tag, 'Special Labnumber')

            self._suppress_special_labnumber_change = True
            self.special_labnumber = sname
            self._suppress_special_labnumber_change = False

            if self._load_labnumber_meta(new):
                if self._set_defaults:
                    self._load_labnumber_defaults(old, new, special)
        else:
            self.sample = ''

    def _project_changed(self):
        self._clear_labnumber()

    def _selected_irradiation_changed(self):
        self._clear_labnumber()
        self.selected_level = 'Level'

    def _selected_level_changed(self):
        self._clear_labnumber()

    def _special_labnumber_changed(self):
        if self._suppress_special_labnumber_change:
            return

        if self.special_labnumber not in ('Special Labnumber', LINE_STR, ''):
            ln = convert_special_name(self.special_labnumber)
            self.debug('special ln changed {}, {}'.format(self.special_labnumber, ln))
            if ln:
                if ln not in ('dg', 'pa'):
                    msname = self.mass_spectrometer[0].capitalize()

                    if ln in SPECIAL_KEYS and not ln.startswith('bu'):
                        ln = make_standard_identifier(ln, '##', msname)
                    else:
                        edname = ''
                        ed = self.extract_device
                        if ed not in ('Extract Device', LINE_STR):
                            edname = ''.join(map(lambda x: x[0].capitalize(), ed.split(' ')))
                        ln = make_special_identifier(ln, edname, msname)

                self.labnumber = ln

            self._frequency_enabled = True

            if not self._selected_runs:
                self.edit_mode = True
        else:
            self.debug('special labnumber changed else')
            self.labnumber = ''
            self._frequency_enabled = False

    def _auto_fill_comment_changed(self):
        if self.auto_fill_comment:
            self._set_auto_comment()
        else:
            self.comment = ''

    def _edit_template_fired(self):
        temp = self._new_template()
        temp.names = list_directory(paths.incremental_heat_template_dir, extension='.txt')
        temp.on_trait_change(self._template_closed, 'close_event')
        open_view(temp)
        # self.open_view(temp)

    def _edit_pattern_fired(self):
        pat = self._new_pattern()
        pat.on_trait_change(self._pattern_closed, 'close_event')
        open_view(pat)
        # self.open_view(pat)

    def _edit_mode_button_fired(self):
        self.edit_mode = not self.edit_mode

    def _clear_conditionals_fired(self):
        if self.edit_mode and \
                self._selected_runs and \
                not self.suppress_update:
            self._set_conditionals('')

    def _aliquot_changed(self):
        # print 'aliquot chhanged {} {}'.format(self.aliquot, self.suppress_update)
        if self.suppress_update:
            return

        if self.edit_mode:
            a = int(self.aliquot)
            for si in self._selected_runs:
                # a = 0
                # if si.aliquot != self.aliquot:
                si.user_defined_aliquot = a

            # self.update_info_needed = True
            self.refresh_table_needed = True
            self.changed = True

    def _save_flux_button_fired(self):
        self._save_flux()

    def _edit_mode_changed(self):
        self.suppress_update = True
        self.aliquot = 0
        self.suppress_update = False

    # @on_trait_change('mass_spectrometer, can_edit')
    # def _update_value(self, name, new):
    #     for si in SCRIPT_NAMES:
    #         script = getattr(self, si)
    #         setattr(script, name, new)

    # ===============================================================================
    # defaults
    # ================================================================================
    def _script_factory(self, label, name=NULL_STR, kind='ExtractionLine'):
        s = Script(label=label,
                   use_name_prefix=self.use_name_prefix,
                   name_prefix=self.name_prefix,
                   mass_spectrometer=self.mass_spectrometer,
                   name=name,
                   kind=kind)
        return s
        # if self.use_name_prefix:
        #     if self.name_prefix:
        #         prefix = self.name_prefix
        #     else:
        #         prefix = self.mass_spectrometer

        # return Script(label=label,
        #               name_prefix = prefix,
        #               # mass_spectrometer=self.mass_spectrometer,
        #               kind=kind)

    def _extraction_script_default(self):
        return self._script_factory('Extraction', 'extraction')

    def _measurement_script_default(self):
        return self._script_factory('Measurement', 'measurement', kind='Measurement')

    def _post_measurement_script_default(self):
        return self._script_factory('Post Measurement', 'post_measurement')

    def _post_equilibration_script_default(self):
        return self._script_factory('Post Equilibration', 'post_equilibration')

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
        dh.mainstore = self.application.get_service('pychron.dvc.dvc.DVC')
        dh.bind_preferences()
        return dh

    @property
    def run_block_enabled(self):
        return self.run_block not in ('RunBlock', LINE_STR)

    @property
    def persistence_path(self):
        return os.path.join(paths.hidden_dir, 'run_factory')

        # ============= EOF =============================================
        # def _labnumber_changed(self, old, labnumber):
        # def _load_labnumber_defaults(self, old, labnumber):
        #     # self.debug('old={}, new={}. {}'.format(old, labnumber, not labnumber or labnumber == NULL_STR))
        #     self.debug('load labnumber defaults L#={}'.format(labnumber))
        #     if not labnumber or labnumber == NULL_STR:
        #         return
        #
        #     db = self.db
        #     if not db:
        #         return
        #     # self.update_labnumber = labnumber
        #
        #     special = False
        #     try:
        #         _ = int(labnumber)
        #     except ValueError:
        #         special = True
        #
        #     # if labnumber has a place holder load default script and return
        #     if '##' in labnumber:
        #         self._load_scripts(old, labnumber)
        #         return
        #
        #     self.irradiation = ''
        #     self.sample = ''
        #
        #     self._aliquot = 0
        #     if labnumber:
        #         with db.session_ctx():
        #             # convert labnumber (a, bg, or 10034 etc)
        #             ln = db.get_labnumber(labnumber)
        #             if ln:
        #                 # set sample and irrad info
        #                 try:
        #                     self.sample = ln.sample.name
        #                 except AttributeError:
        #                     pass
        #
        #                 try:
        #                     a = int(ln.analyses[-1].aliquot + 1)
        #                 except IndexError, e:
        #                     a = 1
        #
        #                 self._aliquot = a
        #
        #                 self.irradiation = self._make_irrad_level(ln)
        #
        #                 if self.auto_fill_comment:
        #                     self._set_auto_comment()
        #
        #                 self._load_scripts(old, labnumber)
        #                 self._load_defaults(labnumber if special else 'u')
        #             elif special:
        #                 ln = labnumber[:2]
        #                 if ln == 'dg':
        #                     # self._load_extraction_defaults(ln)
        #                     self._load_defaults(ln, attrs=('extract_value', 'extract_units'))
        #
        #                 if not (ln in ('pa', 'dg')):
        #                     '''
        #                         don't add pause or degas to database
        #                     '''
        #                     if self.confirmation_dialog(
        #                             'Lab Identifer {} does not exist. Would you like to add it?'.format(labnumber)):
        #                         db.add_labnumber(labnumber)
        #                         self._aliquot = 1
        #                         self._load_scripts(old, labnumber)
        #                     else:
        #                         self.labnumber = ''
        #                 else:
        #                     self._load_scripts(old, labnumber)
        #             else:
        #                 self.warning_dialog(
        #                     '{} does not exist. Add using "Labnumber Entry" or "Utilities>>Import"'.format(labnumber))

#
# def _generate_positions(pos):
# s = None
# e = None
# #(SLICE_REGEX, SSLICE_REGEX, PSLICE_REGEX,
# #          TRANSECT_REGEX, POSITION_REGEX)
#
# if SLICE_REGEX.match(pos):
# s, e = map(int, pos.split('-'))
# elif SSLICE_REGEX.match(pos):
# s, e, inc = map(int, pos.split(':'))
# elif PSLICE_REGEX.match(pos):
# s, e = map(int, pos.split(':'))[:2]
# elif CSLICE_REGEX.match(pos):
# args = pos.split(';')
# positions = []
#            for ai in args:
#                if '-' in ai:
#                    a, b = map(int, ai.split('-'))
#                    inc = 1 if a < b else -1
#                    positions.extend(range(a, b + inc, inc))
#                else:
#                    positions.append(ai)
#
#        elif TRANSECT_REGEX.match(pos):
#            positions = [pos]
#        #else:
#        #    try:
#        #        s = int(self.position)
#        #        e = s
#        #    except ValueError:
#        #        pass
#        #if e < s:
#        #    self.warning_dialog('Endposition {} must greater than start position {}'.format(e, s))
#        #    return
#
#        set_pos = True
#        if s is not None and e is not None:
#
#            inc = 1 if s < e else -1
#            positions = range(s, e + inc, inc)
#            #else:
#        #    if TRANSECT_REGEX.match(pos):
#        #        positions = [pos]
#        #    else:
#        #        set_pos = False
#        #        positions = [0]
#        return positions, set_pos
