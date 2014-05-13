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
from traits.api import Int
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.pdf.items import Row, FootNoteRow, FooterRow
from reportlab.lib import colors
from pychron.processing.tables.pdf_writer import IsotopePDFTableWriter


def DefaultInt(value=40):
    return Int(value)


class FusionPDFTableWriter(IsotopePDFTableWriter):
    extract_label = 'Power'
    extract_units = 'W'

    # def _build(self, doc, groups, title):
    #
    #     title_para = self._new_paragraph(title)
    #     flowables = [title_para, self._vspacer(0.1)]
    #
    #     include_footnotes = True
    #     for gi in groups:
    #         aa=gi.analyses
    #
    #         t, t2 = self._make_table(aa, gi,
    #                                  include_footnotes=include_footnotes)
    #
    #         include_footnotes = False
    #
    #         flowables.append(t)
    #         flowables.append(self._vspacer(0.1))
    #
    #     flowables.append(t2)
    #
    #     return flowables, None

    def _make_table(self, group,
                    double_first_line=True,
                    include_footnotes=False):

        self._ref = group.analyses[0]
        analyses = group.all_analyses
        style = self._new_style(debug_grid=False)

        style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
        style.add('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        style.add('LEFTPADDING', (0, 0), (-1, -1), 1)
        if double_first_line:
            self._new_line(style, 0, weight=2.5, cmd='LINEABOVE', )
        else:
            self._new_line(style, 0, cmd='LINEABOVE')

        data = []
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

        for i, ai in enumerate(analyses):
            r = self._make_analysis_row(ai, scales)
            data.append(r)
            # bdata.append(b)
            if self.options.use_alternating_background:
                idx = cnt + i
                if idx % 2 == 0:
                    style.add('BACKGROUND', (0, idx), (-1, idx),
                              colors.lightgrey)

        auto_col_widths = True
        if auto_col_widths:
            self._calculate_col_widths(data[2:])

        idx = len(data) - 1
        self._new_line(style, idx)
        s = self._make_summary_rows(group, idx + 1, style)
        data.extend(s)

        t = self._new_table(style, data, repeatRows=1)

        fdata = []
        style = self._new_style(debug_grid=False)
        style.add('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey)
        if include_footnotes:
            self._make_footnote_rows(fdata, style)
            self._make_footer_rows(fdata, style)
            ft = self._new_table(style, fdata)
            return t, ft
        else:
            return t,

    def _make_analysis_row(self, analysis, scales):
        value = self._value
        error = self._error
        attrs = (
            ('tag', lambda x: '' if x == 'ok' else 'X'),
            ('aliquot_step_str', '{}',),
            ('extract_value', '{}'),
            ('moles_Ar40', value(n=3, scale=1e-17)),

            #==============================================================
            # signals
            #==============================================================
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

            #==============================================================
            # computed
            #==============================================================

            # ('F', value(n=5)),
            ('kca', value(n=2)),
            ('kca', error(n=3)),
            ('rad40_percent', value(n=1)),
            ('uage', value(n=2)),
            ('age_err_wo_j', error(n=4)),
        )
        default_fontsize = 6

        row = self._new_row(analysis, attrs, default_fontsize)

        # battrs = (
        #     #==============================================================
        #     # blanks
        #     #==============================================================
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

        # blankrow = Row(fontsize=default_fontsize)
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
        #             s = self._new_paragraph('<i>{}</i>'.format(s),
        #             )
        #
        #             e = efmt(v)
        #             e = self._new_paragraph('<i>{}</i>'.format(e))
        #
        #     blankrow.add_item(value=s,
        #     )
        #     blankrow.add_item(value=e,
        #     )

        return row

        # def _set_row_heights(self, table, data):
        #     pass
        #     # a_idxs = self._get_idxs(data, (FooterRow, FootNoteRow))
        #     # for a, v in a_idxs:
        #     #     table._argH[a] = 0.19 * inch
        #     #
        #     idx = self._get_idxs(data, Row)
        #     for i, v in idx:
        #         if v.height:
        #             table._argH[i] = v.height * inch


        #===============================================================================
        # summary
        #===============================================================================

    def _make_summary_rows(self, mean, idx, style):
        weighted_mean_row = Row(fontsize=7, height=0.15)
        weighted_mean_row.add_item(value='<b>Weighted Mean Age</b>', span=5)

        weighted_mean_row.add_blank_item(n=12)
        wa = mean.weighted_age
        weighted_mean_row.add_item(value=self._value(n=2)(wa))
        weighted_mean_row.add_item(value=u'\u00b1{}'.format(self._error(n=3)(wa)))

        #         for s, e in platrow.spans:
        #             style.add('SPAN', (s, idx), (e, idx))
        #         platrow.add_item(value='Weighted Mean Age')
        return [weighted_mean_row]

    #===============================================================================
    # blanks
    #===============================================================================

    #===============================================================================
    # footnotes
    #===============================================================================
    def _make_footnote_rows(self, data, style):
        data.append(Row(height=0.1))

        blanks = self._get_average_blanks()
        if blanks:
            co2_blanks, furnace_blanks = blanks
            average_co2_blanks = 'Average blanks for CO<sub>2</sub>: ({Ar40:0.3f}, {Ar39:0.3f}, {Ar38:0.3f}, ' \
                                 '{Ar37:0.3f}, {Ar36:0.3f}), ' \
                                 'x10<sup>-{sens_exp:}</sup> ' \
                                 'for Ar<super>40</super>, Ar<super>39</super>, ' \
                                 'Ar<super>38</super>, Ar<super>37</super>, Ar<super>36</super> ' \
                                 'respectively'.format(**co2_blanks)
            crow = FooterRow(fontsize=6)
            crow.add_item(span=-1, value=self._new_paragraph(average_co2_blanks))
            data.append(crow)

        def factory(f):
            r = FootNoteRow(fontsize=6)
            r.add_item(value=f)
            return r

        data.extend([factory(fi) for fi in self._footnotes])

        #         _get_idxs = lambda x: self._get_idxs(rows, x)
        _get_se = lambda x: (x[0][0], x[-1][0])
        # set for footnot rows
        footnote_idxs = self._get_idxs(data, FootNoteRow)
        sidx, eidx = _get_se(footnote_idxs)
        style.add('VALIGN', (0, sidx), (-1, eidx), 'MIDDLE')
        for idx, _v in footnote_idxs:
            style.add('SPAN', (0, idx), (-1, idx))


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
            #def _make_meta(self, analyses, style, include_footnotes=False):
            #    ref = analyses[0]
            #    j = ref.j
            #
            #    #ic = ref.ic_factor
            #    ic = (1, 0)
            #    sample = ref.sample
            #    labnumber = ref.labnumber
            #    material = ref.material
            #
            #    igsn = ''
            #
            #    if not isinstance(j, tuple):
            #        j = j.nominal_value, j.std_dev
            #
            #    if not isinstance(ic, tuple):
            #        ic = ic.nominal_value, ic.std_dev
            #
            #    line1 = Row(fontsize=8)
            #    line1.add_item(value=NamedParameter('Sample', sample), span=5)
            #    line1.add_item(value=NamedParameter('Lab #', labnumber), span=2)
            #
            #    js = u'{:0.2E} \u00b1{:0.2E}'.format(j[0], j[1])
            #    line1.add_item(value=NamedParameter('J', js), span=3)
            #    ics = u'{:0.3f} \u00b1{:0.4f}'.format(ic[0], ic[1])
            #    if include_footnotes:
            #        foot = self._make_footnote('IC',
            #                                   'IC Factor',
            #                                   'H1/CDD intercalibration',
            #                                   '<b>IC</b>',
            #                                   link_extra=u': {}'.format(ics))
            #    else:
            #        foot = NamedParameter('IC', ics)
            #
            #    line1.add_item(value=foot, span=3)
            #
            #    line2 = Row(fontsize=8)
            #    line2.add_item(value=NamedParameter('Material', material), span=5)
            #    line2.add_item(value=NamedParameter('IGSN', igsn), span=2)
            #
            #    #         self._sample_summary_row1 = line1
            #    #         self._sample_summary_row2 = line2
            #    title = False
            #    title_row = 0
            #    sample_row = 0
            #    if title:
            #        sample_row += 1
            #
            #    style.add('LINEBELOW', (0, sample_row), (-1, sample_row), 1.5, colors.black)
            #
            #    return [line1, line2]

            #def _make_header(self, style):
            #    sigma = u'\u00b1 1\u03c3'
            #    #         sigma = self._plusminus_sigma()
            #    super_ar = lambda x: '{}Ar'.format(Superscript(x))
            #
            #    _102fa = '(10{} fA)'.format(Superscript(2))
            #    _103fa = '(10{} fA)'.format(Superscript(3))
            #    minus_102fa = '(10{} fA)'.format(Superscript(-2))
            #
            #    #         blank = self._make_footnote('BLANK',
            #    #                                    'Blank Type', 'LR= Linear Regression, AVE= Average',
            #    #                                    'Blank')
            #    #         blank = 'Blank Type'
            #    line = [
            #        ('', ''),
            #        ('N', ''),
            #        (self.extract_label, self.extract_units),
            #        (super_ar(40), ''),
            #        (super_ar(40), _103fa), (sigma, ''),
            #        (super_ar(39), _103fa), (sigma, ''),
            #        (super_ar(38), ''), (sigma, ''),
            #        (super_ar(37), ''), (sigma, ''),
            #        (super_ar(36), ''), (sigma, minus_102fa),
            #        ('%{}*'.format(super_ar(40)), ''),
            #        ('{}*/{}{}'.format(super_ar(40),
            #                           super_ar(39),
            #                           Subscript('K')), ''),
            #        ('Age', '(Ma)'), (sigma, ''),
            #        ('K/Ca', ''),
            #        (sigma, ''),
            #        #                 (blank, 'type'),
            #        #                 (super_ar(40), ''), (sigma, ''),
            #        #                 (super_ar(39), ''), (sigma, ''),
            #        #                 (super_ar(38), ''), (sigma, ''),
            #        #                 (super_ar(37), ''), (sigma, ''),
            #        #                 (super_ar(36), ''), (sigma, ''),
            #    ]
            #
            #    name_row, unit_row = zip(*line)
            #
            #    default_fontsize = 8
            #    nrow = Row(fontsize=default_fontsize)
            #    for i, ni in enumerate(name_row):
            #        nrow.add_item(value=ni)
            #
            #    default_fontsize = 7
            #    urow = Row(fontsize=default_fontsize)
            #    for ni in unit_row:
            #        urow.add_item(value=ni)
            #
            #    name_row_idx = 2
            #    unit_row_idx = 3
            #    # set style for name header
            #    style.add('LINEABOVE', (0, name_row_idx),
            #              (-1, name_row_idx), 1.5, colors.black)
            #
            #    # set style for unit header
            #    style.add('LINEBELOW', (0, unit_row_idx),
            #              (-1, unit_row_idx), 1.5, colors.black)
            #
            #    return [
            #        nrow,
            #        urow
            #    ]