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

#============= standard library imports ========================
#============= local library imports  ==========================
from itertools import groupby

from pychron.core.helpers.iterfuncs import partition
from pychron.experiment.utilities.identifier import is_special


def renumber_aliquots(aruns):
    key = lambda x: x.labnumber
    akey = lambda x: x.user_defined_aliquot

    aruns = sorted(aruns, key=key)
    for ln, ans in groupby(aruns, key=key):
        if is_special(ln):
            continue

        b, a = partition(ans, akey)
        b = list(b)
        if b:
            minaliquot = min([bi.user_defined_aliquot for bi in b])
            for i, (al, ans) in enumerate(groupby(b, key=akey)):
                for ai in ans:
                    ai.user_defined_aliquot = minaliquot + i

# ============= EOF =============================================
