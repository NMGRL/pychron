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
# ============= standard library imports ========================
import os

from chaco.api import PlotLabel
from chaco.svg_graphics_context import SVGGraphicsContext
from kiva.ps import PSGC
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from reportlab.pdfbase import _fontdata
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import TypeFace
from reportlab.pdfbase.ttfonts import TTFont, TTFError
from traitsui.handler import Controller

from pychron import pychron_constants

# ============= local library imports  ==========================
from pychron.core.helpers.filetools import view_file, add_extension, unique_path2
from pychron.core.pdf.options import BasePDFOptions, PDFLayoutView
from pychron.core.pdf.pdf_graphics_context import PdfPlotGraphicsContext

from kiva.api import Font, NORMAL

for face in pychron_constants.TTF_FONTS:
    for face_name in (face, face.lower()):
        spec = Font(face_name=face_name, style=NORMAL, weight=NORMAL).findfont()
        try:
            if isinstance(spec, str):
                tf = TTFont(face_name, spec)
            else:
                tf = TTFont(
                    face_name.lower(), spec.filename, subfontIndex=spec.face_index
                )
            pdfmetrics.registerFont(tf)
            break
        except TTFError as e:
            print("invalid font", spec, e)
            pdfmetrics.registerFont(TTFont(face_name, "Vera.tff"))


class myPdfPlotGraphicsContext(PdfPlotGraphicsContext):
    def get_full_text_extent(self, textstring):
        fontname = self.gc._fontname
        fontsize = self.gc._fontsize

        try:
            ascent, descent = _fontdata.ascent_descent[fontname]
        except KeyError:
            ascent, descent = (718, -207)

        # get the AGG extent (we just care about the descent)
        aw, ah, ad, al = self._agg_gc.get_full_text_extent(textstring)

        # ignore the descent returned by reportlab if AGG returned 0.0 descent
        descent = 0.0 if ad == 0.0 else descent * fontsize / 1000.0
        ascent = ascent * fontsize / 1000.0
        height = ascent + abs(descent)
        width = self.gc.stringWidth(textstring, fontname, fontsize)

        # the final return value is defined as leading. do not know
        # how to get that number so returning zero
        return width, height, descent, 0


class FigurePDFOptions(BasePDFOptions):
    pass


class SavePDFDialog(Controller):
    def traits_view(self):
        return PDFLayoutView


def save_pdf(component, path=None, default_directory=None, view=False, options=None):
    if default_directory is None:
        default_directory = os.path.join(os.path.expanduser("~"), "Documents")

    ok = True
    if options is None:
        ok = False
        options = FigurePDFOptions()
        options.load()
        dlg = SavePDFDialog(model=options)
        info = dlg.edit_traits(kind="livemodal")
        # path = '/Users/ross/Documents/pdftest.pdf'
        if info.result:
            options.dump()
            ok = True
    if ok:
        if path is None:
            dlg = FileDialog(action="save as", default_directory=default_directory)

            if dlg.open() == OK:
                path = dlg.path

        if path:
            use_ps = False
            use_svg = False
            if use_ps:
                path = add_extension(path, ".ps")
                gc = PSGC(component.bounds)
                component.draw(gc)
                gc.save(path)
            elif use_svg:
                path = add_extension(path, ".svg")
                gc = SVGGraphicsContext(component.bounds)
                obackbuffer = component.use_backbuffer
                component.use_backbuffer = False
                gc.render_component(component)
                gc.save(path)
                component.use_backbuffer = obackbuffer

            else:
                path = add_extension(path, ".pdf")
                gc = myPdfPlotGraphicsContext(
                    filename=path, dest_box=options.dest_box, pagesize=options.page_size
                )

                obounds = component.bounds
                print(
                    "obounds",
                    obounds,
                    options.valign,
                    options.halign,
                    options.page_size,
                    options.dest_box,
                )
                # if component not yet drawn e.g. no bounds then force render
                if (not obounds[0] and not obounds[1]) or options.fit_to_page:
                    size = options.bounds
                    component.do_layout(size=size, force=True)

                gc.render_component(
                    component, valign=options.valign, halign=options.halign
                )
                gc.save()
                if view:
                    view_file(path)

                if options.fit_to_page:
                    component.do_layout(size=obounds, force=True)


if __name__ == "__main__":
    from traits.api import HasTraits, Button, Instance
    from traitsui.api import View
    from pychron.graph.graph import Graph
    from pychron.paths import paths

    paths.build("_dev")

    class Demo(HasTraits):
        test = Button("Test")
        save = Button("Save")
        graph = Instance(Graph)

        def _graph_default(self):
            g = Graph(
                container_dict={
                    "padding_top": 15 * 4,
                    "bgcolor": "purple",
                    # 'bounds': [500,500],
                    "spacing": 10,
                    "resizable": "",
                    "padding_bottom": 40,
                }
            )
            p = g.new_plot(padding=[80, 10, 10, 40], resizable="", bounds=(100, 100))
            txt = "gooiooi \u03AE \u00ae \u00a3"
            txt2 = "aaaaaa \xb1 \u00b1"

            pl = PlotLabel(txt, overlay_position="inside bottom", font="Helvetica 12")
            pl2 = PlotLabel(
                txt2,
                x=100,
                y=100,
                overlay_position="inside bottom",
                font="Helvetica 24",
            )

            s, p = g.new_series([1, 2, 3, 4, 5, 6], [10, 21, 34, 15, 133, 1])
            s.overlays.append(pl)
            s.overlays.append(pl2)
            return g

        def _save_fired(self):
            p, cnt = unique_path2("/Users/ross/Desktop", "foo", extension=".pdf")
            save_pdf(self.graph.plotcontainer, path=p, view=True)

        def _test_fired(self):
            self.graph.window_width = 800
            self.graph.window_height = 600
            self.graph.edit_traits()
            # self.graph.plotcontainer.bounds = [600, 600]
            # self.graph.plotcontainer.do_layout(force=True)

    d = Demo()
    d.configure_traits(view=View("test", "save"))
# ============= EOF =============================================
