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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, Str, Property, Event, Bool, String, List, CInt
#============= standard library imports ========================
import yaml
import os
import datetime
#============= local library imports  ==========================
from pychron.experiment.queue.run_block import RunBlock
from pychron.experiment.utilities.frequency_generator import frequency_index_gen
from pychron.pychron_constants import NULL_STR, LINE_STR
from pychron.experiment.stats import ExperimentStats
from pychron.paths import paths
from pychron.core.helpers.ctx_managers import no_update


def extract_meta(line_gen):
    metastr = ''
    # read until break
    for line in line_gen:
        if line.startswith('#====='):
            break
        metastr += '{}\n'.format(line)

    return yaml.load(metastr), metastr


__METASTR__ = '''
username: {}
email: {}
uss_group_email: {}
date: {}
queue_conditionals_name: {}
mass_spectrometer: {}
delay_before_analyses: {}
delay_between_analyses: {}
extract_device: {}
tray: {}
load: {}
'''


class BaseExperimentQueue(RunBlock):
    selected = List

    automated_runs = List
    cleaned_automated_runs = Property(depends_on='automated_runs[]')

    username = String
    email = String
    use_group_email = Bool

    tray = Str
    delay_before_analyses = CInt(5)
    delay_between_analyses = CInt(30)

    queue_conditionals_name = Str

    stats = Instance(ExperimentStats, ())

    update_needed = Event
    refresh_table_needed = Event
    refresh_info_needed = Event
    changed = Event
    name = Property(depends_on='path')
    path = String

    executable = Bool
    initialized = True

    load_name = Str

    _no_update = False
    _frequency_group_counter = 0

    #===============================================================================
    # persistence
    #===============================================================================
    def load(self, txt):
        self.initialized = False
        self.stats.delay_between_analyses = self.delay_between_analyses
        self.stats.delay_before_analyses = self.delay_before_analyses

        line_gen = self._get_line_generator(txt)
        self._extract_meta(line_gen)
        aruns = self._load_runs(line_gen)
        if aruns is not None:
            # set frequency_added_counter
            if aruns:
                self._frequency_group_counter = max([ri.frequency_group for ri in aruns])

            with no_update(self):
                self.automated_runs = aruns
            self.initialized = True
            self.debug('loading queue successful')
            return True

    def dump(self, stream, runs=None, include_meta=True):
        header, attrs = self._get_dump_attrs()
        writeline = lambda m: stream.write(m + '\n')
        if include_meta:
            # write metadata
            self._meta_dumper(stream)
            writeline('#' + '=' * 80)

        def tab(l, comment=False):
            s = '\t'.join(map(str, l))
            if comment:
                s = '#{}'.format(s)
            writeline(s)

        tab(header)

        def is_not_null(vi):
            if vi and vi != NULL_STR:
                try:
                    vi = float(vi)
                    return abs(vi) > 1e-15
                except (ValueError, TypeError):
                    return True
            else:
                return False

        if runs is None:
            runs = self.automated_runs

        for arun in runs:
            vs = arun.to_string_attrs(attrs)
            vals = [v if is_not_null(v) else '' for v in vs]
            tab(vals, comment=arun.skip)

        return stream

    def set_extract_device(self, v):
        self.extract_device = v

    def is_updateable(self):
        return not self._no_update

    def clear_frequency_runs(self):
        if self._frequency_group_counter:
            self.automated_runs = [ri for ri in self.automated_runs
                                   if not ri.frequency_group == self._frequency_group_counter]
            self._frequency_group_counter -= 1

    def add_runs(self, runspecs, freq=None, freq_before=True, freq_after=False,
                 is_run_block=False, is_repeat_block=False):
        """
            runspecs: list of runs
            freq: optional inter
            freq_before_or_after: if true add before else add after
        """
        if not runspecs:
            return []

        with no_update(self):
            if freq:
                runs = self._add_frequency_runs(runspecs, freq,
                                                freq_before, freq_after,
                                                is_run_block, is_repeat_block)
            else:
                runs = self._add_runs(runspecs)

            return runs

    def _add_frequency_runs(self, runspecs, freq,
                            freq_before, freq_after,
                            is_run_block, is_repeat_block):

        aruns = self.automated_runs
        runblock = self.automated_runs
        if is_repeat_block:
            idx = aruns.index(self.selected[-1])
            sidx = idx + freq
        else:
            if len(self.selected) > 1:
                runblock = self.selected
                sidx = aruns.index(runblock[0])
            else:
                sidx = 0

        self._frequency_group_counter += 1
        fcnt = self._frequency_group_counter

        runs = []
        if is_run_block:
            incrementable_types = ('unknown',)
        else:
            run = runspecs[0]
            rtype = run.analysis_type
            incrementable_types = ('unknown',)
            if rtype.startswith('blank'):
                incrementable_types = ('unknown', 'air', 'cocktail')
            elif rtype.startswith('air') or rtype.startswith('cocktail'):
                incrementable_types = ('unknown',)

        for idx in reversed(list(frequency_index_gen(runblock, freq, incrementable_types,
                                                     freq_before, freq_after, sidx=sidx))):
            for ri in reversed(runspecs):
                run = ri.clone_traits()
                run.frequency_group = fcnt
                runs.append(run)
                aruns.insert(idx, run)

        return runs

    def _add_runs(self, runspecs):
        aruns = self.automated_runs
        if self.selected:
            idx = aruns.index(self.selected[-1])
            for ri in reversed(runspecs):
                aruns.insert(idx + 1, ri)
        else:
            aruns.extend(runspecs)
        return runspecs

    def _add_queue_meta(self, params):
        for attr in ('extract_device', 'tray', 'username', 'email',
                     'use_group_email', 'queue_conditionals_name'):
            params[attr] = getattr(self, attr)

            # params['extract_device'] = self.extract_device
            # params['tray'] = self.tray
            # params['username'] = self.username
            # params['email'] = self.email
            # params['use_group_email']
            # params['queue_conditionals_name'] = self.queue_conditionals_name

    def _extract_meta(self, f):
        meta, metastr = extract_meta(f)

        if meta is None:
            self.warning_dialog('Invalid experiment set file. Poorly formatted metadata {}'.format(metastr))
            return
        self._load_meta(meta)
        return meta

    def _load_meta(self, meta):
        # load sample map
        self._load_map(meta)

        #default = lambda x: str(x) if x else ' '
        default_int = lambda x: x if x is not None else 1
        key_default = lambda k: lambda x: str(x) if x else k
        bool_default = lambda x: bool(x) if x else False
        default = key_default('')

        self._set_meta_param('tray', meta, default)
        self._set_meta_param('extract_device', meta, key_default('Extract Device'))
        self._set_meta_param('mass_spectrometer', meta, key_default('Spectrometer'))
        self._set_meta_param('delay_between_analyses', meta, default_int)
        self._set_meta_param('delay_before_analyses', meta, default_int)
        self._set_meta_param('username', meta, default)
        self._set_meta_param('email', meta, default)
        self._set_meta_param('use_group_email', meta, bool_default)
        self._set_meta_param('load_name', meta, default, metaname='load')
        self._set_meta_param('queue_conditionals_name', meta, default)

    def _load_map(self, meta):
        from pychron.lasers.stage_managers.stage_map import StageMap
        from pychron.experiment.map_view import MapView

        def create_map(name):
            if name:
                if not name.endswith('.txt'):
                    name = '{}.txt'.format(name)
                name = os.path.join(paths.map_dir, name)

                if os.path.isfile(name):
                    sm = StageMap(file_path=name)
                    mv = MapView(stage_map=sm)
                    return mv

        self._set_meta_param('sample_map', meta, create_map, metaname='tray')

    def _set_meta_param(self, attr, meta, func, metaname=None):
        if metaname is None:
            metaname = attr

        v = None
        try:
            v = meta[metaname]
        except KeyError:
            pass
        v = func(v)

        self.debug('setting {} to {}'.format(attr, v))
        setattr(self, attr, v)

    def _get_dump_attrs(self):
        seq = ['labnumber', 'sample', 'position',
               ('e_value', 'extract_value'),
               ('e_units', 'extract_units'),
               'duration', 'cleanup', 'overlap',
               ('beam_diam', 'beam_diameter'),
               'pattern',
               ('extraction', 'extraction_script'),
               ('ramp', 'ramp_duration'),
               ('t_o', 'collection_time_zero_offset'),
               ('measurement', 'measurement_script'),
               ('conditionals', 'conditionals'),
               'syn_extraction',
               'use_cdd_warming',
               ('post_meas', 'post_measurement_script'),
               ('post_eq', 'post_equilibration_script'),
               ('s_opt', 'script_options'),
               ('dis_btw_pos', 'disable_between_positons'),
               'weight', 'comment',
               'autocenter', 'frequency_group']

        if self.extract_device == 'Fusions UV':
            # header.extend(('reprate', 'mask', 'attenuator', 'image'))
            # attrs.extend(('reprate', 'mask', 'attenuator', 'image'))
            seq.extend(('reprate', 'mask', 'attenuator', 'image'))

        seq = [(v, v) if not isinstance(v, tuple) else v for v in seq]
        header, attrs = zip(*seq)
        return header, attrs

    def _meta_dumper(self, fp):
        ms = self.mass_spectrometer
        if ms in ('Spectrometer', LINE_STR):
            ms = ''

        s = __METASTR__.format(
            self.username,
            self.email,
            self.use_group_email,
            datetime.datetime.today(),
            self.queue_conditionals_name,
            ms,
            self.delay_before_analyses,
            self.delay_between_analyses,
            self.extract_device,
            self.tray or '',
            self.load_name or '')

        if fp:
            fp.write(s)
        else:
            return s

    #===============================================================================
    # handlers
    #===============================================================================
    def _delay_between_analyses_changed(self, new):
        self.stats.delay_between_analyses = new

    def _delay_before_analyses_changed(self, new):
        self.stats.delay_before_analyses = new

    def _mass_spectrometer_changed(self):
        ms = self.mass_spectrometer
        for ai in self.automated_runs:
            ai.mass_spectrometer = ms

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_cleaned_automated_runs(self):
        return [ci for ci in self.automated_runs
                if not ci.skip and ci.state == 'not run']

    def _get_name(self):
        if self.path:
            return os.path.splitext(os.path.basename(self.path))[0]
        else:
            return ''


#============= EOF =============================================
