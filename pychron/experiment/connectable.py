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
from __future__ import absolute_import

from traits.api import HasTraits, Int, Bool, Str, Any

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traits.trait_errors import TraitError


class Connectable(HasTraits):
    name = Str
    host = Str
    port = Int
    kind = Str
    connected = Bool
    protocol = Any

    # can this connection be used by the AutomatedRunMonitor
    monitorable = False
    manager = Any

    def set_connection_parameters(self, obj):
        if hasattr(obj, "communicator"):
            com = obj.communicator
            for attr in "host", "port", "kind":
                if hasattr(com, attr):
                    try:
                        setattr(self, attr, getattr(com, attr))
                    except TraitError:
                        pass

            self.monitorable = True


# ============= EOF =============================================
