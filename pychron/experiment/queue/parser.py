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
from pychron.helpers.filetools import to_bool
#============= standard library imports ========================
import re
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.regex import ALIQUOT_REGEX

class RunParser(Loggable):
    def _get_attr(self, attr):
        if isinstance(attr, tuple):
            attr, rattr = attr
        else:
            attr, rattr = attr, attr
        return attr, rattr

    def _get_idx(self, header, attr):
        try:
            return header.index(attr)
        except ValueError:
            pass

    def _load_scripts(self, header, args):
        script_info = dict()
        # load scripts
        for attr in [
                     # ver. 1.0
                     'measurement', 'extraction',
                     'post_measurement',
                     'post_equilibration',

                     # ver. 2.0
                     ('post_eq', 'post_equilibration'),
                     ('post_meas', 'post_measurement'),
                     ]:

            attr, rattr = self._get_attr(attr)
            idx = self._get_idx(header, attr)
            if idx:
                try:
                    script_info[rattr] = args[idx]
                except IndexError, e:
                    pass
#                    self.debug('base schedule _run_parser {} {}'.format(e, attr))

        return script_info

    def parse(self, header, line, meta, delim='\t'):
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

        attr, rattr = self._get_attr('truncate_condition')
        idx = self._get_idx(header, attr)
        if idx is not None:
            tc = args[idx]
            if self._validate_truncate_condition(tc):
                params['truncate_condition'] = tc

        # load strings
        for attr in [
                     'pattern',
                     'position',
                     'comment',
#                     ('truncate', 'truncate_condition'),
                     # ver 1.0
                     'extract_units',
                     # ver 2.0
                     ('e_units', 'extract_units')
                     ]:

            attr, rattr = self._get_attr(attr)
            idx = self._get_idx(header, attr)
            if idx:
                try:
                    params[rattr] = args[idx]
                except IndexError, e:
                    pass
#                     self.debug('base schedule _run_parser {} {}'.format(e, attr))

        # load booleans
        for attr in [
                     # ver 1.0
                     'autocenter',
                     'disable_between_positions',

                     # ver 2.0
                     ('dis_btw_pos', 'disable_between_positions')
                     ]:
            attr = self._get_attr(attr)
            idx = self._get_idx(header, attr)
            if idx:
                try:
                    param = args[idx]
                except IndexError:
                    params[rattr] = False
                    continue

                if param.strip():
                    bo = to_bool(param)
                    if bo is not None:
                        params[rattr] = bo
                    else:
                        params[rattr] = False

        # load numbers
        for attr in ['duration',
#                     'overlap',
                     'cleanup',
#                     'aliquot',

                     'ramp_duration',

                     # ver 1.0
                     'extract_group',
                     # ver 2.0
                     ('e_group', 'extract_group'),
                     'weight',
                     # ver 1.0
                     'extract_value',
                     # ver 2.0
                     ('e_value', 'extract_value'),
                     'beam_diameter'
                     ]:
            attr, rattr = self._get_attr(attr)
            idx = self._get_idx(header, attr)
            if idx:
                try:
                    param = args[idx]
                    params[rattr] = float(param.strip())
                except IndexError, e:
                    pass
#                    self.debug('{} {}'.format(e, attr))
                except ValueError, e:
                    pass
#                     self.debug('{} {} {}'.format(e, attr, param))

        return script_info, params

    def _validate_truncate_condition(self, t):
        if t.endswith('.yaml'):
            return True

        try:
            c, start = t.split(',')
            pat = '<=|>=|[<>=]'
            attr, value = re.split(pat, c)
            m = re.search(pat, c)
            comp = m.group(0)
#             self.py_add_truncation(attr, comp, value, int(start))
            return True
        except Exception, e:
            self.debug('truncate_condition parse failed {} {}'.format(e, t))


class UVRunParser(RunParser):
    def parse(self, header, line, meta, delim='\t'):
        script_info, params = super(UVRunParser, self).parse(header, line, meta, delim)
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

    #============= EOF =============================================
