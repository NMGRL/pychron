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

# ============= enthought library imports =======================
from itertools import groupby

from traits.api import Property, List, cached_property, Str
from traitsui.api import View, UItem, Item, VGroup, HGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.helpers.formatting import floatfmt
from pychron.processing.analyses.analysis_group import AnalysisGroup
from pychron.pipeline.editors.base_table_editor import BaseTableEditor
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.pychron_constants import ARGON_KEYS


class ArArRecordView:
    pass


class ArArTableEditor(BaseTableEditor, ColumnSorterMixin):
    analysis_groups = Property(List, depends_on='items[]')
    pdf_writer_klass = None
    xls_writer_klass = None
    csv_writer_klass = None

    analysis_group_klass = AnalysisGroup
    adapter_klass = None
    analysis_groups_adapter_klass = None
    extract_label = Str
    extract_units = Str

    title = Str('Table X. Ar/Ar Analyses')

    def make_records(self, items):
        record_factory = self._record_factory
        records = [record_factory(i) for i in items]

        self.records = records

    def _record_factory(self, item):
        record = ArArRecordView()
        record.record_id = item.record_id
        record.extract_value = item.extract_value
        record.age = floatfmt(nominal_value(item.age), n=4)
        record.age_err = floatfmt(item.age_err_wo_j, n=4)

        record.kca = floatfmt(nominal_value(item.kca), n=2)
        record.kca_err = floatfmt(std_dev(item.kca), n=3)
        record.rad40_percent = floatfmt(nominal_value(item.rad40_percent))

        for attr in ARGON_KEYS:
            v = item.isotopes[attr].get_intensity()
            vv = floatfmt(nominal_value(v), n=3)
            setattr(record, attr, vv)
            ve = floatfmt(std_dev(v), n=3)
            setattr(record, '{}_err'.format(attr), ve)

        return record

    # def _items_items_changed(self):
    #     self.refresh_needed = True

    def _writer_factory(self, klass, **kw):
        kw['extract_label'] = self.extract_label
        kw['extract_units'] = self.extract_units

        return klass(**kw)

    def make_pdf_table(self, title, path):

        ans = self._clean_items()
        t = self._writer_factory(self.pdf_writer_klass,
                                 # orientation='landscape',
                                 use_alternating_background=self.use_alternating_background)

        t.col_widths = self._get_column_widths()
        groups = self.analysis_groups

        # path = '/Users/ross/Sandbox/aaaatable.pdf'
        # path = self._get_save_path(path)

        if path:
            key = lambda x: x.sample
            ans = groupby(ans, key=key)
            t.build(path, ans, groups, title=title)
            return path

    def make_xls_table(self, option):
        # ans = self._clean_items()
        means = self.analysis_groups

        t = self._writer_factory(self.xls_writer_klass)
        # path = self._get_save_path(path, ext='.xls')
        #         p = '/Users/ross/Sandbox/aaaatable.xls'
        if option.path:
            t.build(option.path, means, title=self._generate_title())
            return option.path

    def make_csv_table(self, title, path):
        ans = self._clean_items()
        means = self.analysis_groups

        t = self._writer_factory(self.csv_writer_klass)

        #         p = '/Users/ross/Sandbox/aaaatable.csv'
        # path = self._get_save_path(path, ext='.csv')
        if path:
            t.build(path, ans, means, title)
            return path

    def _generate_title(self):
        return self.title

    def _get_column_widths(self):
        """
            exclude the first column from col widths
            it is displaying in pychron but not in the pdf
        """
        status_width = 6

        ac = map(lambda x: x * 0.6, self.col_widths[1:])
        cs = [status_width]
        cs.extend(ac)

        return cs

    @cached_property
    def _get_analysis_groups(self):
        ans = self._clean_items()
        key = lambda x: x.group_id
        ans = sorted(ans, key=key)
        ms = [self.analysis_group_klass(analyses=list(ais))
              for gid, ais in groupby(ans, key=key)]
        return ms

    def traits_view(self):
        v = View(VGroup(
            HGroup(Item('title')),
            UItem('records',
                  editor=myTabularEditor(adapter=self.adapter_klass(),
                                         #                                               editable=False,
                                         col_widths='col_widths',
                                         selected='selected',
                                         multi_select=True,
                                         auto_update=False,
                                         operations=['delete', 'move'],
                                         column_clicked='column_clicked')),
            UItem('analysis_groups',
                  editor=myTabularEditor(adapter=self.analysis_groups_adapter_klass(),
                                         #                                              auto_resize=True,
                                         editable=False,
                                         auto_update=False,
                                         refresh='refresh_needed'))))
        return v

        # ============= EOF =============================================
