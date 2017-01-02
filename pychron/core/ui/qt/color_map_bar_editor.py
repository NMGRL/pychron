# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from chaco.data_range_1d import DataRange1D
from chaco.default_colormaps import color_map_dict, color_map_name_dict
from pyface.qt.QtGui import QPainter, QColor, QFrame
from traits.api import Float, Int, Str
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from numpy import array

# ============= local library imports  ==========================
# from matplotlib.cm import get_cmap


class Bar(QFrame):
    value = None
    low = 0
    high = 1
    color_scalar = 1
    colormap = 'jet'
    bar_width = 100
    scale = 'power'

    # def __init__(self, parent, ident=-1):
    #     super(Bar, self).__init__()
    #     self._cmap = get_cmap(self.colormap)

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(QColor(*self.value))
        qp.drawRect(0, 0, self.bar_width, 20)
        qp.end()

    def set_value(self, v):
        """
            map v to users color scale
            use power law v=A*x**(1/cs)
            increase cs increases the rate of change at low values
            increase cs will make it easier to see small pertubations (more color change) at
            the low end.

        """
        if self.scale == 'power':
            N = 1 / float(self.color_scalar)
            A = 1 / self.high ** N
            nv = A * v ** N
        else:
            nv = min(1, max(0, (v - self.low) / (self.high - self.low)))

        vs = self.cmap.map_screen(array([nv,]))[0][:3]
        self.value = map(lambda x: x * 255, vs)
        self.update()


class _BarGaugeEditor(Editor):
    def init(self, parent):
        self.control = Bar()
        self.control.low = self.factory.low
        self.control.high = self.factory.high
        self.control.color_scalar = self.factory.color_scalar
        self.control.bar_width = self.factory.width
        self.control.scale = self.factory.scale
        self.control.cmap = color_map_name_dict[self.factory.colormap](DataRange1D(low_setting=0, high_setting=255))

    def update_editor(self):
        if self.control:
            self.control.set_value(self.value)


class BarGaugeEditor(BasicEditorFactory):
    klass = _BarGaugeEditor
    low = Float
    high = Float
    color_scalar = Int(1)
    scale = Str('power')
    colormap = Str('jet')
    width = Int(100)

# ============= EOF =============================================
