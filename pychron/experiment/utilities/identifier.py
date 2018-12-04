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

import os
import re

import yaml

# ============= local library imports  ==========================
from pychron.file_defaults import IDENTIFIERS_DEFAULT
from pychron.paths import paths
from pychron.pychron_constants import LINE_STR, ALPHAS, SPECIAL_IDENTIFIER

IDENTIFIER_REGEX = re.compile(r'(?P<identifier>\d+)-(?P<aliquot>\d+)(?P<step>\w*)')
SPECIAL_IDENTIFIER_REGEX = re.compile(r'(?P<identifier>\w{1,2}-[\d\w]+-\w)-(?P<aliquot>\d+)')

ANALYSIS_MAPPING_UNDERSCORE_KEY = dict()  # blank_air: ba
ANALYSIS_MAPPING = dict()  # ba: 'Blank Air'
NON_EXTRACTABLE = dict()  # ba: 'Blank Air'
ANALYSIS_MAPPING_INTS = dict()  # blank_air: 0
SPECIAL_MAPPING = dict()  # blank_air: ba
SPECIAL_NAMES = [SPECIAL_IDENTIFIER, LINE_STR]  # 'Blank Air'
SPECIAL_KEYS = []  # ba

try:
    p = os.path.join(paths.hidden_dir, 'identifiers.yaml')
    with open(p, 'r') as rfile:
        yd = yaml.load(rfile)
except BaseException:
    yd = yaml.load(IDENTIFIERS_DEFAULT)

for i, idn_d in enumerate(yd):
    key = idn_d['shortname']
    value = idn_d['name']
    ANALYSIS_MAPPING[key] = value

    underscore_name = value.lower().replace(' ', '_')

    ANALYSIS_MAPPING_INTS[underscore_name] = i
    ANALYSIS_MAPPING_UNDERSCORE_KEY[underscore_name] = key

    if not idn_d['extractable']:
        NON_EXTRACTABLE[key] = value

    if idn_d['special']:
        SPECIAL_MAPPING[underscore_name] = key
        SPECIAL_NAMES.append(value)
        SPECIAL_KEYS.append(key)


def convert_identifier_to_int(ln):
    m = {'ba': 1, 'bc': 2, 'bu': 3, 'bg': 4, 'u': 5, 'c': 6, 'ic': 7}

    try:
        return int(ln)
    except ValueError:
        return m[ln]


def convert_special_name(name, output='shortname'):
    """
        input name output shortname

        name='Background'
        returns:

            if output=='shortname'
                return 'bg'
            else
                return 4 #identifier
    """
    if isinstance(name, str):
        name = name.lower()
        name = name.replace(' ', '_')
        if name in SPECIAL_MAPPING:
            sn = SPECIAL_MAPPING[name]
            if output == 'labnumber':
                sn = convert_identifier(sn)
            return sn
    else:
        return name


def convert_identifier(identifier):
    """
        old:
            identifier=='bg, a, ...'
            return  1

        identifier== bu-FD-J, 51234, 13212-01
        return bu-FD-J, 51234, 13212

    """
    if '-' in identifier:
        ln = identifier.split('-')[0]
        try:
            ln = int(ln)
            identifier = str(ln)
        except ValueError:
            return identifier

    return identifier


def get_analysis_type(idn):
    """
        idn: str like 'a-...' or '43513'
    """
    idn = idn.lower()
    for atype, tag in SPECIAL_MAPPING.items():
        if idn.startswith(tag):
            return atype
    else:
        return 'unknown'


def make_runid(ln, a, s=''):
    _as = make_aliquot_step(a, s)
    return '{}-{}'.format(ln, _as)


def strip_runid(r):
    l, x = r.split('-')

    a = ''
    for i, xi in enumerate(x):
        a += xi
        try:
            int(a)
        except ValueError:
            a = x[:i]
            s = x[i:]
            break
    else:
        s = ''

    return l, int(a), s


def make_step(s):
    if isinstance(s, (float, int, int)):
        s = ALPHAS[int(s)]
    return s or ''


def make_increment(s):
    return ALPHAS.index(s)


def make_aliquot(a):
    if not isinstance(a, str):
        a = '{:02d}'.format(int(a))
    return a


def make_aliquot_step(a, s):
    a = make_aliquot(a)
    s = make_step(s)
    return '{}{}'.format(a, s)


def make_identifier(ln, ed, ms):
    try:
        _ = int(ln)
        return ln
    except ValueError:
        return make_special_identifier(ln, ed, ms)


def make_standard_identifier(ln, modifier, ms, aliquot=None):
    """
        ln: str or int
        a: int
        modifier: str or int. if int zero pad
        ms: int or str
    """
    if isinstance(ms, int):
        ms = '{:02d}'.format(ms)
    try:
        modifier = '{:02d}'.format(modifier)
    except ValueError:
        pass

    d = '{}-{}-{}'.format(ln, modifier, ms)
    if aliquot:
        d = '{}-{:02d}'.format(d, aliquot)
    return d


def make_special_identifier(ln, ed, ms, aliquot=None):
    """
        ln: str or int
        a: int aliquot
        ms: int mass spectrometer id
        ed: int extract device id
    """
    if isinstance(ed, int):
        ed = '{:02d}'.format(ed)
    if isinstance(ms, int):
        ms = '{:02d}'.format(ms)

    d = '{}-{}-{}'.format(ln, ed, ms)
    if aliquot:
        if not isinstance(aliquot, str):
            aliquot = '{:02d}'.format(aliquot)

        d = '{}-{}'.format(d, aliquot)
    return d


def make_rid(ln, a, step=''):
    """
        if ln can be converted to integer return runid
        else return ln-a
    """
    try:
        _ = int(ln)
        return make_runid(ln, a, step)
    except ValueError:
        if not isinstance(a, str):
            a = '{:02d}'.format(a)
        return '{}-{}'.format(ln, a)


def is_special(ln):
    special = False
    if '-' in ln:
        special = ln.split('-')[0] in ANALYSIS_MAPPING
    return special


def convert_extract_device(name):
    """
        change Fusions UV to FusionsUV, etc
    """
    n = ''
    if name:
        n = name.replace(' ', '')
    return n


def pretty_extract_device(ident):
    """
        change fusions_uv to Fusions UV, etc
    """
    n = ''
    if ident:
        args = ident.split('_')
        if args[-1] in ('uv, co2'):
            n = ' '.join([a.capitalize() for a in args[:-1]])
            n = '{} {}'.format(n, args[-1].upper())
        else:
            n = ' '.join([a.capitalize() for a in args])
    return n

# ============= EOF =============================================
