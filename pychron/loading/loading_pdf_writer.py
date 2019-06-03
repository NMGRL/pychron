# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

from reportlab.lib import colors
# ============= standard library imports ========================
# from reportlab.platypus.flowables import PageBreak, Flowable
from reportlab.lib.colors import Color
# from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.platypus.doctemplate import FrameBreak
from reportlab.platypus.flowables import Spacer
from reportlab.platypus.frames import Frame
from six.moves import range
from traits.api import Bool
from traits.api import Color as TraitsColor
from traitsui.api import Item, VGroup

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
# from chaco.pdf_graphics_context import PdfPlotGraphicsContext
# ============= local library imports  ==========================
from pychron.core.pdf.items import Row, RowItem
from pychron.core.pdf.options import BasePDFOptions, dumpable
from pychron.loading.component_flowable import ComponentFlowable


class LoadingPDFOptions(BasePDFOptions):
    _persistence_name = 'load_pdf_options'

    show_colors = dumpable(Bool)
    show_identifiers = dumpable(Bool)
    show_samples = dumpable(Bool)
    show_weights = dumpable(Bool)
    show_hole_numbers = dumpable(Bool)
    view_pdf = dumpable(Bool)
    use_alternating_background = dumpable(Bool)
    alternating_background = dumpable(TraitsColor)

    def _show_colors_changed(self, new):
        if new:
            self.use_alternating_background = False

    def get_alternating_background(self):
        color = self.alternating_background
        t = color.red(), color.green(), color.blue()
        return [x / 255. for x in t]

    def traits_view(self):
        layout_grp = VGroup(Item('orientation'),
                            VGroup(Item('left_margin', label='Left'),
                                   Item('right_margin', label='Right'),
                                   Item('top_margin', label='Top'),
                                   Item('bottom_margin', label='Bottom'),
                                   show_border=True, label='Margins'),
                            show_border=True,
                            label='layout')
        grp = VGroup(Item('view_pdf'),
                     Item('show_identifiers'),
                     Item('show_samples'),
                     Item('show_weights'),
                     Item('show_hole_numbers'),
                     Item('show_colors'),
                     Item('use_alternating_background',
                          enabled_when='not show_colors'),
                     Item('alternating_background',
                          enabled_when='use_alternating_background'))
        v = okcancel_view(VGroup(layout_grp,
                                 grp),
                          title='Configure PDF')
        return v


class LoadingPDFWriter(BasePDFTableWriter):
    _options_klass = LoadingPDFOptions

    def _build(self, doc, positions, grouped_positions, component, meta):

        n = len(grouped_positions)
        if n > 5:
            idx = int(round(n / 2.))
            p1 = grouped_positions[:idx]
            p2 = grouped_positions[idx:]
        else:
            p1 = grouped_positions
            p2 = []

        #
        meta = self._make_meta_table(meta)
        t1 = self._make_table(p1)
        t2 = self._make_table(p2)

        t3 = self._make_notes_table(positions)

        flowables = [meta, Spacer(0, 5 * mm),
                     ComponentFlowable(component=component),
                     FrameBreak(),

                     Spacer(0, 5 * mm), t1,
                     FrameBreak(),

                     Spacer(0, 5 * mm), t2,
                     FrameBreak(),

                     t3]

        # make 3 frames top, lower-left, lower-right
        lm = doc.leftMargin
        bm = doc.bottomMargin + doc.height * .333

        fw = doc.width
        fh = doc.height * 0.666
        top = Frame(lm, bm, fw, fh)

        fw = doc.width / 2.
        fh = doc.height * 0.333
        bm = doc.bottomMargin

        lbottom = Frame(lm, bm, fw, fh)
        rbottom = Frame(lm + doc.width / 2., bm, fw, fh)

        frames = [top, lbottom, rbottom]
        template = self._new_page_template(frames)

        return flowables, (template,)

    def _make_meta_table(self, meta):
        ts = self._new_style()
        items = '<b>Load:</b> {load_name}|<b>Loader</b>: ' \
                '{username}|<b>Date</b>: {load_date}'.format(**meta).split('|')
        row1 = [self._new_paragraph(ti) for ti in items]
        row1 = Row(items=[RowItem(value=v) for v in row1])

        items = '<b>Projects</b>: {projects} | | '.format(**meta).split('|')
        row2 = [self._new_paragraph(ti) for ti in items]
        row2 = Row(items=[RowItem(value=v) for v in row2])

        table = self._new_table(ts, (row1, row2))

        return table

    def _make_notes_table(self, positions):
        data = [Row(items=[RowItem('L#'),
                           RowItem('Irradiation'),
                           RowItem('Sample'),
                           RowItem('Hole'),
                           RowItem('Weight'),
                           RowItem('N. Xtals'),
                           RowItem('Note')]), ]

        ts = self._new_style()
        ts.add('LINEBELOW', (0, 0), (-1, 0), 1, colors.black)

        ts.add('FONTSIZE', (0, 1), (-1, -1), 8)
        # ts.add('VALIGN', (-3, 1), (-1, -1), 'MIDDLE')

        idx = 0
        prev_id = None
        for pi in positions:
            if pi.identifier == prev_id:
                items = ('', '', '', pi.position, pi.weight, pi.nxtals, pi.note)
            else:
                items = (pi.identifier,
                         pi.irradiation_str,
                         pi.sample,
                         pi.position,
                         pi.weight, pi.note)

            prev_id = pi.identifier
            data.append(Row(items=[RowItem(ri) for ri in items]))
            if idx % 2 != 0:
                ts.add('BACKGROUND', (0, idx + 1), (-1, idx + 1),
                       colors.lightgrey)
            idx += 1

        cw = [mm * x for x in [13, 30, 40, 15, 16, 17, 58]]

        rh = [mm * 5 for _ in range(len(data))]

        t = self._new_table(ts, data,
                            colWidths=cw,
                            rowHeights=rh)
        return t

    def _make_table(self, positions):
        data = [Row(items=[RowItem('L#'),
                           RowItem('Irradiation'),
                           RowItem('Sample'),
                           RowItem('Positions')]), ]

        ts = self._new_style(header_line_idx=0)

        ts.add('FONTSIZE', (0, 1), (-1, -1), 8)
        # ts.add('VALIGN', (-3, 1), (-1, -1), 'MIDDLE')

        for idx, pi in enumerate(positions):

            items = [RowItem(i) for i in (pi.identifier,
                                          pi.level_str,
                                          pi.sample,
                                          pi.position_str)]
            row = Row(items=items)

            data.append(row)
            c = colors.white
            if self.options.show_colors:
                cc = pi.color
                if sum(cc) < 1.5:
                    ts.add('TEXTCOLOR', (0, idx + 1), (-1, idx + 1),
                           colors.white)

                c = Color(*cc)
            elif self.options.use_alternating_background:
                if idx % 2 == 0:
                    c = self.options.get_alternating_background()

                    if sum(c) < 1.5:
                        ts.add('TEXTCOLOR', (0, idx + 1), (-1, idx + 1),
                               colors.white)

            ts.add('BACKGROUND', (0, idx + 1), (-1, idx + 1), c)

        cw = [mm * x for x in [13, 20, 40, 20]]

        rh = [mm * 5 for _ in range(len(data))]

        t = self._new_table(ts, data, colWidths=cw, rowHeights=rh)
        return t

# ============= EOF =============================================
