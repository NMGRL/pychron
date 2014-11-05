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
from collections import Counter
# ============= local library imports  ==========================


class CondCounter(object):
    _counter = None

    def __init__(self):
        self.reset_counter()

    def reset_counter(self):
        self._counter = Counter()

    def check_counter(self, key, n):
        counter = self._counter
        counter.update([key])
        return counter[key] >= n


cnt = CondCounter()
reset_conditional_results = cnt.reset_counter
check_conditional_results = cnt.check_counter
# ============= EOF =============================================



