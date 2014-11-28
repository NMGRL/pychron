# ===============================================================================
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
# ===============================================================================

#============= enthought library imports =======================
import os
import cPickle as pickle

from traits.api import Str
from traitsui.api import View, UItem


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.processing.tasks.tables.editors.base_table_editor import BaseTableEditor
from pychron.processing.tasks.tables.editors.summary_adapter import SummaryTabularAdapter
from pychron.processing.tables.summary_table_pdf_writer import SummaryPDFTableWriter


class SummaryTableEditor(BaseTableEditor, ColumnSorterMixin):
    notes_template = Str

    def make_table(self, title):
        samples = self.items
        uab = self.use_alternating_background
        t = SummaryPDFTableWriter(
                                  use_alternating_background=uab,
                                  notes_template=self.notes_template
                                  )

        t.col_widths = self._get_column_widths()

#        p = '/Users/ross/Sandbox/aaasumtable.pdf'
        p = self._get_save_path()
        if p:
            t.build(p, samples, title=title)
            # dump our col widths
            self._dump_widths()

            return p

    def _get_column_widths(self):
        cs = []
        ac = map(lambda x: x * 0.6, self.col_widths)
        cs.extend(ac)

        return cs

    def _load_widths(self):
        p = os.path.join(paths.hidden_dir, 'summary_col_widths')
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    return pickle.load(fp)
                except Exception, e :
                    print 'load_widths', e

    def _dump_widths(self):
        p = os.path.join(paths.hidden_dir, 'summary_col_widths')
        with open(p, 'w') as fp:
            pickle.dump(self.col_widths, fp)

    def traits_view(self):

        adapter = SummaryTabularAdapter()
        widths = self._load_widths()
        if widths:
            adapter.set_widths(widths)

        v = View(UItem('items', editor=myTabularEditor(
                                                      adapter=adapter,
                                                      editable=True,
                                                      operations=['delete', 'move'],
                                                      col_widths='col_widths',
                                                      selected='selected',
                                                      multi_select=True,
                                                      refresh='refresh_needed',
                                                      column_clicked='column_clicked'
                                                      )))
        return v


# ============= EOF =============================================
