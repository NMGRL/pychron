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
import re

from reportlab.pdfbase.pdfmetrics import stringWidth
from traits.api import Int

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pdf.items import Row, FootNoteRow, FooterRow
from reportlab.lib import colors
from pychron.processing.tables.pdf_writer import IsotopePDFTableWriter


def DefaultInt(value=40):
    return Int(value)


regex = re.compile(r'>[\w\.\(\)\/]+<')


def extract_text(txt):
    t = 0
    for e in regex.finditer(txt):
        t += len(e.group(0)[1:-1])

    return 'X' * t


class StepHeatPDFTableWriter(IsotopePDFTableWriter):
    def _make_table(self, group,
                    double_first_line=True,
                    include_footnotes=False):

        self._ref = group.analyses[0]
        analyses = group.all_analyses

        style = self._new_style(debug_grid=False)

        style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
        style.add('LEFTPADDING', (0, 0), (-1, -1), 1)
        style.add('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        style.add('BOTTOMPADDING', (0, 0), (-1, -1), 1)
        #style.add('RIGHTPADDING', (0, 0), (-1, -1), 5)

        if double_first_line:
            self._new_line(style, 0, weight=2.5, cmd='LINEABOVE')
        else:
            self._new_line(style, 0, cmd='LINEABOVE')

        data = []
        bdata = []
        #set extract units/label before making meta rows
        if analyses[0].extract_device == 'Furnace':
            self.extract_label = 'Temp'
            self.extract_units = 'C'
        else:
            self.extract_label = 'Power'
            self.extract_units = 'W'

        # make meta
        meta = self._make_meta(analyses, style,
                               include_footnotes=include_footnotes)
        data.extend(meta)

        units = self._get_signal_units(analyses)
        scales = self._get_signal_scales(analyses)
        # make header
        headers = self._make_header(style, signal_units=units)
        data.extend(headers)

        cnt = len(data)

        group.calculate_plateau()
        plateau_bounds = group.plateau_steps
        if plateau_bounds:
            lb, hb = plateau_bounds

        for i, ai in enumerate(analyses):

            is_plat_step = False
            if plateau_bounds:
                is_plat_step = i >= lb and i <= hb

            r = self._make_analysis_row(ai, is_plat_step, scales)
            data.append(r)

            if self.options.use_alternating_background:
                idx = cnt + i
                if idx % 2 == 0:
                    style.add('BACKGROUND', (0, idx), (-1, idx), self.options.alternating_background)

        idx = len(data) - 1
        self._new_line(style, idx)
        s = self._make_summary_rows(group, idx + 1, style)
        data.extend(s)

        auto_col_widths = True
        if auto_col_widths:
            self._calculate_col_widths(data[2:])

        t = self._new_table(style, data, repeatRows=4)

        fdata = []

        style = self._new_style(debug_grid=False)
        style.add('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey)
        style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
        style.add('LEFTPADDING', (0, 0), (-1, -1), 2)
        style.add('RIGHTPADDING', (0, 0), (-1, -1), 0)

        if include_footnotes:
            self._make_footnote_rows(fdata, style)
            self._make_footer_rows(fdata, style)

            ft = self._new_table(style, fdata)
            return t, ft
        else:
            return t,

    def _make_analysis_row(self, analysis, is_plateau_step, scales):
        value = self._value
        error = self._error

        analysis.is_plateau_step = is_plateau_step
        attrs = (
            #('temp_status', lambda x: '' if x == 0 else 'X'),
            ('is_plateau_step', lambda x: '<b>P</b>' if x else ''),
            ('aliquot_step_str', '{}',),
            ('extract_value', '{}'),
            ('moles_Ar40', value(scale=1e-16, n=1)),

            # ==============================================================
            # signals
            # ==============================================================
            ('Ar40', value(scale=scales['Ar40'])),
            ('Ar40', error(scale=scales['Ar40err'])),
            ('Ar39', value(scale=scales['Ar39'])),
            ('Ar39', error(scale=scales['Ar39err'])),
            ('Ar38', value(scale=scales['Ar38'])),
            ('Ar38', error(scale=scales['Ar38err'])),
            ('Ar37', value(scale=scales['Ar37'])),
            ('Ar37', error(scale=scales['Ar37err'])),
            ('Ar36', value(scale=scales['Ar36'])),
            ('Ar36', error(scale=scales['Ar36err'])),

            # ==============================================================
            # computed
            # ==============================================================


            # ('F', value(n=5)),
            ('kca', value(n=1)),
            ('kca', error(n=2, s=1)),
            ('rad40_percent', value(n=1)),
            ('uage', value(n=2)),
            ('age_err_wo_j', error(n=2)),
        )
        default_fontsize = 6

        row = self._new_row(analysis, attrs, default_fontsize)

        # battrs = (
        #     # ==============================================================
        #     # blanks
        #     # ==============================================================
        #     #                     ('', '{}'),
        #     #                     ('', '{}'),
        #     ('', '{}'),
        #     ('', '{}'),
        #     #                     ('blank_fit', '{}'),
        #     ('Ar40', value(scale=1e3)),
        #     ('Ar39', value(scale=1e3)),
        #     ('Ar38',),
        #     ('Ar37',),
        #     ('Ar36', value(scale=1e-2)),
        #     #
        # )
        #
        # # blankrow = Row(fontsize=default_fontsize)
        # for args in battrs:
        #     efmt = self._error()
        #     vfmt = self._value()
        #
        #     if len(args) == 2:
        #         attr, vfmt = args
        #     elif len(args) == 3:
        #         attr, vfmt, efmt = args
        #     else:
        #         attr = args[0]
        #
        #     s, e = '', ''
        #     if attr:
        #         iso = analysis.isotopes.get(attr)
        #         if iso:
        #             v = iso.blank.uvalue
        #
        #             s = vfmt(v)
        #
        #             s = self._new_paragraph('<i>{}</i>'.format(s))
        #
        #             e = efmt(v)
        #             e = self._new_paragraph('<i>{}</i>'.format(e))
        #
        #     blankrow.add_item(value=s)
        #     blankrow.add_item(value=e)

        return row

        # def _set_row_heights(self, table, data):
        #
        #     a_idxs = self._get_idxs(data, (FooterRow, FootNoteRow))
        #     for a, v in a_idxs:
        #         table._argH[a] = 0.19 * inch
        #
        #     idx = self._get_idxs(data, Row)
        #     for i, v in idx:
        #         if v.height:
        #             table._argH[i] = v.height * inch


        # ===============================================================================
        # summary
        # ===============================================================================

    def _make_summary_rows(self, agroup, idx, style):
        span = 14
        height = 0.12
        fontsize = 6

        wtd_mean_row = Row(fontsize=fontsize, height=height)
        wtd_mean_row.add_item(value='<b>Weighted Mean Age</b>', span=span, include_width_calc=False)
        #wtd_mean_row.add_blank_item(n=10)

        wa = agroup.weighted_age
        s = u'{} \u00b1{}'.format(self._value(n=2)(wa), self._error(n=2)(wa))
        wtd_mean_row.add_item(value=s, span=-1, include_width_calc=False)

        inta = agroup.integrated_age
        int_row = Row(fontsize=fontsize, height=height)
        int_row.add_item(value='<b>Integrated</b>', span=span, include_width_calc=False)

        s = u'{} \u00b1{}'.format(self._value(n=2)(inta), self._error(n=2)(inta))
        int_row.add_item(value=s, span=-1, include_width_calc=False)
        #int_row.add_item(value=self._value()(inta))
        #int_row.add_item(value=u' \u00b1{}'.format(self._error()(inta)))

        plat_row = Row(fontsize=fontsize, height=height)
        plat_row.add_item(value='<b>Plateau</b>', span=span - 2, include_width_calc=False)

        s = ''
        pa = agroup.plateau_age

        if agroup.plateau_steps:
            plat_row.add_item(value='<b>Steps</b>')
            plat_row.add_item(value=agroup.plateau_steps_str)

            s = u'{} \u00b1{}'.format(self._value(n=2)(pa), self._error(n=2)(pa))

        plat_row.add_item(value=s, span=-1, include_width_calc=False)

        rows = [wtd_mean_row, int_row, plat_row]
        include_isochron = False
        if include_isochron:
            iso_row = Row(fontsize=fontsize, height=height)
            iso_row.add_item(value='<b>Isochron</b>', span=span, include_width_calc=False)

            isoa = agroup.isochron_age
            s = u'{} \u00b1{}'.format(self._value(n=2)(isoa), self._error(n=2)(isoa))
            iso_row.add_item(value=s, span=-1, include_width_calc=False)
            rows.append(iso_row)

        return rows

    # ===============================================================================
    # blanks
    # ===============================================================================

    # ===============================================================================
    # footnotes
    # ===============================================================================
    def _calculate_span(self, p, start, fontName=None, fontSize=None):
        """
            determine number of columns required
        """
        cs = self.col_widths[start:]
        if fontName is None:
            fontName = p.frags[0].fontName

        if fontSize is None:
            fontSize = p.frags[0].fontSize

        txt_w = stringWidth(p.text, fontName, fontSize)

        cols_w = 0
        for i, ci in enumerate(cs):
            cols_w += ci
            self.debug((i, ci, txt_w, fontSize))
            if cols_w > txt_w:
                break

        return i + 1

    def _make_footnote_rows(self, data, style):
        data.append(Row(height=0.1))
        blanks = self._get_average_blanks()
        fontsize = 6
        height = self.footnote_height
        if blanks:
            co2_blanks, furnace_blanks = blanks
            average_furnace_blanks = 'Average blanks for Furnace: ({Ar40:0.3f}, {Ar39:0.3f}, {Ar38:0.3f}, ' \
                                     '{Ar37:0.3f}, {Ar36:0.3f}), ' \
                                     'x10<sup>-{sens_exp:}</sup> ' \
                                     'for Ar<super>40</super>, Ar<super>39</super>, ' \
                                     'Ar<super>38</super>, Ar<super>37</super>, Ar<super>36</super> ' \
                                     'respectively'.format(**furnace_blanks)

            frow = FooterRow(fontsize=fontsize, height=height)
            frow.add_item(span=-1, value=self._new_paragraph(average_furnace_blanks))
            data.append(frow)

        fr = FootNoteRow(fontsize=fontsize, height=height)

        self._footnotes.append(self._new_paragraph('P: plateau step'))
        txt = ', '.join([fi.text for fi in self._footnotes])
        fr.add_item(value=txt, span=-1)
        data.append(fr)


        #for fi in ['P: plateau step',]:
        #    p=self._new_paragraph(fi)
        #    span=self._calculate_span(p, start, fontSize=8)
        #    fr.add_item(value=p, span=span)
        #
        #    start+=span
        #
        #if self._footnotes:
        #    for fi in self._footnotes:
        #        span=self._calculate_span(fi, start, fontSize=3)
        #        fr.add_item(value=fi, span=span)
        #        start+=span
        #        self.debug("{} {} {}".format(start, start-span, span))
        #dsaf


        #    def factory(f):
        #        r = FootNoteRow(fontsize=fontsize)
        #        r.add_item(value=f)
        #        return r
        #
        #    data.extend([factory(fi) for fi in self._footnotes])
        #
        #_get_se = lambda x: (x[0][0], x[-1][0])
        ## set for footnot rows
        #footnote_idxs = self._get_idxs(data, FootNoteRow)
        #
        #sidx, eidx = _get_se(footnote_idxs)
        #style.add('VALIGN', (0, sidx), (-1, eidx), 'MIDDLE')
        #for idx, _v in footnote_idxs:
        #    style.add('SPAN', (0, idx), (-1, idx))
        #                style.add('VALIGN', (1, idx), (-1, idx), 'MIDDLE')


# ============= EOF =============================================
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
