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
from traits.api import Interface
# ============= standard library imports ========================
# ============= local library imports  ==========================
import traits.has_traits

traits.has_traits.CHECK_INTERFACES = 1


class IDatastore(Interface):
    def get_greatest_aliquot(self, identifier):
        pass

    def get_greatest_step(self, identifier, aliquot):
        pass

    def connect(self, *args, **kw):
        pass

    def is_connected(self):
        pass

# ============= EOF =============================================
