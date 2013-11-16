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
#============= standard library imports ========================
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.lib.units import inch
from reportlab.platypus.tables import Table, TableStyle
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
#============= local library imports  ==========================
from pychron.loggable import Loggable
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import Spacer, PageBreak
from reportlab.lib import colors
from pychron.pdf.items import Anchor, Row
from reportlab.lib.pagesizes import landscape, letter
from pychron.helpers.formatting import floatfmt

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 7)
        self.drawRightString(200 * mm, 20 * mm,
                             "Page %d of %d" % (self._pageNumber, page_count))


class BasePDFWriter(Loggable):
    _footnotes = None
    orientation = 'portrait'
    col_widths = None
    left_margin = 1
    right_margin = 0.5
    top_margin = 1
    bottom_margin = 0.25

    use_alternating_background = True
    show_page_numbers = False

    def _new_base_doc_template(self, path):
        pagesize = letter
        if self.orientation == 'landscape':
            pagesize = landscape(letter)

        doc = BaseDocTemplate(path,
                              leftMargin=self.left_margin * inch,
                              rightMargin=self.right_margin * inch,
                              topMargin=self.top_margin * inch,
                              bottomMargin=self.bottom_margin * inch,
                              pagesize=pagesize
                              #                                   _pageBreakQuick=0,
                              #                                   showBoundary=1
        )
        return doc

    def build(self, path, *args, **kw):
        self.info('saving pdf to {}'.format(path))
        doc = self._new_base_doc_template(path)
        self._doc = doc
        flowables, templates = self._build(doc, *args, **kw)

        if templates is None:
            frames = self._default_frame(doc)
            templates = [self._new_page_template(frames)]

        for ti in templates:
            doc.addPageTemplates(ti)

        if self.show_page_numbers:
            doc.build(flowables, canvasmaker=NumberedCanvas)
        else:
            doc.build(flowables)

    def _build(self, *args, **kw):
        raise NotImplementedError

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

            #         if extend_last:
            #             print t._argW
            #             tw = sum(t._argW)
            #             d = self._doc
            #             aw = d.width - self._doc.leftMargin - self._doc.rightMargin
            #             print tw, aw
            #             t._argW[-1] = aw - tw


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
            ts.add('GRID', (0, 0), (-1, -1), 1.5, colors.red)

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

    def _new_paragraph(self, t, s='Normal', **skw):
        style = getSampleStyleSheet()[s]
        for k, v in skw.iteritems():
            setattr(style, k, v)

        p = Paragraph(t, style)
        return p

    def _page_break(self):
        return PageBreak()

    def _default_frame(self, doc):
        return Frame(doc.leftMargin, doc.bottomMargin,
                     doc.width, doc.height)

    def _new_page_template(self, frames):
        temp = PageTemplate(frames=frames)
        return temp

    def _new_spacer(self, w, h):
        return Spacer(w * inch, h * inch)

    def _vspacer(self, h):
        return self._new_spacer(0, h)

    def _make_footnote(self, tagname, tagName, tagText, linkname, link_extra=None):
        if self._footnotes is None:
            self._footnotes = []

        n = len(self._footnotes)
        link, tag = Anchor('{}_{}'.format(tagname, id(self)), n + 1)
        para = link(linkname, extra=link_extra)

        self._footnotes.append(tag(tagName, tagText))
        return para

    def _new_line(self, style, idx, weight=1.5,
                  start=0, end=-1,
                  color='black',
                  cmd='LINEBELOW'):

        style.add(cmd, (start, idx), (end, idx),
                  weight, getattr(colors, color))

    def _new_row(self, obj, attrs, default_fontsize=6):
        row = Row()
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

    def _get_idxs(self, rows, klass):
        return [(i, v) for i, v in enumerate(rows)
                if isinstance(v, klass)]

    def _fmt_attr(self, v, key='nominal_value', n=5, scale=1, **kw):
        if v is None:
            return ''

        if isinstance(v, tuple):
            if key == 'std_dev':
                v = v[1]
            else:
                v = v[0]
        elif isinstance(v, (float, int)):
            pass
        else:
            if hasattr(v, key):
                v = getattr(v, key)

        if isinstance(v, (float, int)):
            v = v / float(scale)

        return floatfmt(v, n=n, max_width=8, **kw)

    def _error(self, **kw):
        return lambda x: self._fmt_attr(x, key='std_dev', **kw)

    def _value(self, **kw):
        return lambda x: self._fmt_attr(x, key='nominal_value', **kw)

#============= EOF =============================================
