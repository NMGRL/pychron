# ===============================================================================
# Copyright 2016 ross
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
from traits.api import HasTraits, Str, Callable, Enum

# ============= standard library imports ========================
# ============= local library imports  ==========================
START_QUEUE = 1

START_RUN = 2
END_RUN = 3

END_QUEUE = 20


class ExperimentEventAddition(HasTraits):
    id = Str
    action = Callable
    level = Enum(0, START_QUEUE, START_RUN, END_QUEUE, END_RUN)

    def do(self, ctx):
        if self.action is not None:
            self.action(ctx)

# ============= EOF =============================================
