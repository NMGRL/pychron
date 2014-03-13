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
import re

from reportlab.pdfbase.pdfmetrics import stringWidth
from traits.api import Int

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.core.pdf.items import Row, Subscript, Superscript, FootNoteRow, FooterRow
from reportlab.lib.units import inch
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

        analyses = group.analyses
        self._ref = analyses[0]

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

            r, b = self._make_analysis_row(ai, is_plat_step)
            data.append(r)
            bdata.append(b)

            if self.options.use_alternating_background:
                idx = cnt + i
                if idx % 2 == 0:
                    style.add('BACKGROUND', (0, idx), (-1, idx), self.options.alternating_background)
                    #         data.extend([self._make_analysis_row(ai)
                    #                      for ai in analyses])

                    #         data.extend(header)
                    #         data.extend([self._make_blank_row(ai) for ai in analyses])
        auto_col_widths = True
        if auto_col_widths:
            self._calculate_col_widths(data[2:])

        idx = len(data) - 1
        self._new_line(style, idx)
        s = self._make_summary_rows(group, idx + 1, style)
        data.extend(s)

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

            ft = self._new_table(style, fdata, extend_last=True)
            return t, ft
        else:
            return t,

    def _make_analysis_row(self, analysis, is_plateau_step):
        value = self._value
        error = self._error

        analysis.is_plateau_step = is_plateau_step
        attrs = (
            #('temp_status', lambda x: '' if x == 0 else 'X'),
            ('is_plateau_step', lambda x: '<b>P</b>' if x else ''),
            ('aliquot_step_str', '{}',),
            ('extract_value', '{}'),
            ('moles_Ar40', value(scale=1e-16, n=1)),

            #==============================================================
            # signals
            #==============================================================
            ('Ar40', value(scale=1e3)),
            ('Ar40', error()),
            ('Ar39', value(scale=1e3)),
            ('Ar39', error()),
            ('Ar38', value()),
            ('Ar38', error()),
            ('Ar37', value()),
            ('Ar37', error()),
            ('Ar36', value()),
            ('Ar36', error(scale=1e-2)),

            #==============================================================
            # computed
            #==============================================================
            ('uage', value(n=2)),
            ('age_err_wo_j', error(n=4)),
            ('rad40_percent', value(n=1)),
            # ('F', value(n=5)),
            ('kca', value(n=1)),
            ('kca', error(n=2, s=1)),
        )
        default_fontsize = 6

        row = self._new_row(analysis, attrs, default_fontsize)

        battrs = (
            #==============================================================
            # blanks
            #==============================================================
            #                     ('', '{}'),
            #                     ('', '{}'),
            ('', '{}'),
            ('', '{}'),
            #                     ('blank_fit', '{}'),
            ('Ar40', value(scale=1e3)),
            ('Ar39', value(scale=1e3)),
            ('Ar38',),
            ('Ar37',),
            ('Ar36', value(scale=1e-2)),
            #
        )

        blankrow = Row(fontsize=default_fontsize)
        for args in battrs:
            efmt = self._error()
            vfmt = self._value()

            if len(args) == 2:
                attr, vfmt = args
            elif len(args) == 3:
                attr, vfmt, efmt = args
            else:
                attr = args[0]

            s, e = '', ''
            if attr:
                iso = analysis.isotopes.get(attr)
                if iso:
                    v = iso.blank.uvalue

                    s = vfmt(v)

                    s = self._new_paragraph('<i>{}</i>'.format(s))

                    e = efmt(v)
                    e = self._new_paragraph('<i>{}</i>'.format(e))

            blankrow.add_item(value=s)
            blankrow.add_item(value=e)

        return row, blankrow

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

    def _make_summary_rows(self, agroup, idx, style):
        span = 14
        wtd_mean_row = Row(fontsize=7, height=0.2)
        wtd_mean_row.add_item(value='<b>Weighted Mean Age</b>', span=span)
        #wtd_mean_row.add_blank_item(n=10)

        wa = agroup.weighted_age
        s = u'{} \u00b1{}'.format(self._value()(wa), self._error()(wa))
        wtd_mean_row.add_item(value=s, span=-1)

        inta = agroup.integrated_age
        int_row = Row(fontsize=7, height=0.2)
        int_row.add_item(value='<b>Integrated</b>', span=span)

        s = u'{} \u00b1{}'.format(self._value()(inta), self._error()(inta))
        int_row.add_item(value=s, span=-1)
        #int_row.add_item(value=self._value()(inta))
        #int_row.add_item(value=u' \u00b1{}'.format(self._error()(inta)))

        plat_row = Row(fontsize=7, height=0.2)
        plat_row.add_item(value='<b>Plateau</b>', span=span - 2)

        s = ''
        pa = agroup.plateau_age

        plat_row.add_item(value='<b>Steps</b>')
        plat_row.add_item(value=agroup.plateau_steps_str)

        if agroup.plateau_steps:
            s = u'{} \u00b1{}'.format(self._value()(pa), self._error()(pa))
            #pv=self._value()(pa)
            #pe=u' \u00b1{}'.format(self._error()(pa))

        #wtd_mean_row.add_blank_item(n=10)
        plat_row.add_item(value=s, span=-1)
        #plat_row.add_item(value=pv)
        #plat_row.add_item(value=pe)

        iso_row = Row(fontsize=7, height=0.2)
        iso_row.add_item(value='<b>Isochron</b>', span=span)

        isoa = agroup.isochron_age
        s = u'{} \u00b1{}'.format(self._value()(isoa), self._error()(isoa))
        iso_row.add_item(value=s, span=-1)
        #iso_row.add_item(value=self._value()(wa))
        #iso_row.add_item(value=u' \u00b1{}'.format(self._error()(wa)))

        return [wtd_mean_row, int_row, plat_row, iso_row]

    #===============================================================================
    # blanks
    #===============================================================================

    #===============================================================================
    # footnotes
    #===============================================================================
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

        fr = FootNoteRow(fontsize=6)
        #start=0

        self._footnotes.append(self._new_paragraph('P: plateau step'))
        txt = ', '.join([fi.text for fi in self._footnotes])
        #span=self._calculate_span(fi, start, fontSize=3)
        fr.add_item(value=txt, span=-1)

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
        data.append(fr)

        #    def factory(f):
        #        r = FootNoteRow(fontsize=6)
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

    def _make_footer_rows(self, data, style):
        rows = []
        df = 6
        for v in ('<b>Constants used</b>', '<b>Atmospheric argon ratios</b>'):
            row = FooterRow(fontsize=df, height=0.15)
            row.add_item(value=v, span=-1)
            rows.append(row)
            for i in range(19):
                row.add_item(value='')

        ref = self._ref
        arar_constants = ref.arar_constants
        for n, d, key in ((40, 36, 'atm4036'),
                          (40, 38, 'atm4038')):
            row = FooterRow(fontsize=df, height=0.15)
            row.add_item(value='({}Ar/{}Ar){}'.format(
                Superscript(n),
                Superscript(d),
                Subscript('A')),
                         span=3)

            vv = getattr(arar_constants, key)
            v, e = floatfmt(vv.nominal_value, n=1), floatfmt(vv.std_dev, n=1)

            cite_key = '{}_citation'.format(key)
            r = getattr(arar_constants, cite_key)

            row.add_item(value=u'{} \u00b1{}'.format(v, e),
                         span=2)
            row.add_item(value=r, span=-1)
            rows.append(row)

        row = FooterRow(fontsize=df)
        row.add_item(value='<b>Interferring isotope production ratios</b>', span=-1)
        rows.append(row)

        for n, d, s, key in (
                (40, 39, 'K', 'k4039'),
                (38, 39, 'K', 'k3839'),
                (37, 39, 'K', 'k3739'),
                (39, 37, 'Ca', 'ca3937'),
                (38, 37, 'Ca', 'ca3837'),
                (36, 37, 'Ca', 'ca3637')):
            row = FooterRow(fontsize=df, height=0.15)
            row.add_item(value='({}Ar/{}Ar){}'.format(
                Superscript(n),
                Superscript(d),
                Subscript(s)),
                         span=3)

            vv = ref.interference_corrections[key]
            v, e = floatfmt(vv.nominal_value), floatfmt(vv.std_dev)
            row.add_item(value=u'{} \u00b1{}'.format(v, e),
                         span=2)
            rows.append(row)

        row = FooterRow(fontsize=df)
        row.add_item(value='<b>Decay constants</b>', span=-1)
        rows.append(row)

        for i, E, dl, key in (
                (40, 'K', u'\u03BB\u03B5', 'lambda_b'),
                (40, 'K', u'\u03BB\u03B2', 'lambda_e'),
                (39, 'Ar', '', 'lambda_Ar39'),
                (37, 'Ar', '', 'lambda_Ar37')):
            vv = getattr(arar_constants, key)
            v, e = floatfmt(vv.nominal_value), floatfmt(vv.std_dev)

            cite_key = '{}_citation'.format(key)
            r = getattr(arar_constants, cite_key)

            row = FooterRow(fontsize=df, height=0.15)
            row.add_item(value=u'{}{} {}'.format(Superscript(i), E, dl), span=3)
            row.add_item(value=u'{} \u00b1{} a{}'.format(v, e, Superscript(-1)), span=3)
            row.add_item(value=r, span=-1)
            rows.append(row)

        data.extend(rows)

        _get_idxs = lambda x: self._get_idxs(data, x)
        _get_se = lambda x: (x[0][0], x[-1][0])

        footer_idxs = _get_idxs(FooterRow)
        sidx, eidx = _get_se(footer_idxs)
        style.add('VALIGN', (0, sidx), (-1, eidx), 'MIDDLE')

        #         for idx, v in footer_idxs:
        #             for si, se in v.spans:
        #                 style.add('SPAN', (si, idx), (se, idx))

        return rows

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
