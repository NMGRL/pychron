#===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tables.fusion.csv_writer import FusionTableCSVWriter
from pychron.processing.tables.fusion.pdf_writer import FusionPDFTableWriter
from pychron.processing.tables.fusion.xls_writer import FusionTableXLSWriter
from pychron.processing.tasks.tables.editors.arar_table_editor import ArArTableEditor
from pychron.processing.tasks.tables.editors.fusion.fusion_adapter import FusionTableAdapter, FusionGroupTableAdapter


class FusionTableEditor(ArArTableEditor):
    pdf_writer_klass = FusionPDFTableWriter
    xls_writer_klass = FusionTableXLSWriter
    csv_writer_klass = FusionTableCSVWriter
    adapter_klass = FusionTableAdapter
    analysis_groups_adapter_klass = FusionGroupTableAdapter
    extract_label = 'Power'
    extract_units = 'W'

#
#class FusionTableEditor(BaseTableEditor, ColumnSorterMixin):
#    means = Property(List, depends_on='items[]')
#    #show_blanks = Bool(False)
#
#    #     refresh_means = Event
#
#    def _items_items_changed(self):
#        self.refresh_needed = True
#
#    def make_pdf_table(self, title, path=None):
#        from pychron.processing.tables.fusion.pdf_writer import FusionTablePDFWriter
#
#        ans = self._clean_items()
#        t = FusionTablePDFWriter(
#            orientation='landscape',
#            use_alternating_background=self.use_alternating_background)
#
#        t.col_widths = self._get_column_widths()
#        means = self.means
#        path = self._get_save_path(path)
#        #         p = '/Users/ross/Sandbox/aaaatable.pdf'
#        if path:
#            key = lambda x: x.sample
#            ans = groupby(ans, key=key)
#            t.build(path, ans, means, title=title)
#            return path
#
#    def make_xls_table(self, title, path=None):
#        ans = self._clean_items()
#        means = self.means
#        from pychron.processing.tables.fusion.xls_writer import LaserTableXLSWriter
#
#        t = LaserTableXLSWriter()
#        path = self._get_save_path(path, ext='.xls')
#        #         p = '/Users/ross/Sandbox/aaaatable.xls'
#        if path:
#            t.build(path, ans, means, title)
#            return path
#
#    def make_csv_table(self, title, path=None):
#        ans = self._clean_items()
#        means = self.means
#        from pychron.processing.tables.fusion.csv_writer import LaserTableCSVWriter
#
#        t = LaserTableCSVWriter()
#
#        #         p = '/Users/ross/Sandbox/aaaatable.csv'
#        path = self._get_save_path(path, ext='.csv')
#        if path:
#            t.build(path, ans, means, title)
#            return path
#
#    def _get_column_widths(self):
#        '''
#            exclude the first column from col widths
#            it is displaying in pychron but not in the pdf
#        '''
#        status_width = 6
#
#        ac = map(lambda x: x * 0.6, self.col_widths[1:])
#        cs = [status_width]
#        cs.extend(ac)
#
#        return cs
#
#    @cached_property
#    def _get_means(self):
#        key = lambda x: x.sample
#        ans = self._clean_items()
#        ms = [
#            Mean(analyses=list(ais),
#                 sample=sam
#            )
#            for sam, ais in groupby(ans, key=key)]
#        return ms
#
#    #         return [Mean(analyses=self._clean_items()), ]
#
#    #def refresh_blanks(self):
#    #    self._show_blanks_changed(self.show_blanks)
#    #
#    #def _show_blanks_changed(self, new):
#    #    if new:
#    #        self.items = self.oitems
#    #    else:
#    #        self.items = self._clean_items()
#
#    def traits_view(self):
#        v = View(
#            #HGroup(spring, Item('show_blanks')),
#            UItem('items',
#                  editor=myTabularEditor(adapter=LaserTableAdapter(),
#                                         #                                               editable=False,
#                                         col_widths='col_widths',
#                                         selected='selected',
#                                         multi_select=True,
#                                         auto_update=False,
#                                         operations=['delete', 'move'],
#                                         column_clicked='column_clicked'
#                                         #                                               auto_resize=True,
#                                         #                                               stretch_last_section=False
#                  )
#
#            ),
#            UItem('means',
#                  editor=myTabularEditor(adapter=LaserTableMeanAdapter(),
#                                         #                                              auto_resize=True,
#                                         editable=False,
#                                         auto_update=False,
#                                         refresh='refresh_needed'
#                  )
#            )
#
#
#        )
#        return v

#============= EOF =============================================
