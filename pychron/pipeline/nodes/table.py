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
from traits.api import HasTraits, Bool, List, Str
from traitsui.api import View, UItem, TableEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.pipeline.editors.fusion.fusion_table_editor import FusionTableEditor
from pychron.pipeline.editors.interpreted_age_table_editor import InterpretedAgeTableEditor
from pychron.pipeline.nodes.base import BaseNode


class TableOptions(HasTraits):
    pass


class AnalysisTableOptions(TableOptions):
    references_enabled = Bool(False)


class TableColumn(HasTraits):
    name = Str
    display = Bool(True)
    sigfigs = Str
    key = Str


class InterpretedAgeTableOptions(TableOptions):
    columns = List

    @property
    def column_labels(self):
        return [c.name for c in self.columns if c.display]

    @property
    def column_keys(self):
        return [c.key for c in self.columns if c.display]

    @property
    def column_sigfigs(self):
        return [int(c.sigfigs) for c in self.columns if c.sigfigs]

    def _columns_default(self):
        cs = (('Sample', 'sample', ''),
              ('Identifier', 'identifier', ''),
              ('Material', 'material', ''),
              ('Irradiation', 'irradiation', ''),
              ('Age Kind', 'age_kind', ''),
              ('Age', 'display_age', 3),
              ('Age Error', 'display_age_err', 3),
              ('MSWD', 'mswd', 3),
              ('K/Ca', 'kca', 3),
              ('K/Ca Error', 'kca_err', 3))

        cols = [TableColumn(name=attr, key=key, sigfigs=str(sigfigs)) for attr, key, sigfigs in cs]
        return cols

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='display'),
                ObjectColumn(name='sigfigs')]

        v = View(UItem('columns', editor=TableEditor(columns=cols, sortable=False)),
                 title='Interpreted Age Table Options',
                 resizable=True,
                 buttons=['OK', 'Cancel'])
        return v


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

        ta = editor.tabular_adapter
        cols = [c for c in ta.columns if c[1] in self.options.column_keys]
        if cols:
            for c, si in zip(cols, self.options.column_sigfigs):
                attr = '{}_sigfigs'.format(c[1])
                if hasattr(ta, attr):
                    setattr(ta, attr, si)

            ta.columns = cols

        editor.interpreted_ages = state.interpreted_ages
        state.editors.append(editor)

# ============= EOF =============================================
