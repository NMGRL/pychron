# ===============================================================================
# Copyright 2015 Jake Ross
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
from numpy import array, argmin
# ============= local library imports  ==========================
from pychron.pychron_constants import QTEGRA_INTEGRATION_TIMES


def normalize_integration_time(it):
    """
    find the integration time closest to "it"
    """
    try:
        x = array(QTEGRA_INTEGRATION_TIMES)
        return x[argmin(abs(x - it))]
    except TypeError:
        return 1.0


def calculate_radius(m_e, hv, mfield):
    """
    m_e= mass/charge
    hv= accelerating voltage (V)
    mfield= magnet field (H)
    """
    r = ((2 * m_e * hv) / mfield ** 2) ** 0.5

    return r

# ============= EOF =============================================
