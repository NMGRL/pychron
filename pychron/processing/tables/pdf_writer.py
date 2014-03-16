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
from traits.api import Str

#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.core.helpers.formatting import floatfmt
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Superscript, Row, NamedParameter, FooterRow, Subscript


class IsotopePDFTableWriter(BasePDFTableWriter):
    extract_label = Str
    extract_units = Str
    default_row_height = 0.15  #inches

    def _get_signal_units(self, analyses):
        ref = analyses[0]
        if ref.mass_spectrometer.lower() == 'map':
            signal_units = 'nA'
        else:
            signal_units = 'fA'
        return signal_units

    def _get_signal_scales(self, analyses):
        ref = analyses[0]
        if ref.mass_spectrometer.lower() == 'map':
            s40, s39, s38, s37, s36 = 1, 1, 1, 1, 1
            e40, e39, e38, e37, e36 = 1, 1, 1, 1, 1
        else:
            s40, s39, s38, s37, s36 = 1e3, 1e3, 1, 1, 1
            e40, e39, e38, e37, e36 = 1, 1, 1, 1, 1e-2
        return dict(Ar40=s40,
                    Ar39=s39,
                    Ar38=s38,
                    Ar37=s37,
                    Ar36=s36,
                    Ar40err=e40,
                    Ar39err=e39,
                    Ar38err=e38,
                    Ar37err=e37,
                    Ar36err=e36,
        )

    def _build(self, doc, groups, title):
        self.debug('build table {}'.format(title))
        title_para = self._new_paragraph(title)

        templates = None
        flowables = [title_para, self._vspacer(0.1)]

        n = len(groups) - 1
        for i, group in enumerate(groups):

            include_footnotes = i == n
            fs = self._make_table(group,
                                  include_footnotes=include_footnotes)
            for fi in fs:
                flowables.append(fi)
                flowables.append(self._vspacer(0.1))

            if i < n:
                flowables.append(self._vspacer(0.25))

        return flowables, templates

    #def _make_footnotes(self, ref, row):
    #    ics=self._get_ic_factor(ref)
    #    foot = self._make_footnote('IC',
    #                                'IC Factor',
    #                                'H1/CDD intercalibration',
    #                                '<b>IC</b>',
    #                                link_extra=u': {}'.format(ics))
    #    return foot,
    #    #row.add_item(value=foot, span=3)
    #
    def _get_disc(self, ref):
        disc = ref.discrimination
        return u'{:0.3f} \u00b1{:0.4f}'.format(disc.nominal_value, disc.std_dev)

    def _get_ic_factor(self, ref):
        # ic = (1, 0)
        ic = ref.ic_factor
        if not isinstance(ic, tuple):
            ic = ic.nominal_value, ic.std_dev

        return u'{:0.3f} \u00b1{:0.4f}'.format(ic[0], ic[1])

    def _make_meta(self, analyses, style, include_footnotes=False):
        ref = analyses[0]
        j = ref.j

        #ic = ref.ic_factor
        ic = (1, 0)
        sample = ref.sample
        labnumber = ref.labnumber
        material = ref.material
        ms = ref.mass_spectrometer

        igsn = ''

        if not isinstance(j, tuple):
            j = j.nominal_value, j.std_dev

        line1 = Row(fontsize=8)
        line1.add_item(value=NamedParameter('Sample', sample), span=5)
        line1.add_item(value=NamedParameter('Lab #', labnumber), span=2)

        js = u'{:0.2E} \u00b1{:0.2E}'.format(j[0], j[1])
        line1.add_item(value=NamedParameter('J', js), span=4)
        if ms.lower() == 'map':
            disc = self._get_disc(ref)
            if include_footnotes:
                disc = self._make_footnote('Disc.',
                                           'Disc.',
                                           '1 amu discrimination',
                                           '<b>Disc.</b>',
                                           link_extra=u': {}'.format(disc))
            else:
                disc = NamedParameter('Disc.', disc)
            line1.add_item(value=disc, span=3)
        else:
            ics = self._get_ic_factor(ref)

            if include_footnotes:
                foot = self._make_footnote('IC',
                                           'IC Factor',
                                           'H1/CDD intercalibration',
                                           '<b>IC</b>',
                                           link_extra=u': {}'.format(ics))
            else:
                ics = self._get_ic_factor(ref)
                foot = NamedParameter('IC', ics)

            line1.add_item(value=foot, span=3)

        line2 = Row(fontsize=8)
        line2.add_item(value=NamedParameter('Material', material), span=6)
        line2.add_item(value=NamedParameter('IGSN', igsn), span=2)
        line2.add_item(value=NamedParameter('Spectrometer', ms), span=3)

        #         self._sample_summary_row1 = line1
        #         self._sample_summary_row2 = line2
        title = False
        title_row = 0
        sample_row = 0
        if title:
            sample_row += 1

        style.add('LINEBELOW', (0, sample_row), (-1, sample_row), 1.5, colors.black)

        return [line1, line2]

    def _make_header(self, style, signal_units='nA'):
        sigma = u'\u00b1 1\u03c3'

        super_ar = lambda x: '{}Ar'.format(Superscript(x))

        _1016moles = '(10{} mol)'.format(Superscript(-16))
        if signal_units == 'nA':
            unit_scale_40 = ''
            unit_scale_39 = ''
            unit_scale_36err = ''
        else:
            # = '(10{} {})'.format(Superscript(2), signal_units)
            unit_scale_40 = '(10{} {})'.format(Superscript(3), signal_units)
            unit_scale_39 = '(10{} {})'.format(Superscript(3), signal_units)
            unit_scale_36err = '(10{} {})'.format(Superscript(-2), signal_units)


        #         blank = self._make_footnote('BLANK',
        #                                    'Blank Type', 'LR= Linear Regression, AVE= Average',
        #                                    'Blank')
        #         blank = 'Blank Type'
        line = [
            ('', ''),
            ('N', ''),
            (self.extract_label, '({})'.format(self.extract_units)),
            (super_ar(40), _1016moles),
            (super_ar(40), unit_scale_40), (sigma, ''),
            (super_ar(39), unit_scale_39), (sigma, ''),
            (super_ar(38), ''), (sigma, ''),
            (super_ar(37), ''), (sigma, ''),
            (super_ar(36), ''), (sigma, unit_scale_36err),
            ('Age', '(Ma)'), (sigma, ''),
            ('%{}*'.format(super_ar(40)), ''),
            # ('{}*/{}{}'.format(super_ar(40),
            #                    super_ar(39),
            #                    Subscript('K')), ''),

            ('K/Ca', ''),
            (sigma, ''),
            #                 (blank, 'type'),
            #                 (super_ar(40), ''), (sigma, ''),
            #                 (super_ar(39), ''), (sigma, ''),
            #                 (super_ar(38), ''), (sigma, ''),
            #                 (super_ar(37), ''), (sigma, ''),
            #                 (super_ar(36), ''), (sigma, ''),
        ]

        name_row, unit_row = zip(*line)

        default_fontsize = 7
        nrow = Row(fontsize=default_fontsize, height=0.2)
        for i, ni in enumerate(name_row):
            nrow.add_item(value=ni)

        default_fontsize = 6
        urow = Row(fontsize=default_fontsize, height=0.2)
        for ni in unit_row:
            urow.add_item(value=ni)

        name_row_idx = 2
        unit_row_idx = 3
        # set style for name header
        style.add('LINEABOVE', (0, name_row_idx),
                  (-1, name_row_idx), 1.5, colors.black)

        # set style for unit header
        style.add('LINEBELOW', (0, unit_row_idx),
                  (-1, unit_row_idx), 1.5, colors.black)

        return [nrow, urow]

    def _new_row(self, obj, attrs, default_fontsize=6):
        row = Row(height=self.default_row_height)
        for args in attrs:
            if len(args) == 3:
                attr, fmt, fontsize = args
            else:
                attr, fmt = args
                fontsize = default_fontsize

            #if attr in ARGON_KEYS:
            if attr in obj.isotopes:
                v = obj.isotopes[attr].get_intensity()
            else:
                v = getattr(obj, attr)

            #self.debug('{} {}'.format(attr, v))
            row.add_item(value=v, fmt=fmt, fontsize=fontsize)

        return row

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

        return rows

    def _get_average_blanks(self):
        p = '/Users/ross/Programming/git/dissertation/data/minnabluff/average_blanks_map.yaml'
        with open(p, 'r') as fp:
            yd = yaml.load(fp)

        #convert to mols
        ydc = yd['CO2']
        for k, v in ydc.iteritems():
            ydc[k] = v * 5e-17 * 1.0e18

        ydc['sens_exp'] = 18
        ydf = yd['Furnace']
        for k, v in ydf.iteritems():
            ydf[k] = v * 1e-16 * 1.0e18
        ydf['sens_exp'] = 18
        return ydc, ydf
        #============= EOF =============================================
