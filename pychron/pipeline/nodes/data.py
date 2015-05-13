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
from traits.api import List
# ============= standard library imports ========================
from pychron.pipeline.nodes.base import BaseNode


class DataNode(BaseNode):
    name = 'Data'
    analyses = List

    analysis_kind = None

    def run(self, state):
        for ai in self.analyses:
            ai.group_id = 0

        items = getattr(state, self.analysis_kind)
        items.extend(self.analyses)

    def configure(self):
        return True


class UnknownNode(DataNode):
    analysis_kind = 'unknowns'


class ReferenceNode(DataNode):
    analysis_kind = 'references'

# ============= local library imports  ==========================


# ============= EOF =============================================



