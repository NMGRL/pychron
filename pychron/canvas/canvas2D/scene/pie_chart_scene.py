# ===============================================================================
# Copyright 2014 Jake Ross
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
import math
from enable.base import str_to_font
from traits.api import HasTraits, Button, Str, Int, Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.primitives import QPrimitive
from pychron.canvas.canvas2D.scene.scene import Scene
from matplotlib.cm import get_cmap

class PieChart(QPrimitive):
    def __init__(self, error_components, *args, **kw):
        super(PieChart, self).__init__(0,0,*args, **kw)
        self.error_components=error_components
        self.cmap = get_cmap('jet')

    def render(self, gc):
        names = [ei.name for ei in self.error_components]
        error_components = [ei.value for ei in self.error_components]
        ss=float(sum(error_components))
        pi2=math.pi*2
        angles = [si/ss*pi2 for si in error_components]
        percents = [si/ss for si in error_components]

        x,y=self.get_xy()
        gc.translate_ctm(x,y)

        r=self.map_dimension(22, keep_square=True)
        r2=self.map_dimension(25, keep_square=True)
        s=pi2/4.
        gc.set_font(str_to_font(None, None, '12'))
        for i,(ni, a, pp) in enumerate(zip(names,angles, percents)):
            with gc:
                with gc:
                    gc.set_fill_color(self.cmap(min(1, s/pi2)))
                    gc.move_to(0,0)
                    gc.line_to(0,r)
                    gc.arc(0,0, r, s, s+a)
                    gc.line_to(0,0)
                    gc.fill_path()

                if pp>0.01:
                    txt = '{} {:n}%'.format(ni,int(pp*100))
                    theta=a/2.0+s
                    gc.translate_ctm(-10,0)
                    x,y=r2*math.cos(theta),r2*math.sin(theta)

                    gc.set_fill_color((1,1,1))
                    gc.set_stroke_color((1,1,1))
                    w,h,_,_=gc.get_full_text_extent(txt)
                    gc.draw_rect((x-2,y-2,w+2,h+2))

                    gc.set_fill_color((0,0,0))
                    gc.set_text_position(x,y)
                    gc.show_text(txt)
                s+=a


class PieChartScene(Scene):
    def load(self, error_components):
        self.reset_layers()
        v=PieChart(error_components)
        self.add_item(v)
#============= EOF =============================================



