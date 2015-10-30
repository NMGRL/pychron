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
from pychron.pipeline.editors.fusion.fusion_table_editor import FusionTableEditor
from pychron.pipeline.editors.interpreted_age_table_editor import InterpretedAgeTableEditor
from pychron.pipeline.nodes.base import BaseNode


class TableOptions(HasTraits):
    pass


class AnalysisTableOptions(TableOptions):
    references_enabled = Bool(False)


class InterpretedAgeTableOptions(TableOptions):
    pass


# ==================================================


class TableNode(BaseNode):
    pass
    # options = Instance(TableOptions)

    # def configure(self, pre_run=False, **kw):
    #     if not pre_run:
    #         self._manual_configured = True
    #
    #     return self._configure(self.options)

    # def _options_default(self):
    #     return self.options_klass()


class AnalysisTableNode(TableNode):
    name = 'Analysis Table'
    options_klass = AnalysisTableOptions

    auto_configure = False

    def run(self, state):
        if state.unknowns:
            self._make_unknowns_table(state)

        if self.options.references_enabled and state.references:
            self._make_references_table(state.references)

    def _make_unknowns_table(self, state):
        items = state.unknowns

        editor_klass = FusionTableEditor
        editor = editor_klass()

        editor.items = items
        state.editors.append(editor)

    def _make_references_table(self, items):
        pass


class InterpretedAgeTableNode(TableNode):
    name = 'Interpreted Age Table'
    options_klass = InterpretedAgeTableOptions

    def run(self, state):
        editor = InterpretedAgeTableEditor()
        editor.interpreted_ages = state.interpreted_ages
        state.editors.append(editor)
# ============= EOF =============================================
