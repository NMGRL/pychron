# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
import os
import string

import yaml

from pychron.paths import paths

STARTUP_MESSAGE_POSITION = (100, 300)

SPECTROMETER_PROTOCOL = 'pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager'
ION_OPTICS_PROTOCOL = 'pychron.spectrometer.ion_optics_manager.IonOpticsManager'
SCAN_PROTOCOL = 'pychron.spectrometer.scan_manager.ScanManager'
EL_PROTOCOL = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'
DVC_PROTOCOL = 'pychron.dvc.dvc.DVC'
FURNACE_PROTOCOL = 'pychron.furnace.furnace_manager.BaseFurnaceManager'

TTF_FONTS = ['Courier New', 'Arial', 'Georgia', 'Impact', 'Verdana']
FONTS = ['Helvetica'] + TTF_FONTS
SIZES = [10, 6, 8, 9, 10, 11, 12, 14, 15, 18, 24, 36]

PLUSMINUS = '\N{Plus-minus sign}'
SIGMA = '\N{Greek Small Letter Sigma}'
LAMBDA = '\u03BB'

PLUSMINUS_NSIGMA = '{}{{}}{}'.format(PLUSMINUS, SIGMA)
PLUSMINUS_ONE_SIGMA = PLUSMINUS_NSIGMA.format(1)
PLUSMINUS_TWO_SIGMA = PLUSMINUS_NSIGMA.format(2)
PLUSMINUS_PERCENT = '{}%  '.format(PLUSMINUS)

SPECIAL_IDENTIFIER = 'Special Identifier'
NULL_STR = '---'
LINE_STR = '---------'
SCRIPT_KEYS = ['measurement', 'post_measurement', 'extraction', 'post_equilibration']
SCRIPT_NAMES = ['{}_script'.format(si) for si in SCRIPT_KEYS]

SD = 'SD'
SEM = 'SEM'
MSEM = 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)'
ERROR_TYPES = [MSEM, SEM, SD]
SIG_FIGS = range(0, 15)

WEIGHTED_MEAN = 'Weighted Mean'
INTEGRATED = 'Total Integrated'
DEFAULT_INTEGRATED = 'Plateau else Valid Integrated'
VALID_INTEGRATED = 'Valid Integrated'
PLATEAU_INTEGRATED = 'Plateau Integrated'

FIT_TYPES = ['Linear', 'Parabolic', 'Cubic',
             'Average', 'Exponential', WEIGHTED_MEAN]

FIT_ERROR_TYPES = [SD, SEM, 'CI', 'MonteCarlo']

ARITHMETIC_MEAN = 'Arithmetic Mean'
PLATEAU_ELSE_WEIGHTED_MEAN = 'Plateau else Weighted Mean'

AGE_SUBGROUPINGS = (PLATEAU_ELSE_WEIGHTED_MEAN, WEIGHTED_MEAN,
                    INTEGRATED, VALID_INTEGRATED, PLATEAU_INTEGRATED, DEFAULT_INTEGRATED,
                    ARITHMETIC_MEAN, 'Plateau', 'Isochron')
SUBGROUPINGS = [WEIGHTED_MEAN,
                INTEGRATED, VALID_INTEGRATED, PLATEAU_INTEGRATED, DEFAULT_INTEGRATED,
                ARITHMETIC_MEAN]

SUBGROUPING_ATTRS = ('age', 'kca', 'kcl', 'radiogenic_yield', 'moles_k39', 'signal_k39')

WEIGHTINGS = (NULL_STR, 'Volume', 'Variance')
INTERPOLATE_TYPES = ['Preceding', 'Bracketing Interpolate', 'Bracketing Average']
FIT_TYPES_INTERPOLATE = FIT_TYPES + INTERPOLATE_TYPES
DELIMITERS = {',': 'comma', '\t': 'tab', ' ': 'space'}

# AGE_SCALARS = {'Ga': 1e9, 'Ma': 1e6, 'ka': 1e3, 'a': 1}
# AGE_MA_SCALARS = {'Ma': 1, 'ka': 1e-3, 'a': 1e-6, 'Ga': 1e3}

DESCENDING = 'Descending'
ASCENDING = 'Ascending'
AGE_SORT_KEYS = (NULL_STR, ASCENDING, DESCENDING)

UNKNOWN = 'unknown'
COCKTAIL = 'cocktail'
BLANK = 'blank'
DETECTOR_IC = 'detector_ic'
PAUSE = 'pause'
DEGAS = 'degas'
AIR = 'air'

BLANK_UNKNOWN = 'blank_unknown'
BLANK_EXTRACTIONLINE = 'blank_extractionline'
BLANK_TYPES = [BLANK_UNKNOWN, 'blank_air', 'blank_cocktail']

SNIFF = 'sniff'
SIGNAL = 'signal'
BASELINE = 'baseline'
WHIFF = 'whiff'

EXTRACT_DEVICE = 'Extract Device'
NO_EXTRACT_DEVICE = 'No Extract Device'

seeds = string.ascii_uppercase
ALPHAS = [a for a in seeds] + ['{}{}'.format(a, b)
                               for a in seeds
                               for b in seeds]

MAIN = 'Main'
APPEARANCE = 'Appearance'
DISPLAY = 'Display'
GROUPS = 'Groups'


def alpha_to_int(s):
    return ALPHAS.index(s)


def alphas(idx):
    """
        idx should be 0-base ie. idx=0 ==>A
    """
    if idx < 26:
        return seeds[idx]
    else:
        a = idx / 26 - 1
        b = idx % 26
        return '{}{}'.format(seeds[a], seeds[b])


INTERFERENCE_KEYS = ('K4039', 'K3839', 'K3739', 'Ca3937', 'Ca3837', 'Ca3637', 'Cl3638')
RATIO_KEYS = ('Ca_K', 'Cl_K')

AR40 = 'Ar40'
AR39 = 'Ar39'
AR38 = 'Ar38'
AR37 = 'Ar37'
AR36 = 'Ar36'

ARGON_KEYS = (AR40, AR39, AR38, AR37, AR36)

ARAR_MAPPING = dict({k: v for k, v in zip(ARGON_KEYS, ARGON_KEYS)})

IRRADIATION_KEYS = [('k4039', 'K_40_Over_39'),
                    ('k3839', 'K_38_Over_39'),
                    ('k3739', 'K_37_Over_39'),
                    ('ca3937', 'Ca_39_Over_37'),
                    ('ca3837', 'Ca_38_Over_37'),
                    ('ca3637', 'Ca_36_Over_37'),
                    ('cl3638', 'P36Cl_Over_38Cl')]

DECAY_KEYS = [('a37decayfactor', '37_Decay'),
              ('a39decayfactor', '39_Decay')]

MEASUREMENT_COLOR = '#FF7EDF'  # magenta
EXTRACTION_COLOR = '#FFFF66'
SUCCESS_COLOR = '#66FF33'  # light green
SKIP_COLOR = '#33CCFF'
CANCELED_COLOR = '#FF9999'
TRUNCATED_COLOR = 'orange'
FAILED_COLOR = 'red'
END_AFTER_COLOR = 'gray'
NOT_EXECUTABLE_COLOR = 'red'

LIGHT_RED = '#FF7373'
LIGHT_YELLOW = '#F7F6D0'
LIGHT_GREEN = '#99FF99'

DETECTOR_ORDER = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
DETECTOR_MAP = {o: i for i, o in enumerate(DETECTOR_ORDER)}

IC_ANALYSIS_TYPE_MAP = {'air': 0, 'cocktail': 1}

QTEGRA_INTEGRATION_TIMES = [0.065536, 0.131072, 0.262144, 0.524288,
                            1.048576, 2.097152, 4.194304, 8.388608,
                            16.777216, 33.554432, 67.108864]
QTEGRA_DEFAULT_INTEGRATION_TIME = 1.048576
ISOTOPX_INTEGRATION_TIMES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0]
ISOTOPX_DEFAULT_INTEGRATION_TIME = 1

DEFAULT_INTEGRATION_TIME = 1

K_DECAY_CONSTANTS = {'Min et al., 2000': (5.80e-11, 0, 4.883e-10, 0),
                     'Steiger & Jager 1977': (5.81e-11, 0, 4.962e-10, 0)}

FLUX_CONSTANTS = {'FC Min': {'lambda_ec': [5.80e-11, 0], 'lambda_b': [4.883e-10, 0], 'monitor_age': 28.201},
                  'FC SJ': {'lambda_ec': [5.81e-11, 0], 'lambda_b': [4.962e-10, 0],
                            'monitor_age': 28.02}}

if paths.setup_dir:
    flux_constants = os.path.join(paths.setup_dir, 'flux_constants.yaml')
    if os.path.isfile(flux_constants):
        with open(flux_constants, 'r') as rf:
            obj = yaml.load(rf)
            try:
                FLUX_CONSTANTS.update(obj)
            except BaseException:
                pass

AR_AR = 'Ar/Ar'

QTEGRA_SOURCE_KEYS = ('extraction_lens', 'ysymmetry', 'zsymmetry', 'zfocus')
QTEGRA_SOURCE_NAMES = ('ExtractionLens', 'Y-Symmetry', 'Z-Symmetry', 'Z-Focus')

BLANKS = ['Blank Unknown', 'Blank Air', 'Blank Cocktail', 'Blank']
REFERENCE_ANALYSIS_TYPES = ['Air', 'Cocktail']
ANALYSIS_TYPES = ['Unknown'] + REFERENCE_ANALYSIS_TYPES + BLANKS

DEFAULT_MONITOR_NAME = 'FC-2'

ELLIPSE_KINDS = ('1' + SIGMA, '2' + SIGMA, '95%')
ELLIPSE_KIND_SCALE_FACTORS = dict(zip(ELLIPSE_KINDS, (1, 2, 2.4477)))

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

DEFAULT_PIPELINE_ROOTS = ('Fit', 'Plot', 'Table', 'History', 'Share', 'Transfer', 'MDD', 'User')

# SAMPLE PREP ===================================================
INITIAL_STEPS = ('crush', 'sieve', 'wash')
HIGH_GRADE_STEPS = ('frantz', 'heavy_liquid', 'gold_table', 'acid', 'pick')
IMAGE_STEPS = ('mount', 'us_wand', 'eds', 'cl', 'bse', 'se')

SAMPLE_PREP_STEPS = INITIAL_STEPS + HIGH_GRADE_STEPS + IMAGE_STEPS

SAMPLE_METADATA = ('sample',
                   'material',
                   'grainsize',
                   'project',
                   'principal_investigator',
                   'latitude',
                   'longitude',
                   'lithology',
                   'lithology_class',
                   'lithology_group',
                   'lithology_type',
                   'rlocation',
                   'irradiation',
                   'irradiation_level',
                   'irradiation_position')

EXTRACTION_ATTRS = ('weight', 'extract_device', 'tray', 'extract_value',
                    'extract_units',
                    # 'duration',
                    # 'cleanup',
                    'load_name',
                    'load_holder',
                    'extract_duration',
                    'cleanup_duration',
                    'pattern', 'beam_diameter', 'ramp_duration', 'ramp_rate')

META_ATTRS = ('analysis_type', 'uuid', 'identifier', 'aliquot', 'increment',

              'comment', 'mass_spectrometer',
              'username', 'queue_conditionals_name',
              'repository_identifier',
              'acquisition_software',
              'data_reduction_software', 'instrument_name', 'laboratory', 'experiment_queue_name', 'experiment_type',

              ) + SAMPLE_METADATA

# ============= EOF =============================================
