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
from traits.api import HasTraits, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================


class BaseNode(HasTraits):
    name = 'Base'
    enabled = Bool(True)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def run(self, state):
        raise NotImplementedError

    def configure(self):
        raise NotImplementedError

    def to_template(self):
        d = {'klass': self.__class__.__name__}
        self._to_template(d)

        return d

    def _to_template(self, d):
        pass
        # return []
# ============= EOF =============================================



