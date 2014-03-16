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
from traits.api import Instance
#============= standard library imports ========================
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.lib.units import inch
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
#============= local library imports  ==========================
from pychron.loggable import Loggable
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import Spacer, PageBreak
from pychron.core.pdf.items import Anchor
from reportlab.lib.pagesizes import landscape, letter
from pychron.core.helpers.formatting import floatfmt

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from pychron.core.pdf.options import BasePDFOptions


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

    options = Instance(BasePDFOptions)
    _options_klass = BasePDFOptions

    def _options_default(self):
        return self._options_klass()

    def _new_base_doc_template(self, path):
        pagesize = letter
        opt = self.options
        if opt.orientation == 'landscape':
            pagesize = landscape(letter)
            leftMargin = opt.bottom_margin * inch
            rightMargin = opt.top_margin * inch
            topMargin = opt.left_margin * inch
            bottomMargin = opt.right_margin * inch
        else:
            leftMargin = opt.left_margin * inch
            rightMargin = opt.right_margin * inch
            topMargin = opt.top_margin * inch
            bottomMargin = opt.bottom_margin * inch

        print leftMargin, rightMargin, topMargin, bottomMargin
        doc = BaseDocTemplate(path,
                              leftMargin=leftMargin,
                              rightMargin=rightMargin,
                              topMargin=topMargin,
                              bottomMargin=bottomMargin,
                              pagesize=pagesize)
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

        if self.options.show_page_numbers:
            doc.build(flowables, canvasmaker=NumberedCanvas)
        else:
            doc.build(flowables)

    def _build(self, *args, **kw):
        raise NotImplementedError

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

        return floatfmt(v, n=n, max_width=10, **kw)

    def _error(self, **kw):
        return lambda x: self._fmt_attr(x, key='std_dev', **kw)

    def _value(self, **kw):
        return lambda x: self._fmt_attr(x, key='nominal_value', **kw)


#============= EOF =============================================
