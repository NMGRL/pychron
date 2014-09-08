# ===============================================================================
# Copyright 2011 Jake Ross
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



#=============enthought library imports=======================
from Image import Image
from traits.api import Any, Bool, Event, Str
from traitsui.qt4.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory
from PySide.QtGui import QLabel, QImage, QPixmap, QScrollArea
from pyface.image_resource import ImageResource
from traitsui.ui_traits import convert_bitmap as traitsui_convert_bitmap

from pychron.core.ui.gui import invoke_in_main_thread



#=============standard library imports ========================

# import math
#=============local library imports  ==========================
# from ctypes_opencv import  cvCreateImage, CvSize, cvAddS, CvScalar, \
# CvRect, cvSetImageROI, cvResize, cvResetImageROI
# from ctypes_opencv.cxcore import cvZero

def convert_bitmap(image, width=None, height=None):
    pix = None
    if isinstance(image, ImageResource):
        pix = traitsui_convert_bitmap(image)
    elif isinstance(image, Image):
        # image = image.convert('RGBA')
        data = image.tostring('raw', 'RGBA')
        im = QImage(data, image.size[0], image.size[1], QImage.Format_ARGB32)
        pix = QPixmap.fromImage(QImage.rgbSwapped(im))
    else:
        s = image.shape
        if len(s) >= 2:
            im = QImage(image.tostring(),
                        s[1], s[0],
                        QImage.Format_RGB888)
            pix = QPixmap.fromImage(QImage.rgbSwapped(im))
        else:
            pix = QPixmap()
    if pix:
        if width > 0 and height > 0:
            pix = pix.scaled(width, height)
        elif width > 0:
            pix = pix.scaledToWidth(width)
        if height > 0:
            pix = pix.scaledToHeight(height)

    return pix


class _ImageEditor(Editor):
    image_ctrl = Any
    refresh = Event

    def init(self, parent):
        image = self.factory.image
        if image is None:
            image = self.value

        image_ctrl = QLabel()

        #         w = self.item.width
        #        if self.factory.scale:
        #            w *= self.factory.scale
        if image is not None:
            image_ctrl.setPixmap(convert_bitmap(image))
        self.image_ctrl = image_ctrl

        if self.factory.scrollable:
            scroll_area = QScrollArea()
            scroll_area.setWidget(image_ctrl)
            scroll_area.setWidgetResizable(True)
            scroll_area.setMinimumWidth(self.item.width)
            scroll_area.setMinimumHeight(self.item.height)

            self.control = scroll_area
        else:
            self.control = self.image_ctrl

        self.set_tooltip()

        self.sync_value(self.factory.refresh, 'refresh', 'from')

    def _refresh_fired(self):
        print 'reasfasd'
        self.update_editor()

    def update_editor(self):
        image = self.factory.image
        if image is None:
            image = self.value

        qsize = self.image_ctrl.size()
        if self.factory.scale:
            w = qsize.width()
        else:
            w = None

        invoke_in_main_thread(self.set_pixmap, image, w)

    def set_pixmap(self, image, w):
        if image is not None:
            im = convert_bitmap(image, w)
            if im:
                self.image_ctrl.setPixmap(im)
            else:
                self.image_ctrl.setText('No Image')


class ImageEditor(BasicEditorFactory):
    """
    """
    klass = _ImageEditor
    image = Any
    scrollable = Bool(False)
    scale = Bool(True)
    refresh = Str
