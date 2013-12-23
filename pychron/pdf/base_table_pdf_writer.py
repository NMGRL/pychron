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
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pdf.base_pdf_writer import BasePDFWriter
from pychron.pdf.options import PDFTableOptions


class BasePDFTableWriter(BasePDFWriter):
    col_widths = None
    _options_klass = PDFTableOptions

    def _get_idxs(self, rows, klass):
        return [(i, v) for i, v in enumerate(rows)
                if isinstance(v, klass)]

    def _new_line(self, style, idx, weight=1.5,
                  start=0, end=-1,
                  color='black',
                  cmd='LINEBELOW'):

        style.add(cmd, (start, idx), (end, idx),
                  weight, getattr(colors, color))

    def _new_table(self, style, data, hAlign='LEFT',
                   col_widths=None, extend_last=False, *args, **kw):

        # set spans

        for idx, ri in enumerate(data):
            for s, e in ri.spans:
                style.add('SPAN', (s, idx), (e, idx))

        # render rows
        rows = [di.render() if hasattr(di, 'render') else di
                for di in data]

        t = Table(rows, hAlign=hAlign,
                  style=style,
                  *args, **kw)

        self._set_col_widths(t, rows, col_widths)
        self._set_row_heights(t, data)

        return t

    def _new_style(self, header_line_idx=None, header_line_width=1,
                   header_line_color='black',
                   debug_grid=False):

        ts = TableStyle()
        if debug_grid:
            ts.add('GRID', (0, 0), (-1, -1), 1, colors.red)

        if isinstance(header_line_color, str):
            try:
                header_line_color = getattr(colors, header_line_color)
            except AttributeError:
                header_line_color = colors.black

        if header_line_idx is not None:
            ts.add('LINEBELOW', (0, header_line_idx),
                   (-1, header_line_idx),
                   header_line_width, header_line_color)

        return ts

    def _set_row_heights(self, t, data):
        pass

    def _set_col_widths(self, t, rows, col_widths):
        cs = col_widths
        if cs is None:
            cs = self.col_widths

        if cs:
            cn = len(cs)
            dn = max([len(di) for di in rows])
            #             dn = len(data[0])
            if cn < dn:
                cs.extend([30 for _ in range(dn - cn)])

            t._argW = cs






#============= EOF =============================================

