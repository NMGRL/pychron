# ===============================================================================
# Copyright 2019 ross
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
import smopy
from PIL import Image
from pyface.qt.QtGui import QPainter, QFrame, QPixmap, QImage
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class QMapWidget(QFrame):
    def __init__(self, *args, **kw):
        super(QMapWidget, self).__init__(*args, **kw)
        self._pix_maps = []
        # self._pix_map = QPixmap(self.width(), self.height())
        # self._pix_map.fill(Qt.transparent)

    def set_tile(self, image):

        data = image.tobytes('raw', 'RGB')

        im = QImage(data, image.size[0], image.size[1], QImage.Format_RGB888)
        pix = QPixmap.fromImage(im)

        self._pix_maps.append(pix)
        # print(self._pix_map)
        self.update()

    #
    # def resizeEvent(self, event):
    #     print('asdf', event.size().width())
    #     esize = event.size()
    #     csize = self._pix_map.size()
    #
    #     try:
    #
    #         print(csize.width(), esize.width(), csize.height(), esize.height())
    #         self._pix_map = self._pix_map.scaled(csize.width()/esize.width(),
    #                                              csize.height()/esize.height(),)
    #     except ZeroDivisionError:
    #         pass
    #
    #     # self.update()
    #     self.repaint()

    def paintEvent(self, event):
        super(QMapWidget, self).paintEvent(event)

        qp = QPainter()
        qp.begin(self)
        for p in self._pix_maps:
            qp.drawPixmap(0, 0, p)
        qp.end()

    # def set_screen(self):
    #     self._screen = QPixMap()


class _MapEditor(Editor):
    def init(self, parent):
        self.control = self._create_control(parent)

    def update_editor(self):
        if self.control:
            self.control.update()

    # def set_size_policy(self, direction, resizable, springy, stretch):
    #     pass

    def _create_control(self, parent):
        control = QMapWidget()
        # control.setMaximumSize(200,200)
        lat_min = 34.052999
        lon_min = -106.924551
        lat_max = 34.076752
        lon_max = -106.885971
        #
        # lat_min = 34.052999
        # lon_min = -106.81
        # lat_max = 34.08
        # lon_max = -106.83
        rect = (lat_min, lon_min, lat_max, lon_max)
        server = 'https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png'
        server = 'http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png'
        # server = 'https://c.tiles.wmflabs.org/hillshading/{z}/{x}{y}.png'
        # server = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'  # satelite
        # server = 'https://mt1.google.com/vt/lyrs=t&x={x}&y={y}&z={z}'  # terrain
        # server = 'https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}'  # maps

        smopy.TILE_SERVER = server
        m = smopy.Map(rect, z=10)
        # m = smopy.Map(rect)
        # m = smopy.Map(lat_min, lon_min, z=10, tileserver='http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png')

        # m.show_ipython()
        # control.set_tile(m.img)
        base = m.img
        base = base.convert('RGBA')
        base.putalpha(200)
        control.set_tile(base)

        # return control

        server = 'https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png'
        # server = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'  # satelite

        smopy.TILE_SERVER = server
        m = smopy.Map(rect, z=10)
        # img = m.img
        # img = img.convert('RGBA')
        # img.putalpha(128)
        # img = img.convert('RGB')

        img = m.img.convert('RGBA')
        img.putalpha(128)

        img = Image.alpha_composite(base, img)

        control.set_tile(img)
        # control.set_tile(Image.blend(base, l1, 129))
        # m.show_mpl()
        # from matplotlib.pyplot import show
        # show()

        # control.set_screen()
        return control


class MapViewEditor(BasicEditorFactory):
    klass = _MapEditor
# ============= EOF =============================================
