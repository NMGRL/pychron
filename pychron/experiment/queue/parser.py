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
from pychron.core.helpers.strtools import to_bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.regex import ALIQUOT_REGEX


class RunParser(Loggable):
    def parse(self, header, line, delim='\t'):
        params = dict()
        if not isinstance(line, list):
            line = line.split(delim)

        args = map(str.strip, line)
        script_info = self._load_scripts(header, args)
        ln = args[header.index('labnumber')]
        if ALIQUOT_REGEX.match(ln):
            ln, a = ln.split('-')
            #params['aliquot'] = int(a)
            params['user_defined_aliquot'] = int(a)

        params['labnumber'] = ln

        # load strings
        self._load_strings(header, args, params)

        # load booleans
        self._load_booleans(header, args, params)

        # load numbers
        self._load_numbers(header, args, params)

        return script_info, params

    def _load_scripts(self, header, args):
        script_info = dict()
        # load scripts
        for attr in ['measurement', 'extraction',
                     ('script_options', 's_opt'),
                     ('post_measurement', 'post_meas'),
                     ('post_equilibration', 'post_eq'), ]:
            v = self._get_attr_value(header, args, attr)
            if v is not None:
                script_info[v[0]] = v[1]

        return script_info

    def _get_attr_value(self, header, args, attr, cast=None):
        for hi, ai in self._get_attr(attr):
            idx = self._get_idx(header, ai)
            #print header
            #print hi, ai, idx
            if idx:
                try:
                    v = args[idx]
                    if v.strip():
                        return hi, cast(v) if cast else v
                except IndexError, e:
                    pass
                    #print e, attr, idx, args

    def _load_strings(self, header, args, params):
        for attr in [
            'pattern',
            'position',
            'comment',
            'syn_extraction',
            'overlap',
            ('conditionals', 'truncate'),
            ('extract_units', 'e_units')]:
            v = self._get_attr_value(header, args, attr)
            if v is not None:
                params[v[0]] = v[1]

    def _load_numbers(self, header, args, params):
        for attr in ['duration',
                     'cleanup',
                     ('ramp_duration','ramp'),
                     'weight',
                     ('time_zero_offset', 't_o'),
                     ('extract_value', 'e_value'),
                     ('beam_diameter', 'beam_diam'),
                     'frequency_group', ]:

            v = self._get_attr_value(header, args, attr, cast=float)
            if v is not None:
                params[v[0]] = v[1]

    def _load_booleans(self, header, args, params):

        for attr in [
            'autocenter',
            'use_cdd_warming',
            ('disable_between_positions', 'dis_btw_pos')]:
            v = self._get_attr_value(header, args, attr, cast=lambda x: to_bool(x.strip()))
            if v is not None:
                params[v[0]] = v[1]

            #     def _validate_truncate_condition(self, t):
            #         if t.endswith('.yaml'):
            #             return True
            #
            #         try:
            #             c, start = t.split(',')
            #             pat = '<=|>=|[<>=]'
            #             attr, value = re.split(pat, c)
            #             m = re.search(pat, c)
            #             comp = m.group(0)
            # #             self.py_add_truncation(attr, comp, value, int(start))
            #             return True
            #         except Exception, e:
            #             self.debug('truncate_condition parse failed {} {}'.format(e, t))

    def _get_attr(self, attr):
        if isinstance(attr, tuple):
            ref = attr[0]
            return [(ref, hi) for hi in attr]
        else:
            return [(attr, attr)]

    def _get_idx(self, header, attr):
        try:
            return header.index(attr)
        except ValueError:
            pass


class UVRunParser(RunParser):
    def parse(self, header, line, delim='\t'):
        script_info, params = super(UVRunParser, self).parse(header, line, delim)
        if not isinstance(line, list):
            line = line.split(delim)

        args = map(str.strip, line)

        def _set(attr, cast):
            try:
                idx = self._get_idx(header, attr)
                v = args[idx]
                params[attr] = cast(v)
            except (IndexError, ValueError, TypeError), e:
                #print e
                pass

        _set('reprate', int)
        _set('attenuator', str)
        _set('mask', str)
        _set('image', str)

        return script_info, params

        # ============= EOF =============================================
