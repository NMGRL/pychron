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

from itertools import tee
def partition(seq, predicate):
    '''
        http://stackoverflow.com/questions/949098/python-split-a-list-based-on-a-condition
        partition seqeunce based on evaluation of predicate(i)

        returns 2 generators
        True_eval, False_eval
    '''

    l1, l2 = tee((predicate(item), item) for item in seq)
    return (i for p, i in l1 if p), (i for p, i in l2 if not p)
# ============= EOF =============================================
