#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, List, \
    on_trait_change, Callable, Bool, Int, Property
from pychron.helpers.formatting import floatfmt
from pychron.pychron_constants import PLUSMINUS

#============= standard library imports ========================
#============= local library imports  ==========================
# def fixed_width(m, i):
#    return '{{:<{}s}}'.format(i).format(m)
# def floatfmt(m, i=6):
#    if abs(m) < 10 ** -i:
#        return '{:0.2e}'.format(m)
#    else:
#        return '{{:0.{}f}}'.format(i).format(m)

class TextCell(HasTraits):
    text = ''
    color = 'black'
    bg_color = None
    bold = False
    format = Callable
    width = Int
    col_span = None

    def __init__(self, text, *args, **kw):
        super(TextCell, self).__init__(**kw)
        if not text is None:
            if self.format:
                self.text = self.format(text)
            else:
                self.text = u'{}'.format(text)

#             if self.width:
#                 self.text='{{:<{}s}}'.format(self.width).format(self.text)

class HtmlCell(TextCell):
    html = Property

    def _get_html(self):
        html = self.text
        if self.bold:
            html = '<b>{}</b>'.format(html)
        return html

        #        for k in kw:

#            setattr(self, k, kw[k])
class BoldCell(TextCell):
    bold = True


class TextRow(HasTraits):
    cells = List
    color = None

    def __init__(self, *args, **kw):
        super(TextRow, self).__init__(**kw)
        self.cells = list(args)


class HeaderRow(TextRow):
    @on_trait_change('cells[]')
    def _update_cell(self):
        for ci in self.cells:
            ci.bold = True


class TextTable(HasTraits):
    items = List
    border = Bool

    def __init__(self, *args, **kw):
        self.items = list(args)
        super(TextTable, self).__init__(**kw)

    def rows(self):
        return len(self.items)

    def cols(self):
        return max([len(ri.cells) for ri in self.items])


class TextTableAdapter(HasTraits):
#    def __getattr__(self, attr):
#        pass
    columns = List
    _cached_table = None

    def _make_header_row(self, columns=None):
        if columns is None:
            columns = self.columns
        return HeaderRow(*[self._header_cell_factory(args)
                           for args in columns])

    def make_tables(self, value):
        return self._make_tables(value)

    #        if not self._cached_table:
    #            table = self._make_tables(value)
    #            self._cached_table = table[0]
    #        else:
    #            for i, vi in enumerate(value):
    #                for ci, args in enumerate(self.columns):
    #                    if len(args) == 3:
    #                        fmt = args[2]
    #                    else:
    #                        fmt = floatfmt
    #                    try:
    #                        self._cached_table.items[i + 1].cells[ci].text = fmt(getattr(vi, args[1]))
    #                    except IndexError:
    #                        self._cached_table.items.append(TextRow(*[self._cell_factory(vi, args)
    #                                                                  for args in self.columns]))
    #        return [self._cached_table]

    def _make_tables(self, value):
        raise NotImplementedError

    def _cell_factory(self, obj, args):
        fmt = floatfmt
        width = 12
        if len(args) == 3:
            _, li, fmt = args
        elif len(args) == 4:
            _, li, fmt, width = args
        else:
            _, li = args

        if fmt is None:
            fmt = floatfmt

        return TextCell(getattr(obj, li),
                        width=width,
                        format=fmt)

    def _header_cell_factory(self, args):
    #        if len(args) == 3:
    #            ci, _, _ = args
    #        else:
    #            ci, _ = args

        if len(args) == 4:
            ci, _, _, width = args
            return TextCell(ci, width=width)
        else:
            return TextCell(args[0])


class SimpleTextTableAdapter(TextTableAdapter):
    def _make_tables(self, value):
        return [self._make_signal_table(value)]

    def _make_signal_table(self, sg, columns=None):
        if columns is None:
            columns = self.columns

        rs = [self._make_header_row(columns=columns)]
        rs.extend(
            [TextRow(*[self._cell_factory(ri, args) for args in columns])
             for ri in sg]
        )
        tt = TextTable(border=True,
                       *rs
        )
        return tt


class MultiTextTableAdapter(SimpleTextTableAdapter):
    '''
        columns should be 2D
    '''

    def _make_tables(self, value):
        return [self._make_signal_table(value,
                                        ci
        )
                for ci in self.columns
        ]

#    def _make_signal_table(self, sg, columns):
#        rs = [self._make_header_row()]
#        rs.extend(
#                   [TextRow(*[self._cell_factory(ri, args)
#                              for args in self.columns])
#                                for ri in sg]
#                   )
#        tt = TextTable(border=True,
#                       *rs
#                       )
#        return tt

class ValueErrorAdapter(TextTableAdapter):
    columns = [
        ('', 'name', str, 20),
        ('Value', 'value', None, 20),
        (u'{}1s'.format(PLUSMINUS), 'error', None, 20),
    ]

    def _make_tables(self, value):
        rs = [self._make_header_row(),
        ]
        #        for vi in value:
        # #            ri = TextRow(
        # #                         self._cell_factory(vi, (None, 'name', str, 10)),
        # #                         self._cell_factory(vi, (None, 'value', None, 12)),
        # #                         self._cell_factory(vi, (None, 'error', None, 12)),
        # #                         )
        #            ri =
        #            rs.append(ri)
        rs.extend([TextRow(*[self._cell_factory(vi, args) for args in self.columns])
                   for vi in value])

        tt = TextTable(border=True, *rs)
        return [tt]


class RatiosAdapter(ValueErrorAdapter):
    columns = [
        ('Ratio', 'name', str, 20),
        ('Value', 'value', None, 20),
        (u'{}1s'.format(PLUSMINUS), 'error', None, 20),
    ]


#============= EOF =============================================
