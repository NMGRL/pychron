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
from pychron.envisage.browser.view import BrowserView
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
        browser_view = BrowserView(model=self.browser_model)
        info = browser_view.edit_traits(kind='livemodal')
        if info.result:
            records = self.browser_model.get_analysis_records()
            if records:
                analyses = self.dvc.make_analyses(records)
                if browser_view.is_append:
                    self.analyses.extend(analyses)
                else:
                    self.analyses = analyses

                return True


class UnknownNode(DataNode):
    name = 'Unknowns'
    analysis_kind = 'unknowns'


class ReferenceNode(DataNode):
    name = 'References'
    analysis_kind = 'references'

    def run(self, state):
        items = getattr(state, self.analysis_kind)
        if not self.analyses or state.has_references:
            self.analyses = items
        else:
            for ai in self.analyses:
                ai.group_id = 0

            items.extend(self.analyses)

# ============= local library imports  ==========================


# ============= EOF =============================================



