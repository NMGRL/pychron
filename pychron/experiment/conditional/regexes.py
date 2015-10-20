# ===============================================================================
# Copyright 2014 Jake Ross
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
import re
# ============= local library imports  ==========================
# match .current_point
CP_REGEX = re.compile(r'[\w\d]+\.(current|cur)')
# match .std_dev
STD_REGEX = re.compile(r'[\w\d]+\.(std_dev|sd|stddev)')
# match .inactive
ACTIVE_REGEX = re.compile(r'[\w\d]+\.inactive')

# Functions
def make_func_regex(r):
    reg = r'(not ){{0,1}}{}'.format(r)
    return re.compile(reg)

# match average(ar##)
AVG_REGEX = make_func_regex('average\([A-Za-z]+\d*\)')
# AVG_REGEX = re.compile(r'average\([A-Za-z]+\d*\)')
# match max(ar##)
MAX_REGEX = make_func_regex(r'max\([A-Za-z]+\d*\)')
# MAX_REGEX = re.compile(r'max\([A-Za-z]+\d*\)')
# match min(ar##)
MIN_REGEX = make_func_regex(r'min\([A-Za-z]+\d*\)')
# MIN_REGEX = re.compile(r'min\([A-Za-z]+\d*\)')
# match slope(ar##)
# SLOPE_REGEX = re.compile(r'slope\([A-Za-z]+\d*\)')
SLOPE_REGEX = make_func_regex(r'slope\([A-Za-z]+\d*\)')
# match between(age, 0,10)
# BETWEEN_REGEX = make_func_regex(r'between\([\w\d\s]+(\.\w+)*\s*,\s*[-\d+]+(\.\d)*(\s*,\s*[-\d+]+(\.\d)*)\)')
BETWEEN_REGEX = make_func_regex(r'between\([\w\d\s\(\)]+(\.\w+)*\s*,\s*[-\d+]+(\.\d)*(\s*,\s*[-\d+]+(\.\d)*)\)')


# match x in x**2+3x+1
MAPPER_KEY_REGEX = re.compile(r'[A-Za-z]+')

# match kca, ar40, etc..
KEY_REGEX = re.compile(r'[A-Za-z]+\d*')

BASELINE_REGEX = re.compile(r'[\w\d]+\.bs')
BASELINECOR_REGEX = re.compile(r'[\w\d]+\.bs_corrected')

PARENTHESES_REGEX = re.compile(r'\([\w\d\s]+\)')

COMP_REGEX = re.compile(r'<=|>=|>|<|==')

DEFLECTION_REGEX = re.compile(r'[\w\d]+\.deflection')

RATIO_REGEX = re.compile(r'[A-Za-z]{1,2}\d{1,2}/[A-Za-z]{1,2}\d{1,2}')

ARGS_REGEX = re.compile(r'\(.+\)')

PRESSURE_REGEX = re.compile(r'\w+\.\w+\.pressure')
DEVICE_REGEX = re.compile(r'device\.\w+')

INTERPOLATE_REGEX = re.compile(r'\$\w+')
# ============= EOF =============================================



