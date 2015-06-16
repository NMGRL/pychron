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
from traits.api import HasTraits
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.nodes.base import BaseNode


class TableOptions(HasTraits):
    pass


class TableNode(BaseNode):
    options = None

    def run(self, state):
        if state.unknowns:
            self._make_unknowns_table(state.unknowns)

        if self.options.references_enabled and state.references:
            self._make_references_table(state.references)

    def _make_unknowns_table(self, items):
        pass

    def _make_references_table(self, items):
        pass

# ============= EOF =============================================
