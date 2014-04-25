#===============================================================================
# Copyright 2012 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, Str, Property, Event, Bool, String, List, CInt
#============= standard library imports ========================
import yaml
import os
import datetime
#============= local library imports  ==========================
from pychron.pychron_constants import NULL_STR, LINE_STR
from pychron.experiment.automated_run.uv.spec import UVAutomatedRunSpec
from pychron.experiment.stats import ExperimentStats
from pychron.paths import paths
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.loggable import Loggable
from pychron.experiment.queue.parser import RunParser, UVRunParser
from pychron.core.helpers.ctx_managers import no_update


def extract_meta(line_gen):
    metastr = ''
    # read until break
    for line in line_gen:
        if line.startswith('#====='):
            break
        metastr += '{}\n'.format(line)

    return yaml.load(metastr), metastr


class BaseExperimentQueue(Loggable):
    automated_runs = List
    cleaned_automated_runs = Property(depends_on='automated_runs[]')

    mass_spectrometer = String
    extract_device = String
    username = String
    email = String

    tray = Str
    delay_before_analyses = CInt(5)
    delay_between_analyses = CInt(30)

    stats = Instance(ExperimentStats, ())

    update_needed = Event
    refresh_table_needed = Event
    refresh_info_needed = Event
    changed = Event
    name = Property(depends_on='path')
    path = String

    executable = Bool
    _no_update = False
    initialized = True

    load_name = Str

    def _get_name(self):
        if self.path:
            return os.path.splitext(os.path.basename(self.path))[0]
        else:
            return ''

    def set_extract_device(self, v):
        self.extract_device = v

    def test(self):
        self.info('testing')
        return True

    def clear_frequency_runs(self):
        self.automated_runs = [ri for ri in self.automated_runs
                               if not ri.frequency_added]

    def add_runs(self, runviews, freq=None):
        """
            runviews: list of runs
            freq: optional inter
        """
        if not runviews:
            return

        with no_update(self):
            aruns = self.automated_runs
            #        self._suppress_aliquot_update = True
            if freq:
                cnt = 0
                n = len(aruns)
                for i, ai in enumerate(aruns[::-1]):
                    if cnt == freq:
                        run = runviews[0].clone_traits()
                        run.frequency_added = True
                        aruns.insert(n - i, run)
                        cnt = 0
                    if ai.analysis_type in ('unknown', 'air', 'cocktail'):
                        cnt += 1
            else:
                if self.selected:
                    idx = aruns.index(self.selected[-1])
                    for ri in reversed(runviews):
                        aruns.insert(idx + 1, ri)
                else:
                    aruns.extend(runviews)

                    #===============================================================================
                    # persistence
                    #===============================================================================

    def load(self, txt):
        self.initialized = False
        self.stats.delay_between_analyses = self.delay_between_analyses
        aruns = self._load_runs(txt)
        if aruns:
            with no_update(self):
                self.automated_runs = aruns
            self.initialized = True
            return True

    def dump(self, stream):
        header, attrs = self._get_dump_attrs()

        writeline = lambda m: stream.write(m + '\n')

        def tab(l, comment=False):
            s = '\t'.join(map(str, l))
            if comment:
                s = '#{}'.format(s)
            writeline(s)

        # write metadata
        self._meta_dumper(stream)
        writeline('#' + '=' * 80)

        tab(header)

        def isNotNull(vi):
            if vi and vi != NULL_STR:
                try:
                    vi = float(vi)
                    return abs(vi) > 1e-15
                except (ValueError, TypeError):
                    return True
            else:
                return False

        for arun in self.automated_runs:
            vs = arun.to_string_attrs(attrs)
            vals = [v if isNotNull(v) else '' for v in vs]
            tab(vals, comment=arun.skip)

        return stream

    def _load_meta(self, meta):
        # load sample map
        self._load_map(meta)

        #default = lambda x: str(x) if x else ' '
        default_int = lambda x: x if x is not None else 1
        key_default = lambda k: lambda x: str(x) if x else k
        default = key_default('')

        self._set_meta_param('tray', meta, default)
        self._set_meta_param('extract_device', meta, key_default('Extract Device'))
        self._set_meta_param('mass_spectrometer', meta, key_default('Spectrometer'))
        self._set_meta_param('delay_between_analyses', meta, default_int)
        self._set_meta_param('delay_before_analyses', meta, default_int)
        self._set_meta_param('username', meta, default)
        self._set_meta_param('email', meta, default)
        self._set_meta_param('load_name', meta, default, metaname='load')

    def _load_runs(self, txt):
        aruns = []
        f = (l for l in txt.split('\n'))
        meta, metastr = extract_meta(f)

        if meta is None:
            self.warning_dialog('Invalid experiment set file. Poorly formatted metadata {}'.format(metastr))
            return

        self._load_meta(meta)

        delim = '\t'

        header = map(str.strip, f.next().split(delim))

        pklass = RunParser
        if self.extract_device == 'Fusions UV':
            pklass = UVRunParser
        parser = pklass()
        for linenum, line in enumerate(f):
            skip = False
            line = line.rstrip()

            # load commented runs but flag as skipped
            if line.startswith('##'):
                continue
            if line.startswith('#'):
                skip = True
                line = line[1:]

            if not line:
                continue

            try:

                script_info, params = parser.parse(header, line, meta)
                params['mass_spectrometer'] = self.mass_spectrometer
                params['extract_device'] = self.extract_device
                params['tray'] = self.tray
                params['username'] = self.username
                params['email'] = self.email
                params['skip'] = skip

                klass = AutomatedRunSpec
                if self.extract_device == 'Fusions UV':
                    klass = UVAutomatedRunSpec

                arun = klass()
                arun.load(script_info, params)
                #arun = self._automated_run_factory(script_info, params, klass)

                aruns.append(arun)

            except Exception, e:
                import traceback

                print traceback.print_exc()
                self.warning_dialog('Invalid Experiment file {}\nlinenum= {}\nline= {}'.format(e, linenum, line))

                return

        return aruns

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

        setattr(self, attr, func(v))

    def _get_dump_attrs(self):
        seq = ['labnumber', 'sample', 'position',
               ('e_value', 'extract_value'),
               ('e_units', 'extract_units'),
               'duration', 'cleanup', 'overlap',
               ('beam_diam', 'beam_diameter'),
               'pattern',
               ('extraction', 'extraction_script'),
               ('t_o', 'collection_time_zero_offset'),
               ('measurement', 'measurement_script'),
               ('truncate','truncate_condition'),
               'syn_extraction',
               ('post_meas', 'post_measurement_script'),
               ('post_eq', 'post_equilibration_script'),
               ('s_opt', 'script_options'),
               ('dis_btw_pos','disable_between_positons'),
               'weight', 'comment',
               'autocenter']

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

        s = '''
username: {}
email: {}
date: {}
mass_spectrometer: {}
delay_before_analyses: {}
delay_between_analyses: {}
extract_device: {}
tray: {} 
load: {}
'''.format(
            self.username,
            self.email,
            datetime.datetime.today(),
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

    def isUpdateable(self):
        return not self._no_update

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


#============= EOF =============================================
