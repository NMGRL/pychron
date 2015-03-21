# ===============================================================================
# Copyright 2013 Jake Ross
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
import re

from pychron.pychron_constants import DETECTOR_MAP


def rank_func(x):
    if isinstance(x, (list, tuple)):
        x = x[0]
    return re.sub('\D', '', x)


def extract_mass(x):
    return int(re.split('\w*\D', x)[-1])


def sort_isotopes(keys, reverse=True, key=None):
    if key:
        rf = lambda x: rank_func(key(x))
    else:
        rf = rank_func
    keys = list(keys)
    return sorted(keys, key=rf,
                  reverse=reverse)


def sort_detectors(idets):
    def f(det):
        if det in DETECTOR_MAP:
            return DETECTOR_MAP[det]
        else:
            return 0

    dets=sorted(idets, key=f)
    # dets = ['', ] * len(idets)
    # edets = []

    # for det in idets:
    #     if det in DETECTOR_MAP:
    #         try:
    #             dets[DETECTOR_MAP[det]] = det
    #         except IndexError:
    #             dets.append(det)
    #     else:
    #         edets.append(det)
    #
    # dets.extend(edets)
    return dets

# ============= EOF =============================================
