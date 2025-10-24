# ===============================================================================
# Copyright 2021 ross
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
from kiva.qpainter import GraphicsContext
from pychron.core.ui.dialogs import PrinterDialog


class PrinterGraphicsContext(GraphicsContext):
    def __init__(
        self,
        component,
        pagesize,
        is_landscape=False,
        scale_to_fit=True,
        halign="center",
        valign="top",
        *args,
        **kw
    ):
        super(PrinterGraphicsContext, self).__init__(pagesize, *args, **kw)

        x, y = component.outer_position
        x = -x
        y = -y
        width, height = component.outer_bounds
        print("asfdaf", is_landscape)
        page_width, page_height = pagesize
        if is_landscape:
            width, height = height, width
            # page_width, page_height = page_height, page_width

        # if page_width < 0:
        #     page_width += full_page_width - page_offset_x
        # if page_height < 0:
        #     page_height += full_page_height - page_offset_y

        if scale_to_fit:
            # Compute the correct scaling to fit the component into the
            # available canvas space while preserving aspect ratio.
            aspect = float(width) / float(height)
            if aspect >= page_width / page_height:
                # We are limited in width, so use widths to compute the scale
                # factor between pixels to page units.  (We want square pixels,
                # so we re-use this scale for the vertical dimension.)
                scale = float(page_width) / float(width)
                trans_width = page_width

                trans_height = height * scale
                trans_x = x * scale
                trans_y = y * scale
                if valign == "top":
                    trans_y += page_height - trans_height
                elif valign == "center":
                    trans_y += (page_height - trans_height) / 2.0

            else:
                # We are limited in height
                scale = page_height / height
                trans_height = page_height

                trans_width = width * scale
                trans_x = x * scale
                trans_y = y * scale
                if halign == "right":
                    trans_x += page_width - trans_width
                elif halign == "center":
                    trans_x += (page_width - trans_width) / 2.0

            self.translate_ctm(trans_x, trans_y)
            self.scale_ctm(scale, scale)

            # if is_landscape:
            # self.rotate_ctm(-math.pi/2)

        self.clip_to_rect(-x, -y, width, height)

        old_bb_setting = component.use_backbuffer
        component.use_backbuffer = False
        component.draw(self, view_bounds=(0, 0, width, height))
        component.use_backbuffer = old_bb_setting


def print_component(component):
    d = PrinterDialog()
    if d.open():
        # painter = QPainter()
        # painter.begin(d.printer)
        # painter.drawImage()
        # painter.end()
        PrinterGraphicsContext(
            component, d.pagesize(), is_landscape=d.is_landscape(), parent=d.printer
        )

        # gc = PdfPlotGraphicsContext(pagesize='landscape_letter', filename='fooprinter.pdf')
        # gc.render_component(component, valign='center')
        # gc.save()

        # doc = popplerqt4.Poppler.Document.load('fooprinter.pdf')
        # w, h = component.bounds
        # iamge = doc.page*
        # w = gc.width()
        # h = gc.height()
        # data = gc.pixel_map.convert_to_argb32string()
        # image = QtGui.QImage(data, w, h, QtGui.QImage.Format_ARGB32)
        # rect = QtCore.QRect(0, 0, w, h)
        # painter.drawImage(rect, image)


# ============= EOF =============================================
