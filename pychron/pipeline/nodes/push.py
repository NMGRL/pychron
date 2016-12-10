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
from traits.api import Instance

from pychron.dvc.func import repository_has_staged
from pychron.pipeline.nodes.base import BaseNode


class PushNode(BaseNode):
    dvc = Instance('pychron.dvc.dvc.DVC')

    def run(self, state):
        ps = {ai.repository_identifier for ans in (state.unknowns, state.references) for ai in ans}
        # ps.union({ai.repository_identifier})
        if ps:
            changed = repository_has_staged(ps)
            self.debug('pipeline has changes to {}'.format(changed))
            if changed:
                # m = 'You have changes to analyses. Would you like to share them?'
                # ret = self._handle_prompt_for_save(m, 'Share Changes')
                # if ret == 'save':
                self.dvc.push_repositories(changed)

# ============= EOF =============================================
