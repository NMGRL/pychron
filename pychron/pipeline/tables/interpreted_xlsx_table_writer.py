# ===============================================================================
# Copyright 2017 ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.stats import calculate_weighted_mean
from pychron.pipeline.tables.xlsx_table_writer import XLSXTableWriter


class InterpretedAgeXLSTableWriter(XLSXTableWriter):
    def build(self, p, ias, title=None, adapter=None, options=None):
        self._new_workbook(p)

        self._write_summary_sheet(ias, title, adapter, options)
        # options = self.options
        # if options.use_sample_sheets:
        #     for gi in groups:
        #         # for sam, ais in self._group_samples(ans):
        #         sh = self._add_sample_sheet(wb, gi.sample)
        #         #                 ais = list(ais)
        #
        #         #                 self._add_metadata(sh, ais[0])
        #         self._add_header_row(sh, 0)
        #         self._add_analyses(sh, gi.analyses, start=2)
        # else:
        #     # if use_summary_sheet:
        #     # self._write_summary_sheet(wb, groups)
        #
        #     sh = wb.add_sheet('ArArData')
        #     start = 2
        #     for i, gi in enumerate(groups):
        #         if i == 0:
        #             self._add_header_row(sh, 0)
        #
        #         self._add_analyses(sh, gi.analyses, start=start)
        #         start += len(gi.analyses) + 1

        self._workbook.close()

    def _write_summary_sheet(self, ias, title, adapter, options):
        # def set_nsigma(nattr):
        #     def f(item, attr):
        #         return getattr(item, attr) * getattr(self.options,
        #                                              '{}_nsigma'.format(nattr))
        #
        #     return f

        sh = self._workbook.add_worksheet('Summary')
        if options:
            sh.show_grid = options.show_grid
            sh.show_outline = options.show_outline
        # cols = [('Sample', 'sample'),
        #         ('Identifier', 'identifier'),
        #         ('Irradiation', 'irradiation'),
        #         ('Material', 'material'),
        #         ('Age Type', 'age_kind'),
        #         ('MSWD', 'mswd'),
        #         ('N', 'nanalyses'),
        #         ('K/Ca', 'kca'),
        #         # (u'{}\u03c3'.format(self.options.kca_nsigma),
        #         # 'kca_err', set_nsigma('kca')),
        #
        #         ('Age', 'display_age'),
        #         # (u'{}\u03c3'.format(self.options.age_nsigma),
        #         #  'age_err', set_nsigma('age')),
        #         ]
        cols = adapter.columns
        start = 0
        if title:
            self._add_title_row(0, sh, title)
            start = 1

        self._add_summary_header_row(start, sh, cols)
        start += 2
        for i, ia in enumerate(ias):
            r = i + start
            self._add_summary_row(sh, ia, r, cols, adapter)

        if options.include_weighted_mean:
            vs, es = zip(*((ia.age, ia.age_err) for ia in ias if not ia.is_omitted()))

            wm, we = calculate_weighted_mean(vs, es)
            print wm, we
            sh.write(r + 2, 0, 'Weighted Mean')
            sh.write(r + 2, 2, wm)
            sh.write(r + 2, 3, we)

    def _add_title_row(self, row, sh, title):
        # sh.write(row, 0, title)
        sh.merge_range(row, 0, row, 9, title)

    def _add_summary_header_row(self, start, sh, cols):
        # s1, s2 = self._get_header_styles()
        # header_style = self._get_header_style()
        for i, ci in enumerate(cols):
            # sh.write(start, i, ci[0], style=header_style)
            sh.write(start, i, ci[0])

    def _add_summary_row(self, sh, ia, row, cols, adapter):
        for j, c in enumerate(cols):
            attr = c[1]
            if len(c) == 3:
                getter = c[2]
            else:
                getter = getattr

            txt = getter(ia, attr)
            # if isinstance(txt, float):
            #     if attr == 'kca_err':
            #         txt *= adapter.kca_nsigma
            #     elif attr == 'display_age_err':
            #         txt *= adapter.display_age_nsigma
            #
            #     style = self._style_factory()
            #
            #     fmt = '0' * getattr(adapter, '{}_sigfigs'.format(attr))
            #     style.num_format_str = '0.{}'.format(fmt)
            # else:
            #     style = self.default_style

            sh.write(row, j, txt)
            # sh.write(row, j, txt, style)

# ============= EOF =============================================
