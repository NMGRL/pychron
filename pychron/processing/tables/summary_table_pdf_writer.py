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
from traits.api import Int, Str
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pdf.base_pdf_writer import BasePDFWriter
from pychron.helpers.formatting import floatfmt
from pychron.pdf.items import Row, FootNoteRow, FooterRow
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
from pychron.paths import paths
import yaml

def DefaultInt(value=40):
    return Int(value)



class SummaryTablePDFWriter(BasePDFWriter):
    notes_template = Str('summary_table.temp')

    def _build(self, doc, samples, title):

        title_para = self._new_paragraph(title)
        flowables = [title_para, self._vspacer(0.1)]

#         t, t2 = self._make_table(samples)
        t = self._make_table(samples)
        flowables.append(t)
        flowables.append(self._vspacer(0.1))
#         flowables.append(t2)
#         n = self._make_notes()
#         flowables.append(n)

        return flowables, None

    def _short_material_name(self, mat):
        if mat.lower() == 'groundmass concentrate':
            mat = 'GMC'

        return mat

    def _make_table(self, interpreted_ages):
        style = self._new_style(header_line_idx=1)

        style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
        style.add('LEFTPADDING', (0, 0), (-1, -1), 1)
        self._new_line(style, 0, cmd='LINEABOVE')

        data = []

        # make header
        header = self._make_header(style)
        data.extend(header)

        cnt = len(data)
        for i, sam in enumerate(interpreted_ages):

            r = self._make_interpreted_age_row(sam)
            data.append(r)

            if self.use_alternating_background:
                idx = cnt + i
                if i % 2 != 0:
                    style.add('BACKGROUND', (0, idx), (-1, idx),
                              colors.lightgrey)

        idx = len(data) - 1
        self._new_line(style, idx)

        self._make_notes(data, style)

        t = self._new_table(style, data,
                            repeatRows=3)
        return t

    def _make_header(self, style):
        PMS = u'\u00b1 1\u03c3'

        pr = Row()
        pr.add_blank_item(6)
        pr.add_item(value='Preferred Age', span=-1)
#         style.add('ALIGN', (0, 3), (0, -1), 'CENTER')
        self._new_line(style, 0, weight=0.75, start=4, end=-1)

        r = Row()

        r.add_item(value='Sample')
        r.add_item(value='L#')
        r.add_item(value='Irrad')
        r.add_item(value='Material')

        r.add_item(value='Type')
        r.add_item(value='N')
        r.add_item(value='MSWD')
        r.add_item(value='K/Ca')
        r.add_item(value=PMS)
        r.add_item(value='Age')
        r.add_item(value=PMS)

        return (pr, r,)

    def _make_interpreted_age_row(self, interpreted_age):
        row = Row()
        row.add_item(value=interpreted_age.sample)
        row.add_item(value=interpreted_age.identifier)
        row.add_item(value=interpreted_age.irradiation)
        row.add_item(value=self._short_material_name(interpreted_age.material))
        row.add_item(value=interpreted_age.kind)
        row.add_item(value=interpreted_age.nanalyses)
        row.add_item(value=floatfmt(interpreted_age.mswd, n=1))
        # row.add_item(value=self._value(n=1)(interpreted_age.weighted_kca))
        # row.add_item(value=self._error(n=1)(interpreted_age.weighted_kca))
        # row.add_item(value=self._value(n=4)(interpreted_age.weighted_age))
        # row.add_item(value=self._error(n=4)(interpreted_age.weighted_age))

        return row

    def _set_row_heights(self, table, data):
        a_idxs = self._get_idxs(data, (FooterRow, FootNoteRow))
        for a, v in a_idxs:
            table._argH[a] = 0.19 * inch

        idx = self._get_idxs(data, Row)
        for i, v in idx:
            if v.height:
                table._argH[i] = v.height * inch

#===============================================================================
# summary
#===============================================================================
    def _make_notes(self, data, style):
        p = os.path.join(paths.template_dir, self.notes_template)

        if os.path.isfile(p):
            with open(p, 'r') as fp:
                meta = ''
                for li in fp:
                    if li.startswith('#-----------'):
                        break

                    meta += li
                meta = yaml.load(meta)
                txt = ''
                for li in fp:
                    txt += li

            size = meta.get('fontsize', 5)
            leading = meta.get('leading', 5)
            bgcolor = meta.get('bgcolor', None)

            p = self._new_paragraph(txt, leading=leading)
            r = Row(fontsize=size)
            r.add_item(value=p, span=-1)
            data.append(r)
            if bgcolor:
                bgcolor = bgcolor.replace(' ', '')
                if hasattr(colors, bgcolor):
                    idx = len(data) - 1
                    style.add('BACKGROUND', (0, idx), (-1, idx),
                          getattr(colors, bgcolor),
                          )

#===============================================================================
# footnotes
#===============================================================================
#     def _make_footnote_rows(self, data, style):
#         return
#
#         data.append(Row(height=0.1))
#         def factory(f):
#             r = FootNoteRow(fontsize=6)
#             r.add_item(value=f)
#             return r
#         data.extend([factory(fi) for fi in self._footnotes])
#
# #         _get_idxs = lambda x: self._get_idxs(rows, x)
#         _get_se = lambda x: (x[0][0], x[-1][0])
#         # set for footnot rows
#         footnote_idxs = self._get_idxs(data, FootNoteRow)
#         sidx, eidx = _get_se(footnote_idxs)
#         style.add('VALIGN', (0, sidx), (-1, eidx), 'MIDDLE')
#         for idx, _v in footnote_idxs:
#             style.add('SPAN', (0, idx), (-1, idx))
# #            style.add('VALIGN', (1, idx), (-1, idx), 'MIDDLE')

#===============================================================================
#
#===============================================================================

#============= EOF =============================================
# class TableSpec(HasTraits):
#     status_width = Int(5)
#     id_width = Int(20)
#     power_width = Int(30)
#     moles_width = Int(50)
#
#
#     ar40_width = DefaultInt(value=45)
#     ar40_error_width = DefaultInt()
#     ar39_width = DefaultInt(value=45)
#     ar39_error_width = DefaultInt()
#     ar38_width = DefaultInt()
#     ar38_error_width = DefaultInt()
#     ar37_width = DefaultInt()
#     ar37_error_width = DefaultInt()
#     ar36_width = DefaultInt()
#     ar36_error_width = DefaultInt(value=50)
