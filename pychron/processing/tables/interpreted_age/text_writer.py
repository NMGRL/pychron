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
# ============= standard library imports ========================
from xlwt import XFStyle


# ============= local library imports  ==========================


class InterpretedAgeTextWriter(object):
    def build(self, p, ias, title=None, adapter=None, options=None):
        wb = self._new_workbook()
        self._write_summary_sheet(wb, ias, title, adapter, options)
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

        wb.save(p)

    def _write_summary_sheet(self, wb, ias, title, adapter, options):
        # def set_nsigma(nattr):
        #     def f(item, attr):
        #         return getattr(item, attr) * getattr(self.options,
        #                                              '{}_nsigma'.format(nattr))
        #
        #     return f

        sh = wb.add_sheet('Summary')
        if options:
            sh.show_grid = options.show_grid
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
        start += 1
        for i, ia in enumerate(ias):
            self._add_summary_row(sh, ia, i + start, cols, adapter)

    def _add_title_row(self, row, sh, title):
        sh.write(row, 0, title)
        sh.merge(row, row, 0, 9)

    def _add_summary_header_row(self, start, sh, cols):
        s1, s2 = self._get_header_styles()
        for i, ci in enumerate(cols):
            sh.write(start, i, ci[0], style=s2)

    def _add_summary_row(self, sh, ia, row, cols, adapter):
        for j, c in enumerate(cols):
            attr = c[1]
            if len(c) == 3:
                getter = c[2]
            else:
                getter = getattr

            txt = getter(ia, attr)
            if isinstance(txt, float):
                if attr == 'kca_err':
                    txt *= adapter.kca_nsigma
                elif attr == 'display_age_err':
                    txt *= adapter.display_age_nsigma

                style = XFStyle()
                fmt = '0' * getattr(adapter, '{}_sigfigs'.format(attr))
                style.num_format_str = '0.{}'.format(fmt)
            else:
                style = self.default_style

            sh.write(row, j, txt, style)

# ============= EOF =============================================
