# ===============================================================================
# Copyright 2014 Jake Ross
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
from chaco.ticks import AbstractTickGenerator
from numpy import array
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.utilities.identifier import ANALYSIS_MAPPING_INTS, SPECIAL_MAPPING

TICKS = array(sorted(ANALYSIS_MAPPING_INTS.values()))


class StaticTickGenerator(AbstractTickGenerator):
    def get_ticks(self, *args, **kw):
        return TICKS


KEYS = [v[0] for v in sorted(ANALYSIS_MAPPING_INTS.items(), key=lambda x: x[1])]
TICK_KEYS = [SPECIAL_MAPPING[v] for v in KEYS]


def tick_formatter(x):
    try:
        v = TICK_KEYS[int(x)]
    except IndexError:
        v = ''
    return v


def analysis_type_formatter(x):
    try:
        v = KEYS[int(x)]
    except IndexError:
        v = ''
    return v

# ============= EOF =============================================

