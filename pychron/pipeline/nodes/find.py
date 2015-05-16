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
from traits.api import Float, Bool
from traitsui.api import Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.graphical_filter import GraphicalFilterModel, GraphicalFilterView
from pychron.pipeline.nodes.base import BaseNode


class FindNode(BaseNode):
    pass


class FindBlanksNode(FindNode):
    name = 'Find Blanks'
    threshold = Float

    use_review = Bool

    def traits_view(self):
        v = self._view_factory(Item('threshold',
                                    tooltip='Maximum difference between blank and unknowns in hours',
                                    label='Threshold (Hrs)'),
                               Item('use_review'))

        return v

    def load(self, nodedict):
        self.threshold = nodedict['threshold']

    # def dump(self, obj):
    # obj['threshold'] = self.threshold
    #
    def run(self, state):
        # for ai in state.unknowns:
        # pass
        # atypes = tuple({ai.analysis_type for ai in state.unknowns})
        times = sorted((ai.rundate for ai in state.unknowns))
        atypes = 'blank_unknown'

        refs = self.dvc.find_references(times, atypes)

        if self.use_review:
            model = GraphicalFilterModel()
            obj = GraphicalFilterView(model=model)
            info = obj.edit_traits(kind='livemodal')
            if info.result:
                refs = 'asdf'

        state.references = refs

# ============= EOF =============================================



