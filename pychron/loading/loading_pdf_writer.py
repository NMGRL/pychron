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
from traits.api import HasTraits, List, Bool
from traitsui.api import View, Item, Group, VGroup, HGroup
# ============= standard library imports ========================
# from reportlab.platypus.flowables import PageBreak, Flowable
from reportlab.lib.colors import Color
from reportlab.platypus.doctemplate import FrameBreak
# from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus.frames import Frame

# from chaco.pdf_graphics_context import PdfPlotGraphicsContext
# ============= local library imports  ==========================
from pychron.core.pdf.items import Row, RowItem
from pychron.core.pdf.options import BasePDFOptions
from pychron.loading.component_flowable import ComponentFlowable
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
from reportlab.platypus.flowables import Spacer
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter


class LoadingPDFOptions(BasePDFOptions):
    _persistence_name = 'load_pdf_options'

    show_colors = Bool
    show_labnumbers = Bool
    show_weights = Bool
    show_hole_numbers = Bool

    def _show_colors_changed(self, new):
        if new:
            self.use_alternating_background = False

    def _get_dump_attrs(self):
        d = super(LoadingPDFOptions, self)._get_dump_attrs()
        return d + ('show_colors', 'show_labnumbers', 'show_weights', 'show_hole_numbers')

    def traits_view(self):
        layout_grp = VGroup(Item('orientation'),
                            VGroup(Item('left_margin', label='Left'),
                                   Item('right_margin', label='Right'),
                                   Item('top_margin', label='Top'),
                                   Item('bottom_margin', label='Bottom'),
                                   show_border=True, label='Margins'),
                            show_border=True,
                            label='layout')
        grp = VGroup(Item('show_labnumbers'),
                     Item('show_weights'),
                     Item('show_hole_numbers'),
                     Item('show_colors'),
                     Item('use_alternating_background', enabled_when='not show_colors'),
                     Item('alternating_background', enabled_when='use_alternating_background'))
        v = View(VGroup(layout_grp,
                        grp,
                        ),
                 kind='livemodal', buttons=['OK', 'Cancel'])
        return v


class LoadingPDFWriter(BasePDFTableWriter):
    _options_klass = LoadingPDFOptions

    def _build(self, doc, positions, component, meta):

        n = len(positions)
        idx = int(round(n / 2.))

        p1 = positions[:idx]
        p2 = positions[idx:]
        #
        meta = self._make_meta_table(meta)
        t1 = self._make_table(p1)
        t2 = self._make_table(p2)

        t3 = self._make_notes_table(component)

        flowables = [meta, Spacer(0, 5 * mm), ComponentFlowable(component=component),
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
        items = '<b>Load:</b> {load_name}|<b>Loader</b>: {username}|<b>Date</b>: {load_date}'.format(**meta).split('|')
        row1 = [self._new_paragraph(ti) for ti in items]
        row1 = Row(items=[RowItem(value=v) for v in row1])

        items = '<b>Projects</b>: {projects} | | '.format(**meta).split('|')
        row2 = [self._new_paragraph(ti) for ti in items]
        row2 = Row(items=[RowItem(value=v) for v in row2])

        table = self._new_table(ts, (row1, row2))

        return table

    def _make_notes_table(self, canvas):
        data = [Row(items=[RowItem('L#'),
                           RowItem('Irradiation'),
                           RowItem('Sample'),
                           RowItem('Hole'),
                           RowItem('Weight'),
                           RowItem('Note')]), ]

        ts = self._new_style()
        ts.add('LINEBELOW', (0, 0), (-1, 0), 1, colors.black)

        ts.add('FONTSIZE', (0, 1), (-1, -1), 8)
        # ts.add('VALIGN', (-3, 1), (-1, -1), 'MIDDLE')

        idx = 0
        prev_irrad = None
        for pi in sorted(canvas.scene.get_items(LoadIndicator),
                         key=lambda x: int(x.name)):
            if pi.irradiation:
                if pi.irradiation == prev_irrad:
                    items = (pi.labnumber_label.text,
                             '', '',
                             pi.name,
                             pi.weight or '',
                             pi.note or '')
                else:
                    items = (pi.labnumber_label.text,
                             pi.irradiation,
                             pi.sample,
                             pi.name,
                             pi.weight, pi.note)

                prev_irrad = pi.irradiation

                data.append(Row(items=[RowItem(ri) for ri in items]))
                if idx % 2 == 0:
                    ts.add('BACKGROUND', (0, idx + 1), (-1, idx + 1),
                           colors.lightgrey)
                idx += 1

        cw = map(lambda x: mm * x, [15, 22, 22, 22, 22, 80])

        rh = [mm * 5 for _ in xrange(len(data))]

        t = self._new_table(ts, data,
                            colWidths=cw,
                            rowHeights=rh)
        return t

    def _make_table(self, positions):
        data = [Row(items=[RowItem('L#'),
                           RowItem('Irradiation'),
                           RowItem('Sample'),
                           RowItem('Positions')]),]

        ts = self._new_style(header_line_idx=0)

        ts.add('FONTSIZE', (0, 1), (-1, -1), 8)
        # ts.add('VALIGN', (-3, 1), (-1, -1), 'MIDDLE')

        for idx, pi in enumerate(positions):
            # row = (pi.labnumber, pi.irradiation_str, pi.sample,
            # pi.position_str)

            items = [RowItem(i) for i in (pi.labnumber, pi.irradiation_str, pi.sample,
                                          pi.position_str)]
            row = Row(items=items)

            data.append(row)
            c = colors.white
            if self.options.show_colors:
                cc = pi.color
                if sum(cc) < 1.5:
                    ts.add('TEXTCOLOR', (0, idx + 1), (-1, idx + 1), colors.white)

                c = Color(*cc)
            elif self.options.use_alternating_background:
                if idx % 2 == 0:
                    c = self.options.get_alternating_background()

                    if sum(c) < 1.5:
                        ts.add('TEXTCOLOR', (0, idx + 1), (-1, idx + 1), colors.white)

            ts.add('BACKGROUND', (0, idx + 1), (-1, idx + 1), c)

        cw = map(lambda x: mm * x, [13, 21, 22, 38])

        rh = [mm * 5 for _ in xrange(len(data))]

        t = self._new_table(ts, data, colWidths=cw, rowHeights=rh)
        return t

# ============= EOF =============================================
