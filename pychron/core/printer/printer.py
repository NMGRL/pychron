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
import tempfile

from PyQt5.QtGui import QPainter
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
from enable.graphics_context import ImageGraphicsContextEnable
from kiva.qpainter import GraphicsContext
from pyface.qt import QtGui, QtCore

from pychron.core.ui.dialogs import PrinterDialog


def print_component(component):
    d = PrinterDialog()
    if d.open():
        print('asfd')
        print(d.printer)

        # painter = QPainter()
        # painter.begin(d.printer)
        # painter.drawImage()
        # painter.end()

        gc = GraphicsContext(component.bounds, parent=d.printer)
        component.draw(gc)

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
