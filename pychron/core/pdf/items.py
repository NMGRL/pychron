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
from traits.api import HasTraits, List, Int, Str, Any, Either, Callable
# ============= standard library imports ========================
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
# ============= local library imports  ==========================

STYLES = getSampleStyleSheet()


class Row(HasTraits):
    items = List
    fontsize = Int
    fontname = Str
    spans = List
    height = None

    def render(self):
        return [it.render() for it in self.items]

    def add_item(self, span=1, blank_fill=True, **kw):
        if 'fontsize' not in kw and self.fontsize:
            kw['fontsize'] = self.fontsize

        self.items.append(RowItem(**kw))
        ss = len(self.items) - 1
        if span > 1:
            se = ss + span
            self.spans.append((ss, se - 1))
            self.add_blank_item(span - 1)
        elif span == -1:
            self.spans.append((ss, -1))

    def add_blank_item(self, n=1):
        for _ in range(n):
            self.add_item(value='')

    def __iter__(self):
        return (it.render() for it in self.items)

    def __getitem__(self, i):
        return self.items[i].value


class BaseItem(HasTraits):
    value = Any
    fmt = Either(Str, Callable)
    fontsize = Int(8)
    fontname = Str#'Helvetica'
    italic = False

    def __init__(self, value=None, *args, **kw):
        self.value = value
        super(BaseItem, self).__init__(*args, **kw)

    def render(self):
        v = self.value

        if not isinstance(v, Paragraph):
            fmt = self.fmt
            if fmt is None:
                fmt = u'{}'
            if isinstance(fmt, (str, unicode)):
                v = fmt.format(v)
            else:
                v = fmt(v)

        v = self._set_font(v, self.fontsize, self.fontname)

        return v

    def _set_font(self, v, size, name):
        if isinstance(v, Paragraph):
            for frag in v.frags:
                if frag.super or frag.sub:
                    frag.fontSize = size - 2
                else:
                    frag.fontSize = size
        elif name:
            v = self._new_paragraph(u'<font size="{}" name="{}">{}</font>'.format(size, name, v))

        return v

    def _new_paragraph(self, t, s='Normal'):
        style = STYLES[s]
        p = Paragraph(t, style)
        return p


class RowItem(BaseItem):
    include_width_calc = True


def Superscript(v):
    return u'<super>{}</super>'.format(v)


def Subscript(v):
    return u'<sub>{}</sub>'.format(v)


def NamedParameter(name, value):
    return u'<b>{}</b>: {}'.format(name, value)


def Anchor(tagname, num, s='Normal'):
    snum = Superscript(num)
    link = u'{{}}<a href="#{}" color="green">{}</a>'.format(tagname, snum)
    tag = u'{{}}{}: {{}}<a name="{}"/>'.format(snum, tagname)

    style = STYLES[s]

    def flink(x, extra=None):
        f = link.format(x)
        if extra:
            f = u'{}{}'.format(f, extra)
        return Paragraph(f, style)

    def p2(n, v):
        return Paragraph(tag.format(n, v), style)

    #    p1 = lambda x: Paragraph(link.format(x), style)
    #     p2 = lambda n, v: Paragraph(tag.format(n, v), style)

    return flink, p2


class FootNoteRow(Row):
    pass


class FooterRow(Row):
    pass

# ============= EOF =============================================
