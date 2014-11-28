# ===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
from traits.api import HasTraits, List, Str, Int, Any
#============= standard library imports ========================
#============= local library imports  ==========================

class TempAnalysis(HasTraits):
    uuid = Any
    group_id = Int
    graph_id = Int


class PreviousSelection(HasTraits):
    analysis_ids = List(TempAnalysis)
    name = Str
    hash_str = Str

    def __init__(self, records, **kw):
        super(PreviousSelection, self).__init__(**kw)

        ps = []
        for ai in records:
            ps.append(TempAnalysis(uuid=ai.uuid,
                                   group_id=ai.group_id,
                                   graph_id=ai.graph_id,
                                   labnumber=ai.labnumber
            ))

        self.analysis_ids = ps

    def __repr__(self):
        return self.name


# ============= EOF =============================================
