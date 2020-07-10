# ===============================================================================
# Copyright 2020 ross
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
from enable.component_editor import ComponentEditor
from traits.api import Instance, HasTraits, Float, List, Int, on_trait_change, Button
from traitsui.api import UItem, TableEditor, HGroup
from traitsui.table_column import ObjectColumn

from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import RestrictedStr
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.loggable import Loggable


class Position(HasTraits):
    id = Int
    x = Float
    y = Float
    radius = Float(0.1)

    def totuple(self):
        return self.x, self.y, self.radius, str(self.id)


class TrayMaker(Loggable):
    canvas = Instance(IrradiationCanvas, ())
    positions = List
    add_position_button = Button
    refresh_button = Button
    names = List
    name = RestrictedStr(name='names')

    def holes(self):
        return [p.totuple() for p in self.positions]

    def _add_position_button_fired(self):
        p = Position()
        self.positions.append(p)

    @on_trait_change('positions[], positions:[x,y]')
    def _positions_changed(self):
        for i, p in enumerate(self.positions):
            p.id = i + 1

        self.canvas.load_scene(self.holes())
        self.canvas.invalidate_and_redraw()

    def traits_view(self):
        cols = [ObjectColumn(name='id'),
                ObjectColumn(name='x'),
                ObjectColumn(name='y')]

        v = okcancel_view(HGroup(icon_button_editor('add_position_button', 'add'), ),
                          UItem('name'),
                          UItem('positions', editor=TableEditor(columns=cols)),
                          UItem('canvas', editor=ComponentEditor()),
                          )
        return v


if __name__ == '__main__':
    t = TrayMaker()
    t.names = ['a', 'bc']
    t.configure_traits()
# ============= EOF =============================================
