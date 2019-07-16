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
from operator import attrgetter

from traits.api import HasTraits, List, on_trait_change, Button, Float, Enum, Instance, Str
from traitsui.api import View, UItem, TableEditor
from traitsui.table_column import ObjectColumn

from pychron.canvas.canvas2D.scene.canvas_parser import CanvasParser
from pychron.canvas.canvas2D.scene.extraction_line_scene import RECT_TAGS, SWITCH_TAGS
from pychron.canvas.canvas2D.scene.primitives.valves import BaseValve


class ItemGroup(HasTraits):
    name = Str
    items = List
    selected = List

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                ObjectColumn(name='x'),
                ObjectColumn(name='y')]

        v = View(UItem('items',
                       editor=TableEditor(columns=cols,
                                          selected='selected',
                                          selection_mode='rows')), )
        return v


class CanvasEditor(HasTraits):
    groups = List

    selected_group = Instance(ItemGroup)

    ex = Float
    ey = Float
    increment_up_x = Button
    increment_down_x = Button

    increment_up_y = Button
    increment_down_y = Button

    save_button = Button('Save')
    x_magnitude = Enum(0.25, 0.5, 1, 2, 5, 10)
    y_magnitude = Enum(0.25, 0.5, 1, 2, 5, 10)

    width = Float
    height = Float

    width_increment_plus_button = Button
    width_increment_minus_button = Button
    height_increment_plus_button = Button
    height_increment_minus_button = Button

    def load(self, canvas, path):
        self.canvas = canvas
        self.path = path
        self._valve_changes = []
        self._rect_changes = []

        self.x_magnitude = 1
        self.y_magnitude = 1

        vs = canvas.scene.valves
        rs = canvas.scene.rects

        self.groups = [ItemGroup(name='Valves',
                                 items=sorted([v for v in vs.values() if v.name], key=attrgetter('name'))),
                       ItemGroup(name='Rects',
                                 items=sorted([v for v in rs.values() if v.name], key=attrgetter('name')))]
        self.selected_group = self.groups[0]

    def _increment(self, sign, axis):
        inc = sign * getattr(self, '{}_magnitude'.format(axis))

        g = self.selected_group
        for s in g.selected:
            setattr(s, axis, getattr(s, axis) + inc)

    def _dim_increment(self, sign, dim):
        g = self.selected_group

        inc = sign
        for s in g.selected:
            setattr(s, dim, getattr(s, dim) + inc)

            self.width = s.width
            self.height = s.height

    def _save_button_fired(self):
        cp = CanvasParser(self.path)

        for o in self._valve_changes:
            for t in SWITCH_TAGS:
                elem = next((s for s in cp.get_elements(t) if s.text.strip() == o.name), None)
                if elem:
                    t = elem.find('translation')
                    t.text = '{},{}'.format(o.x, o.y)
                    break

        for o in self._rect_changes:
            for t in RECT_TAGS:
                elem = next((s for s in cp.get_elements(t) if s.text.strip() == o.name), None)
                if elem:
                    t = elem.find('translation')
                    t.text = '{},{}'.format(o.x, o.y)
                    t = elem.find('dimension')
                    t.text = '{},{}'.format(o.width, o.height)
                    break

        cp.save()

    def _increment_up_x_fired(self):
        self._increment(1, 'x')

    def _increment_down_x_fired(self):
        self._increment(-1, 'x')

    def _increment_up_y_fired(self):
        self._increment(1, 'y')

    def _increment_down_y_fired(self):
        self._increment(-1, 'y')

    def _width_increment_plus_button_fired(self):
        self._dim_increment(1, 'width')

    def _width_increment_minus_button_fired(self):
        self._dim_increment(-1, 'width')

    def _height_increment_plus_button_fired(self):
        self._dim_increment(1, 'height')

    def _height_increment_minus_button_fired(self):
        self._dim_increment(-1, 'height')

    @on_trait_change('groups:selected')
    def _handle_selected(self, obj, name, old, new):
        if new:
            if self.selected_group.name == 'Rects':
                self.width = new[0].width
                self.height = new[0].height

    @on_trait_change('groups:items:[x,y,width,height]')
    def _handle(self, obj, name, old, new):

        if isinstance(obj, BaseValve):
            if obj not in self._valve_changes:
                self._valve_changes.append(obj)
        else:
            if obj not in self._rect_changes:
                self._rect_changes.append(obj)

        obj.request_layout()
        self.canvas.invalidate_and_redraw()
# ============= EOF =============================================
