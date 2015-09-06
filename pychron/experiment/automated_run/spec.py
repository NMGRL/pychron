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
from traits.api import Str, Int, Bool, Float, Property, \
    Enum, on_trait_change, CStr, Long, HasTraits
# ============= standard library imports ========================
import hashlib
from datetime import datetime
import uuid
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import remove_extension
from pychron.core.helpers.logger_setup import new_logger
from pychron.experiment.utilities.identifier import get_analysis_type, make_rid, make_runid, is_special, \
    convert_extract_device
from pychron.experiment.utilities.position_regex import XY_REGEX
from pychron.pychron_constants import SCRIPT_KEYS, SCRIPT_NAMES, ALPHAS


logger = new_logger('AutomatedRunSpec')


class AutomatedRunSpec(HasTraits):
    """
        this class is used to as a simple container and factory for
        an AutomatedRun. the AutomatedRun does the actual work. ie extraction and measurement
    """
    state = Enum('not run', 'extraction',
                 'measurement', 'success',
                 'failed', 'truncated', 'canceled',
                 'invalid', 'test')

    skip = Bool(False)
    end_after = Bool(False)
    collection_version = Str
    # ===========================================================================
    # queue globals
    # ===========================================================================
    mass_spectrometer = Str
    extract_device = Str
    username = Str
    tray = Str
    queue_conditionals_name = Str
    # ===========================================================================
    # run id
    # ===========================================================================
    labnumber = Str
    uuid = Str
    aliquot = Property
    _aliquot = Int
    # assigned_aliquot = Int

    user_defined_aliquot = Int

    step = Property(depends_on='_step')
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

    duration = Float
    cleanup = Float
    pattern = Str
    beam_diameter = CStr
    ramp_duration = Float
    ramp_rate = Float
    disable_between_positions = Bool(False)
    overlap = Property
    _overlap = Int
    _min_ms_pumptime = Int
    conditionals = Str
    syn_extraction = Str

    collection_time_zero_offset = Float

    # ===========================================================================
    # info
    # ===========================================================================
    weight = Float
    comment = Str

    # ===========================================================================
    # display only
    # ===========================================================================
    project = Str
    sample = Str
    irradiation = Str
    irradiation_level = Str
    irradiation_position = Int
    material = Str
    data_reduction_tag = ''

    analysis_type = Property(depends_on='labnumber')
    run_klass = 'pychron.experiment.automated_run.automated_run.AutomatedRun'

    identifier_error = Bool(False)
    _executable = Bool(True)
    executable = Property(depends_on='identifier_error, _executable')

    frequency_group = 0

    runid = Property
    _estimated_duration = 0
    _changed = False

    rundate = Property
    _step_heat = False
    conflicts_checked = False

    experiment_identifier = Str
    identifier = Property

    def is_detector_ic(self):
        return self.analysis_type == 'detector_ic'

    def is_step_heat(self):
        return bool(self.user_defined_aliquot) and not self.is_special()

    def is_special(self):
        return is_special(self.labnumber)

    def to_string(self):
        attrs = ['labnumber', 'aliquot', 'step',
                 'extract_value', 'extract_units', 'ramp_duration',
                 'position', 'duration', 'cleanup', 'beam_diameter',
                 'mass_spectrometer', 'extract_device',
                 'extraction_script', 'measurement_script',
                 'post_equilibration_script', 'post_measurement_script']
        return ','.join(map(str, self.to_string_attrs(attrs)))

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
                    logger.debug('{} in script context. using previous estimated duration'.format(name))
                    warned.append(name)

                script, ok = script_context[name]
                if ok and duration:
                    if si in ('measurement_script', 'extraction_script'):
                        # ctx = dict(duration=self.duration,
                        # cleanup=self.cleanup,
                        #            analysis_type=self.analysis_type,
                        #            position=self.position)
                        # arun.setup_context(script)
                        ctx = self.make_script_context()
                        d = script.calculate_estimated_duration(ctx)
                        s += d
                script_oks.append(ok)
            else:
                if arun is None:
                    arun = self.make_run(new_uuid=False)

                # arun.invalid_script = False
                script = getattr(arun, si)
                if script is not None:
                    # if duration:
                    # arun.setup_context(script)

                    ok = script.syntax_ok()
                    script_oks.append(ok)
                    script_context[name] = script, ok
                    if ok and duration:
                        if si in ('measurement_script', 'extraction_script'):
                            ctx = self.make_script_context()
                            d = script.calculate_estimated_duration(ctx)
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
        elif ',' in pos:
            # interpert as list of holenumbers
            ps = list(pos.split(','))
        else:
            ps = [pos]

        return ps

    def make_script_context(self):
        hdn = convert_extract_device(self.extract_device)
        # hdn = self.extract_device.replace(' ','')

        an = self.analysis_type.split('_')[0]
        ctx = dict(tray=self.tray,
                   position=self.get_position_list(),
                   disable_between_positions=self.disable_between_positions,
                   duration=self.duration,
                   extract_value=self.extract_value,
                   extract_units=self.extract_units,
                   cleanup=self.cleanup,
                   extract_device=hdn,
                   analysis_type=an,
                   ramp_rate=self.ramp_rate,
                   pattern=self.pattern,
                   beam_diameter=self.beam_diameter,
                   ramp_duration=self.ramp_duration)
        return ctx

    def get_estimated_duration(self, script_context=None, warned=None, force=False):
        """
            use the pyscripts to calculate etd

            script_context is a dictionary of already loaded scripts

            this is a good point to set executable as well
        """
        if not self._estimated_duration or self._changed or force:
            s = self.test_scripts(script_context, warned)

            db_save_time = 1
            self._estimated_duration = s + db_save_time

        self._changed = False
        logger.debug('Run total estimated duration= {:0.3f}'.format(self._estimated_duration))
        return self._estimated_duration

    def make_run(self, new_uuid=True, run=None):
        if run is None:
            args = self.run_klass.split('.')
            md, klass = '.'.join(args[:-1]), args[-1]

            md = __import__(md, fromlist=[klass])
            run = getattr(md, klass)()

        for si in SCRIPT_KEYS:
            setattr(run.script_info, '{}_script_name'.format(si),
                    getattr(self, '{}_script'.format(si)))

        if new_uuid:
            run.uuid = u = str(uuid.uuid4())
            self.uuid = u
            # self._step_heat = bool(self.aliquot)
            # print self._step_heat, bool(self.aliquot), self.aliquot

        # run.spec = weakref.ref(self)()
        run.spec = self

        return run

    def load(self, script_info, params):
        for k, v in script_info.iteritems():
            k = k if k == 'script_options' else '{}_script'.format(k)
            setattr(self, k, v)

        for k, v in params.iteritems():
            # print 'load', hasattr(self, k), k, v
            if hasattr(self, k):
                setattr(self, k, v)

        self._changed = False

    # def _remove_mass_spectrometer_name(self, name):
    #     if self.mass_spectrometer:
    #         name = name.replace('{}_'.format(self.mass_spectrometer.lower()), '')
    #     return name

    def to_string_attrs(self, attrs):
        def get_attr(attrname):
            if attrname == 'labnumber':
                if self.user_defined_aliquot and not self.is_special():
                    v = make_rid(self.labnumber, self.aliquot)
                else:
                    v = self.labnumber
            elif attrname.endswith('script'):
                # remove mass spectrometer name
                v = getattr(self, attrname)
                # v = self._remove_mass_spectrometer_name(v)
                v = remove_extension(v)

            elif attrname == 'overlap':
                o, m = self.overlap
                if m:
                    v = '{},{}'.format(*self.overlap)
                else:
                    v = o
            else:
                try:
                    v = getattr(self, attrname)
                except AttributeError, e:
                    v = ''

            return v

        return [get_attr(ai) for ai in attrs]

    # def _get_run_attrs(self):
    #     return ('labnumber', 'aliquot', 'step',
    #             'extract_value', 'extract_units', 'ramp_duration',
    #             'position', 'duration', 'cleanup', 'collection_time_zero_offset',
    #             'pattern',
    #             'beam_diameter',
    #             'truncate_condition',
    #             'syn_extraction',
    #             'mass_spectrometer', 'extract_device',
    #             'analysis_type',
    #             'sample', 'irradiation', 'username', 'comment', 'skip', 'end_after')

    # ===============================================================================
    # handlers
    # ===============================================================================
    #     @on_trait_change('automated_run:state')
    #     def _update_state(self, new):
    #         self.state = new

    #     def _update_aliquot(self, new):
    #         print 'upda', new
    #         self.aliquot = new

    @on_trait_change('''measurment_script, post_measurment_script,
    post_equilibration_script, extraction_script, script_options''')
    def _script_changed(self, name, new):
        if new == 'None':
            #            self.trait_set(trait_change_notify=False, **{name: ''})
            self.trait_set(**{name: ''})
        else:
            self._changed = True

    @on_trait_change('''extract_+, position, duration, cleanup ''')
    def _extract_changed(self):
        self._changed = True

    # ===============================================================================
    # property get/set
    # ===============================================================================
    #    def _get_state(self):
    #        return self._state
    #
    #    def _set_state(self, s):
    #        if self._state != 'truncate':
    #            self._state = s
    def _set_aliquot(self, v):
        self._aliquot = v

    def _get_aliquot(self):
        if self.is_special():
            return self._aliquot
        else:
            if self.user_defined_aliquot:
                return self.user_defined_aliquot
        return self._aliquot

    def _get_analysis_type(self):
        return get_analysis_type(self.labnumber)

    def reset(self):
        self.clear_step()
        self.conflicts_checked = False

    def clear_step(self):
        self._step = -1

    def _set_step(self, v):
        if isinstance(v, str):
            v = v.upper()
            if v in ALPHAS:
                self._step = ALPHAS.index(v)
        else:
            self._step = v

    def _get_step(self):
        if self._step < 0:
            return ''
        else:
            return ALPHAS[self._step]

    def _get_runid(self):
        return make_runid(self.labnumber, self.aliquot, self.step)

    def _get_rundate(self):
        return datetime.now()

    def _set_executable(self, v):
        self._executable = v

    def _get_executable(self):
        return self._executable and not self.identifier_error

    def _set_overlap(self, v):
        if isinstance(v, (list, tuple)):
            args = v
        else:
            try:
                args = map(int, v.split(','))
            except ValueError:
                logger.debug('Invalid overlap string "{}". Should be of the form "10,60" or "10" '.format(v))

        if len(args) == 1:
            self._overlap = args[0]
        elif len(args) == 2:
            self._overlap, self._min_ms_pumptime = args

    def _get_overlap(self):
        return self._overlap, self._min_ms_pumptime

    # mirror labnumber for now. deprecate labnumber and replace with identifier
    def _get_identifier(self):
        return self.labnumber

    def _set_identifier(self, v):
        self.labnumber = v

    @property
    def display_irradiation(self):
        ret = ''
        if self.irradiation:
            ret = '{} {}:{}'.format(self.irradiation, self.irradiation_level, self.irradiation_position)
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
    def extract_duration(self):
        return self.duration

    @property
    def cleanup_duration(self):
        return self.cleanup

    @cleanup_duration.setter
    def set_cleanup(self, v):
        self.cleanup = v

    @extract_duration.setter
    def set_duration(self, v):
        self.duration = v

    @property
    def script_hash(self):
        ctx = dict(nposition=len(self.get_position_list()),
                   disable_between_positions=self.disable_between_positions,
                   duration=self.duration,
                   extract_value=self.extract_value,
                   extract_units=self.extract_units,
                   cleanup=self.cleanup,
                   ramp_rate=self.ramp_rate,
                   pattern=self.pattern,
                   ramp_duration=self.ramp_duration)

        ctx['measurement'] = self.measurement_script
        ctx['extraction'] = self.extraction_script

        md5 = hashlib.md5()
        for k, v in sorted(ctx.items()):
            md5.update(str(k))
            md5.update(str(v))
        return md5.hexdigest()

# ============= EOF =============================================
