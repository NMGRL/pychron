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
# from traits.api import HasTraits, List
# from traitsui.api import View, Item
# ============= standard library imports ========================
# from reportlab.platypus.flowables import PageBreak, Flowable
from reportlab.platypus.doctemplate import FrameBreak
# from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus.frames import Frame

# from chaco.pdf_graphics_context import PdfPlotGraphicsContext
# ============= local library imports  ==========================
from pychron.loading.component_flowable import ComponentFlowable
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
from reportlab.platypus.flowables import Spacer
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter


class LoadingPDFWriter(BasePDFTableWriter):

    def _build(self, doc, positions, component, meta):

        n = len(positions)
        idx = int(round(n / 2.))

        p1 = positions[:idx]
        p2 = positions[idx:]
#
        m = self._make_meta_table(meta)
        t1 = self._make_table(p1)
        t2 = self._make_table(p2)

        t3 = self._make_notes_table(component)

        flowables = [
              m,
              Spacer(0, 5 * mm),
              ComponentFlowable(component=component),
              FrameBreak(),
              Spacer(0, 5 * mm),
              t1,
              FrameBreak(),
              Spacer(0, 5 * mm),
              t2,
              FrameBreak(),
              t3
              ]

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
#         p = Paragraph()
        ts = self._new_style()
        items = '<b>Load:</b> {load_name}|<b>Loader</b>: {username}|<b>Date</b>: {load_date}'.format(**meta).split('|')
        row1 = [self._new_paragraph(ti) for ti in items]

        items = '<b>Projects</b>: {projects} | | '.format(**meta).split('|')
        row2 = [self._new_paragraph(ti) for ti in items]

        data = [row1, row2]

        table = self._new_table(ts, data)

        return table

    def _make_notes_table(self, canvas):
        data = [('L#', 'Irradiation', 'Sample', 'Hole', 'Weight', 'Note')]

        ts = self._new_style()
        ts.add('LINEBELOW', (0, 0), (-1, 0), 1, colors.black)

        ts.add('FONTSIZE', (-3, 1), (-1, -1), 8)
        ts.add('VALIGN', (-3, 1), (-1, -1), 'MIDDLE')

        idx = 0
        prev_irrad = None
        for pi in sorted(canvas.scene.get_items(LoadIndicator),
                         key=lambda x: x.name):
            if pi.irradiation:
                if pi.irradiation == prev_irrad:
                    row = (pi.labnumber_label.text,
                           '', '',
                           pi.name,
                           pi.weight or '',
                           pi.note or ''
                           )
                else:
                    row = (pi.labnumber_label.text,
                           pi.irradiation,
                           pi.sample,
                           pi.name,
                           pi.weight, pi.note)

                prev_irrad = pi.irradiation
                data.append(row)
                if idx % 2 == 0:
                    ts.add('BACKGROUND', (0, idx + 1), (-1, idx + 1),
                            colors.lightgrey)
                idx += 1

        cw = map(lambda x: mm * x, [15, 20, 20, 20, 20, 100])

        rh = [mm * 5 for _ in xrange(len(data))]

        t = self._new_table(ts, data,
                  colWidths=cw,
                  rowHeights=rh
                  )

        return t

    def _make_table(self, positions):
        data = [('L#', 'Irradiation', 'Sample', 'Positions')]
        ts = self._new_style(header_line_idx=0)

        ts.add('FONTSIZE', (-3, 1), (-1, -1), 8)
        ts.add('VALIGN', (-3, 1), (-1, -1), 'MIDDLE')

        for idx, pi in enumerate(positions):
            row = (pi.labnumber, pi.irradiation_str, pi.sample,
                   pi.position_str)
            data.append(row)
            if idx % 2 == 0:
                ts.add('BACKGROUND', (0, idx + 1), (-1, idx + 1),
                        colors.lightgrey)

        cw = map(lambda x: mm * x, [12, 20, 22, 40])

        rh = [mm * 5 for _ in xrange(len(data))]

        t = self._new_table(ts, data, colWidths=cw, rowHeights=rh)
        return t
# ============= EOF =============================================
