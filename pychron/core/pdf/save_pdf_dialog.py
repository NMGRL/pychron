# ===============================================================================
# Copyright 2015 Jake Ross
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
# from chaco.pdf_graphics_context import PdfPlotGraphicsContext
from kiva.fonttools.font_manager import findfont, FontProperties
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import Enum, \
    Bool, Float
from traitsui.api import View, Item, HGroup, VGroup, Spring, spring
from traitsui.handler import Controller
# ============= standard library imports ========================
import os
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# ============= local library imports  ==========================
from pychron.core.pdf.options import BasePDFOptions, dumpable
from pychron.core.helpers.filetools import view_file, add_extension
from pychron.core.pdf.pdf_graphics_context import PdfPlotGraphicsContext

PAGE_MAP = {'A4': A4, 'letter': letter}
UNITS_MAP = {'inch': inch, 'cm': cm}
COLUMN_MAP = {'1': 1, '2': 0.5, '3': 0.33, '2/3': 0.66}


# register helvetica.
# Enable sets the font name to lowercase but Reportlab fonts are case-sensitive

pdfmetrics.registerFont(TTFont('helvetica', findfont(FontProperties(family='Helvetica',
                                                                    style='normal',
                                                                    weight='normal'))))

pdfmetrics.registerFont(TTFont('arial', findfont(FontProperties(family='Arial',
                                                                style='normal',
                                                                weight='normal'))))


class FigurePDFOptions(BasePDFOptions):
    fixed_width = dumpable(Float)
    fixed_height = dumpable(Float)

    page_type = dumpable(Enum('letter', 'A4'))
    units = dumpable(Enum('inch', 'cm'))
    use_column_width = dumpable(Bool(True))
    columns = dumpable(Enum('1', '2', '3', '2/3'))
    fit_to_page = dumpable(Bool)

    @property
    def bounds(self):
        units = UNITS_MAP[self.units]
        page = PAGE_MAP[self.page_type]
        if self.fit_to_page:
            if self.orientation == 'landscape':
                b = [page[1], page[0]]
            else:
                b = [page[0], page[1]]

            b[0] -= (self.left_margin+self.right_margin)*units
            b[1] -= (self.top_margin+self.bottom_margin)*units

        elif self.use_column_width:
            if self.orientation == 'landscape':
                page = landscape(page)
                width_margins = self.bottom_margin + self.top_margin
            else:
                width_margins = self.left_margin + self.right_margin

            fw = page[0]
            w = fw - width_margins * units
            # print 'cw', w, fw, width_margins, width_margins * units, COLUMN_MAP[self.columns]
            nw = w * COLUMN_MAP[self.columns]
            b = [nw, nw]
        else:
            b = [self.fixed_width * units, self.fixed_height * units]

        return b

    @property
    def page_size(self):
        orientation = 'landscape_' if self.orientation == 'landscape' else ''
        return '{}{}'.format(orientation, self.page_type)

    @property
    def dest_box(self):
        units = UNITS_MAP[self.units]
        if self.orientation == 'landscape':
            w, h = self.bounds
            lbrt = (self.bottom_margin, self.right_margin,
                    w / units + self.bottom_margin,
                    h / units + self.right_margin)
        else:
            w, h = self.bounds
            lbrt = (self.left_margin, self.bottom_margin,
                   w / units+self.left_margin,
                   h / units+self.bottom_margin)
            # lbrt = self.left_margin, self.bottom_margin, -self.right_margin, -self.top_margin
        # print map(lambda x: x*units, lbrt)
        # print 'lbrt', lbrt
        return lbrt


mgrp = VGroup(HGroup(Spring(springy=False, width=100),
                     Item('top_margin', label='Top'),
                     spring, ),
              HGroup(Item('left_margin', label='Left'),
                     Item('right_margin', label='Right')),
              HGroup(Spring(springy=False, width=100), Item('bottom_margin', label='Bottom'),
                     spring),
              label='Margins', show_border=True)
cgrp = VGroup()

sgrp = VGroup(Item('fit_to_page'),
              HGroup(Item('use_column_width', enabled_when='not fit_to_page'),
                     Item('columns', enabled_when='use_column_width')),
              HGroup(Item('fixed_width', label='W', enabled_when='not use_column_width and not fit_to_page'),
                     Item('fixed_height', label='H', enabled_when='not fit_to_page')),

              label='Size', show_border=True)
PDFLayoutView = View(Item('orientation'),
                     mgrp,
                     sgrp,
                     cgrp,
                     buttons=['OK', 'Cancel'],
                     title='PDF Save Options',
                     resizable=True)


class SavePDFDialog(Controller):
    def traits_view(self):
        return PDFLayoutView


def save_pdf(component, path=None, default_directory=None, view=False, options=None):
    if default_directory is None:
        default_directory = os.path.join(os.path.expanduser('~'), 'Documents')

    ok = True
    if options is None:
        ok = False
        options = FigurePDFOptions()
        options.load()
        dlg = SavePDFDialog(model=options)
        info = dlg.edit_traits(kind='livemodal')
        # path = '/Users/ross/Documents/pdftest.pdf'
        if info.result:
            options.dump()
            ok = True
    if ok:
        if path is None:
            dlg = FileDialog(action='save as', default_directory=default_directory)

            if dlg.open() == OK:
                path = dlg.path

        if path:
            path = add_extension(path, '.pdf')
            gc = PdfPlotGraphicsContext(filename=path,
                                        dest_box=options.dest_box,
                                        pagesize=options.page_size)
            # component.inset_border = False
            # component.padding = 0
            # component.border_visible = True
            # component.border_width = 2
            # component.fill_padding = True
            # component.bgcolor = 'green'
            obounds = component.bounds
            size = None
            if not obounds[0] and not obounds[1]:
                size = options.bounds

            if options.fit_to_page:
                size = options.bounds

            component.do_layout(size=size, force=True)
            gc.render_component(component,
                                valign='center')
            gc.save()
            if view:
                view_file(path)
            component.do_layout(size=obounds, force=True)

# def render_pdf(component, options):
#     pass

# if __name__ == '__main__':
#     paths.build('_dev')
#
#
#     class Demo(HasTraits):
#         test = Button('Test')
#         graph = Instance(Graph)
#
#         def _graph_default(self):
#             g = Graph()
#             p = g.new_plot()
#             g.new_series([1, 2, 3, 4, 5, 6], [10, 21, 34, 15, 133, 1])
#             return g
#
#         def _test_fired(self):
#             self.graph.edit_traits()
#             # self.graph.plotcontainer.bounds = [600, 600]
#             # self.graph.plotcontainer.do_layout(force=True)
#             # save_pdf(self.graph.plotcontainer, path='/Users/ross/Desktop/foop.pdf')
#
#
#     d = Demo()
#     d.configure_traits(view=View('test'))
# ============= EOF =============================================
