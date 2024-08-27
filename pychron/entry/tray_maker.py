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
from traitsui.api import UItem, TableEditor, HGroup, HSplit
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
        return self.x, self.y, self.radius * 2, str(self.id)

    def dump(self, inches=False):
        x, y = self.x, self.y
        if inches:
            x /= 25.4
            y /= 25.4

        return "{},{:0.5f},{:0.5f}".format(self.id, x, y)


class TrayMaker(Loggable):
    canvas = Instance(IrradiationCanvas, ())
    positions = List
    add_position_button = Button
    refresh_button = Button
    names = List
    name = RestrictedStr(name="names")
    save_button = Button

    def gen(self):
        # rows = [
        #     (5, -2),
        #     (9, -4),
        #     (13, -6),
        #     (15, -7),
        #     (17, -8),
        #     (19, -9),
        #     (19, -9),
        #     (21, -10),
        #     (21, -10),
        #     (23, -11),
        #     (23, -11),
        #     (23, -11),
        #     (23, -11),
        #     (23, -11),
        #     (21, -10),
        #     (21, -10),
        #     (19, -9),
        #     (19, -9),
        #     (17, -8),
        #     (15, -7),
        #     (13, -6),
        #     (9, -4),
        #     (5, -2),
        # ]

        rows = [
            (3, -1),
            (5, -2),
            (7, -3),
            (7, -3),
            (7, -3),
            (5, -2),
            (3, -1),
        ]

        space = 6.75
        oy = 20.25
        ps = []
        for ri, (rc, ox) in enumerate(rows):
            y = oy - ri * space
            for ji in range(rc):
                x = (ox * space) + ji * space
                p = Position(x=x, y=y, radius=2.25)
                ps.append(p)
                print(x, y)

        self.positions = ps

    def holes(self):
        return [p.totuple() for p in self.positions]

    def _add_position_button_fired(self):
        p = Position()
        self.positions.append(p)

    def _save_button_fired(self):
        out = "out.txt"
        with open(out, "w") as wfile:
            wfile.write("circle, 0.02\n")
            wfile.write("\n\n")
            for p in self.positions:
                wfile.write("{}\n".format(p.dump("inches")))

    @on_trait_change("positions[], positions:[x,y]")
    def _positions_changed(self):
        for i, p in enumerate(self.positions):
            p.id = i + 1

        self.canvas.load_scene(self.holes())
        self.canvas.invalidate_and_redraw()

    def traits_view(self):
        cols = [ObjectColumn(name="id"), ObjectColumn(name="x"), ObjectColumn(name="y")]

        v = okcancel_view(
            HGroup(
                icon_button_editor("add_position_button", "add"),
                icon_button_editor("save_button", "save"),
            ),
            UItem("name"),
            HSplit(
                UItem("positions", width=0.25, editor=TableEditor(columns=cols)),
                UItem("canvas", width=0.75, editor=ComponentEditor()),
            ),
            width=900,
            height=900,
        )
        return v


if __name__ == "__main__":
    t = TrayMaker()
    t.gen()
    t.names = ["a", "bc"]
    t.configure_traits()
# ============= EOF =============================================
