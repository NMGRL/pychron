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
from itertools import groupby

from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.tables.xlsx_table_writer import XLSXTableWriterOptions
from pychron.processing.analyses.analysis_group import AnalysisGroup


class TableNode(BaseNode):
    pass


class XLSXAnalysisTableNode(TableNode):
    name = 'Analysis Table'
    options_klass = XLSXTableWriterOptions

    def finish_configure(self):
        self.options.dump()

    def run(self, state):
        self._make_table(state)

    def _make_table(self, state):
        unknowns = (a for a in state.unknowns if a.analysis_type == 'unknown')
        blanks = (a for a in state.unknowns if a.analysis_type == 'blank_unknown')
        airs = (a for a in state.unknowns if a.analysis_type == 'air')

        key = lambda x: x.group_id
        unk_group = [AnalysisGroup(analyses=list(analyses)) for _, analyses in groupby(sorted(unknowns, key=key),
                                                                                       key=key)]
        blank_group = [AnalysisGroup(analyses=list(analyses)) for _, analyses in groupby(sorted(blanks, key=key),
                                                                                         key=key)]
        air_group = [AnalysisGroup(analyses=list(analyses)) for _, analyses in groupby(sorted(airs, key=key),
                                                                                       key=key)]

        state.tables.append({'options': self.options,
                             'unknowns': unk_group,
                             'blanks': blank_group,
                             'airs': air_group})

#
# class TableOptions(HasTraits, PersistenceMixin):
#     pass
#
#
# class AnalysisTableOptions(TableOptions):
#     references_enabled = Bool(False)
#
#
# class TableColumn(HasTraits):
#     name = Str
#     display = Bool(True)
#     sigfigs = Str
#     key = Str
#
#
# class InterpretedAgeTableOptions(TableOptions):
#     columns = List(dump=True)
#     kca_nsigma = Enum(1, 2, 3, dump=True)
#     age_nsigma = Enum(1, 2, 3, dump=True)
#
#     def __init__(self, *args, **kw):
#         super(InterpretedAgeTableOptions, self).__init__(*args, **kw)
#         self.persistence_path = os.path.join(paths.hidden_dir, 'interpreted_age_table_options.p')
#
#     def _kca_nsigma_default(self):
#         return 2
#
#     def _age_nsigma_default(self):
#         return 2
#
#     @property
#     def column_labels(self):
#         return [c.name for c in self.columns if c.display]
#
#     @property
#     def column_keys(self):
#         return [c.key for c in self.columns if c.display]
#
#     @property
#     def column_sigfigs(self):
#         return [int(c.sigfigs) for c in self.columns if c.sigfigs]
#
#     def _columns_default(self):
#         cs = (('Sample', 'sample', ''),
#               ('Identifier', 'identifier', ''),
#               ('Material', 'material', ''),
#               ('Irradiation', 'irradiation', ''),
#               ('Age Kind', 'age_kind', ''),
#               ('MSWD', 'mswd', 3),
#               ('K/Ca', 'kca', 3),
#               ('K/Ca Error', 'kca_err', 3),
#               ('N', 'nanalyses', ''),
#               ('Age', 'display_age', 3),
#               ('Age Error', 'display_age_err', 3),
#               )
#
#         cols = [TableColumn(name=attr, key=key, sigfigs=str(sigfigs)) for attr, key, sigfigs in cs]
#         return cols
#
#     def traits_view(self):
#         cols = [ObjectColumn(name='name', editable=False),
#                 CheckboxColumn(name='display'),
#                 ObjectColumn(name='sigfigs')]
#
#         sigma = VGroup(Item('age_nsigma'), Item('kca_nsigma'))
#
#         v = View(VGroup(UItem('columns', editor=TableEditor(columns=cols, sortable=False)),
#                         sigma,
#                         ),
#                  title='Interpreted Age Table Options',
#                  resizable=True,
#                  height=500,
#                  width=300,
#                  buttons=['OK', 'Cancel'])
#         return v
#
#
# # ==================================================
#
#
# class TableNode(BaseNode):
#     pass
#     # options = Instance(TableOptions)
#
#     # def configure(self, pre_run=False, **kw):
#     #     if not pre_run:
#     #         self._manual_configured = True
#     #
#     #     return self._configure(self.options)
#
#     # def _options_default(self):
#     #     return self.options_klass()
#
#
# class AnalysisTableNode(TableNode):
#     name = 'Analysis Table'
#     options_klass = AnalysisTableOptions
#
#     auto_configure = False
#
#     def run(self, state):
#         if state.unknowns:
#             self._make_unknowns_table(state)
#
#         # if self.options.references_enabled and state.references:
#         #     self._make_references_table(state.references)
#
#     def _make_unknowns_table(self, state):
#         items = state.unknowns
#
#         editor_klass = FusionTableEditor
#         editor = editor_klass()
#
#         # editor.make_records(items)
#         editor.items = items
#
#         state.editors.append(editor)
#
#     # def _make_references_table(self, items):
#     #     pass
#
#
# class InterpretedAgeTableNode(TableNode):
#     name = 'Interpreted Age Table'
#     options_klass = InterpretedAgeTableOptions
#
#     def finish_configure(self):
#         if self.options:
#             self.options.dump()
#
#     def _options_factory(self):
#         op = super(InterpretedAgeTableNode, self)._options_factory()
#         op.load()
#         return op
#
#     def run(self, state):
#         editor = InterpretedAgeTableEditor()
#
#         ta = editor.tabular_adapter
#         cols = [c for c in ta.columns if c[1] in self.options.column_keys]
#         if cols:
#
#             ta.kca_nsigma = self.options.kca_nsigma
#             ta.display_age_nsigma = self.options.age_nsigma
#
#             for i, c in enumerate(cols):
#                 if c[1] == 'kca_err':
#                     cols[i] = (PLUSMINUS_NSIGMA.format(self.options.kca_nsigma), 'kca_err')
#                 elif c[1] == 'display_age_err':
#                     cols[i] = (PLUSMINUS_NSIGMA.format(self.options.age_nsigma), 'display_age_err')
#
#             for c, si in zip(cols, self.options.column_sigfigs):
#                 attr = '{}_sigfigs'.format(c[1])
#                 if hasattr(ta, attr):
#                     setattr(ta, attr, si)
#
#             ta.columns = cols
#
#         editor.interpreted_ages = state.interpreted_ages
#         state.editors.append(editor)

# ============= EOF =============================================
