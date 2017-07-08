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
# ============= standard library imports ========================
import os

from kiva.fonttools.font_manager import findfont, FontProperties
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from traitsui.handler import Controller

from pychron.core.helpers.filetools import view_file, add_extension
# ============= local library imports  ==========================
from pychron.core.pdf.options import BasePDFOptions, PDFLayoutView
from pychron.core.pdf.pdf_graphics_context import PdfPlotGraphicsContext

# register helvetica.
# Enable sets the font name to lowercase but Reportlab fonts are case-sensitive

pdfmetrics.registerFont(TTFont('helvetica', findfont(FontProperties(family='Helvetica',
                                                                    style='normal',
                                                                    weight='normal'))))

pdfmetrics.registerFont(TTFont('arial', findfont(FontProperties(family='Arial',
                                                                style='normal',
                                                                weight='normal'))))


class FigurePDFOptions(BasePDFOptions):
    pass


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
