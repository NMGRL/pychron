# ===============================================================================
# Copyright 2020 ross
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
from traits.api import Float
from traitsui.api import HGroup, VGroup, UItem, Item, Label, spring

from pychron.pipeline.nodes.base import BaseNode
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class CosmogenicCorrectionNode(BaseNode):
    name = 'Cosmogenic Correction'

    solar3836_v = Float
    solar3836_e = Float

    cosmo3836_v = Float
    cosmo3836_e = Float

    def run(self, state):
        ans = state.unknowns

        rs = (self.solar3836_v, self.solar3836_e)
        rc = (self.cosmo3836_v, self.cosmo3836_e)

        for ai in ans:
            ai.set_cosmogenic_correction(rs, rc)

    def traits_view(self):
        # add views for configurable options
        cg = HGroup(Label('Cosmo 38/36'),
                    UItem('cosmo3836_v'), Label(PLUSMINUS_ONE_SIGMA), UItem('cosmo3836_e'))
        sg = HGroup(Item('Solar/Terrestrial/Martian 38/36'),
                    UItem('solar3836_v'), Label(PLUSMINUS_ONE_SIGMA), UItem('solar3836_e'))

        return self._view_factory(VGroup(cg, sg))

# ============= EOF =============================================
