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
#============= standard library imports ========================
#============= local library imports  ==========================
PLUSMINUS = u'\u00b1'
try:
    PLUSMINUS_ERR = u'{}Err.'.format(PLUSMINUS)
except UnicodeEncodeError:
    PLUSMINUS = '+/-'
    PLUSMINUS_ERR = '{}Err.'.format(PLUSMINUS)

SIGMA = u'\u03c3'
try:
    SIGMA = u'{}'.format(SIGMA)
except UnicodeEncodeError, e:
    try:
        SIGMA = unicode('\x73', encoding='Symbol')
    except Exception:
        SIGMA = 's'

NULL_STR = '---'
LINE_STR = '---------'
SCRIPT_KEYS = ['measurement', 'post_measurement', 'extraction', 'post_equilibration']
SCRIPT_NAMES = ['{}_script'.format(si) for si in SCRIPT_KEYS]

FIT_TYPES = ['linear', 'parabolic', 'cubic',
             'average','weighted_mean'
             ]

INTERPOLATE_TYPES = ['preceding', 'Bracketing Interpolate', 'Bracketing Average']
FIT_TYPES_INTERPOLATE = FIT_TYPES + ['preceding', 'Bracketing Interpolate', 'Bracketing Average']
DELIMITERS = {',': 'comma', '\t': 'tab', ' ': 'space'}
AGE_SCALARS = {'Ma': 1e6, 'ka': 1e3, 'a': 1}

import string

seeds = string.ascii_uppercase
ALPHAS = [a for a in seeds] + ['{}{}'.format(a, b)
                               for a in seeds
                               for b in seeds]


def alphas(idx):
    '''
        idx should be 0-base ie. idx=0 ==>A
    '''
    if idx < 26:
        return seeds[idx]
    else:
        a = idx / 26 - 1
        b = idx % 26
        return '{}{}'.format(seeds[a], seeds[b])


ARGON_KEYS = ('Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36')
IRRADIATION_KEYS = [('k4039', 'K_40_Over_39'),
                    ('k3839', 'K_38_Over_39'),
                    ('k3739', 'K_37_Over_39'),
                    ('ca3937', 'Ca_39_Over_37'),
                    ('ca3837', 'Ca_38_Over_37'),
                    ('ca3637', 'Ca_36_Over_37'),
                    ('cl3638', 'P36Cl_Over_38Cl')
]

DECAY_KEYS = [('a37decayfactor', '37_Decay'),
              ('a39decayfactor', '39_Decay'),
]

MEASUREMENT_COLOR = '#FF7EDF'  # magenta
EXTRACTION_COLOR = '#FFFF66'
SUCCESS_COLOR = '#66FF33'  # light green
SKIP_COLOR = '#33CCFF'
CANCELED_COLOR = '#FF9999'
TRUNCATED_COLOR = 'orange'
FAILED_COLOR = 'red'
END_AFTER_COLOR = 'gray'
NOT_EXECUTABLE_COLOR = 'red'

LIGHT_RED_COLOR = '#FF7373'

DETECTOR_ORDER = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
DETECTOR_MAP = {o: i for i, o in enumerate(DETECTOR_ORDER)}

IC_ANALYSIS_TYPE_MAP = {'air': 0, 'cocktail': 1}

QTEGRA_INTEGRATION_TIMES = [0.065536, 0.131072, 0.262144, 0.524288,
                                  1.048576, 2.097152, 4.194304, 8.388608,
                                  16.777216, 33.554432, 67.108864]
DEFAULT_INTEGRATION_TIME = 1.048576

# MINNA_BLUFF_IRRADIATIONS = [('NM-205', ['E', 'F' , 'G', 'H', 'O']),
# ('NM-213', ['A', 'C', 'I', 'J', 'K', 'L']),
# ('NM-216', ['C', 'D', 'E', 'F']),
# ('NM-220', ['L', 'M', 'N', 'O']),
# ('NM-222', ['A', 'B', 'C', 'D']),
# ('NM-256', ['E', 'F'])]
#============= EOF =============================================
