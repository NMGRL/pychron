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
import os
import shutil
from operator import attrgetter

import yaml

from traits.api import (
    HasTraits,
    List,
    on_trait_change,
    Button,
    Float,
    Enum,
    Instance,
    Str,
    Bool,
    Color,
)
from traits.traits import Color
from traitsui.api import View, UItem, TableEditor
from traitsui.table_column import ObjectColumn

from pychron.canvas.canvas2D.scene.base_scene_loader import SWITCH_TAGS, RECT_TAGS
from pychron.canvas.canvas2D.scene.canvas_parser import CanvasParser
from pychron.canvas.canvas2D.scene.primitives.base import Primitive
from pychron.canvas.canvas2D.scene.primitives.connections import Connection
from pychron.canvas.canvas2D.scene.primitives.lasers import Laser
from pychron.canvas.canvas2D.scene.primitives.pumps import Turbo, IonPump
from pychron.canvas.canvas2D.scene.primitives.rounded import Spectrometer, Stage, Getter
from pychron.canvas.canvas2D.scene.primitives.valves import (
    BaseValve,
    Valve,
    Switch,
    ManualSwitch,
)
from pychron.loggable import Loggable
from pychron.pychron_constants import NULL_STR

ITEM_KLASS = {
    "Valve": Valve,
    "Spectrometer": Spectrometer,
    "Stage": Stage,
    "Connection": Connection,
}


class ItemGroup(HasTraits):
    name = Str
    items = List
    selected = List

    def traits_view(self):
        cols = [
            ObjectColumn(name="name", editable=False),
            ObjectColumn(name="x"),
            ObjectColumn(name="y"),
        ]

        v = View(
            UItem(
                "items",
                editor=TableEditor(
                    columns=cols, selected="selected", selection_mode="rows"
                ),
            ),
        )
        return v


class CanvasEditor(Loggable):
    groups = List

    selected_group = Instance(ItemGroup)

    increment_up_x = Button
    increment_down_x = Button

    increment_up_y = Button
    increment_down_y = Button

    save_button = Button("Save")
    x_magnitude = Enum(0.25, 0.5, 1, 2, 5, 10)
    y_magnitude = Enum(0.25, 0.5, 1, 2, 5, 10)

    width = Float
    height = Float

    width_increment_plus_button = Button
    width_increment_minus_button = Button
    height_increment_plus_button = Button
    height_increment_minus_button = Button

    color = Color
    add_item_button = Button("Add")
    new_item_kind = Enum(NULL_STR, "Valve", "Spectrometer", "Stage")
    new_item = Instance(Primitive)

    edit_mode = Bool(False)

    def load(self, canvas, path):
        self.canvas = canvas
        self.path = path
        self._valve_changes = []
        self._rect_changes = []

        self.x_magnitude = 1
        self.y_magnitude = 1

        vs = canvas.scene.valves
        rs = canvas.scene.rects

        self.groups = [
            ItemGroup(
                name="Valves",
                items=sorted(
                    [v for v in vs.values() if v.name], key=attrgetter("name")
                ),
            ),
            ItemGroup(
                name="Rects",
                items=sorted(
                    [v for v in rs.values() if v.name], key=attrgetter("name")
                ),
            ),
        ]
        self.selected_group = self.groups[0]

    def _increment(self, sign, axis):
        inc = sign * getattr(self, "{}_magnitude".format(axis))

        g = self.selected_group
        for s in g.selected:
            setattr(s, axis, getattr(s, axis) + inc)
            s.request_layout()

        self.canvas.scene.request_layout()
        self.canvas.invalidate_and_redraw()

    def _dim_increment(self, sign, dim):
        g = self.selected_group

        inc = sign
        for s in g.selected:
            setattr(s, dim, getattr(s, dim) + inc)

            self.width = s.width
            self.height = s.height

    def _new_item_kind_changed(self, new):
        if new and new != NULL_STR:
            self.new_item = ITEM_KLASS[new](0, 0)

    def _add_item_button_fired(self):
        item = self.new_item
        if item:
            if item.name:
                cp = CanvasParser(self.path)
                elem = cp.add(item.tag, item.name)
                cp.add("translation", "{},{}".format(item.x, item.y), elem)
                cp.add("dimension", "{},{}".format(item.width, item.width), elem)
                if item.tag in ("valve",):
                    self.canvas.scene.valves[item.name] = self.new_item
                elif item.tag in ("stage", "spectrometer"):
                    cp.add("color", "100,100,100", elem)
                self.canvas.scene.add_item(self.new_item)
                self.canvas.scene.request_layout()
                self.canvas.invalidate_and_redraw()
                cp.save()
            else:
                self.information_dialog("Please enter a name for the new item")

    def _edit_mode_changed(self, new):
        if self.canvas:
            self.canvas.edit_mode = new

    def _save_yaml(self, p):
        obj = {}
        items = [i.toyaml() for i in self.canvas.scene.valves.values()]
        obj["valve"] = items

        for klass, key in (
            (Switch, "switch"),
            # (Valve, "valve"),
            (ManualSwitch, "manual_valve"),
            (Turbo, "turbo"),
            (IonPump, "ionpump"),
            (Getter, "getter"),
            (Laser, "laser"),
            (Stage, "stage"),
            (Spectrometer, "spectrometer"),
        ):
            items = [i.toyaml() for i in self.canvas.scene.get_items(klass)]
            obj[key] = items

        for tag, orientation in (
            ("connection", NULL_STR),
            ("hconnection", "horizontal"),
            ("vconnection", "vertical"),
        ):
            obj[tag] = [
                i.toyaml()
                for i in self.canvas.scene.get_items(Connection)
                if i.orientation == orientation
            ]

        shutil.copyfile(p, "{}.bak".format(p))

        with open(p, "w") as wfile:
            yaml.dump(obj, wfile)

    def _save_button_fired(self):
        p = self.path
        if p.endswith(".yaml") or p.endswith(".yml"):
            self._save_yaml(p)
        else:
            yp = "{}.yaml".format(os.path.splitext(p)[0])

            self.warning_dialog(
                "The xml canvas format is deprecated. Please consider switching to YAML. "
                "Pychron will attempt to create a yaml file automatically at {}".format(
                    yp
                )
            )

            self._save_yaml(yp)
            cp = CanvasParser(self.path)
            for o in self._valve_changes:
                for t in SWITCH_TAGS:
                    elem = next(
                        (s for s in cp.get_elements(t) if s.text.strip() == o.name),
                        None,
                    )
                    if elem:
                        t = elem.find("translation")
                        t.text = "{},{}".format(o.x, o.y)
                        break

            for o in self._rect_changes:
                for t in RECT_TAGS:
                    elem = next(
                        (s for s in cp.get_elements(t) if s.text.strip() == o.name),
                        None,
                    )
                    if elem:
                        t = elem.find("translation")
                        t.text = "{},{}".format(o.x, o.y)
                        t = elem.find("dimension")
                        t.text = "{},{}".format(o.width, o.height)
                        t = elem.find("color")
                        if t:
                            t.text = "{},{},{}".format(*o.default_color.getRgb())
                        break
            cp.save()

    def _increment_up_x_fired(self):
        self._increment(1, "x")

    def _increment_down_x_fired(self):
        self._increment(-1, "x")

    def _increment_up_y_fired(self):
        self._increment(1, "y")

    def _increment_down_y_fired(self):
        self._increment(-1, "y")

    def _width_increment_plus_button_fired(self):
        self._dim_increment(1, "width")

    def _width_increment_minus_button_fired(self):
        self._dim_increment(-1, "width")

    def _height_increment_plus_button_fired(self):
        self._dim_increment(1, "height")

    def _height_increment_minus_button_fired(self):
        self._dim_increment(-1, "height")

    def _color_changed(self, new):
        item = self.selected_group.selected[0]
        item.default_color = tuple(255 * i for i in new)
        if self.selected_group.name == "Rects":
            if item not in self._rect_changes:
                self._rect_changes.append(item)

        self.canvas.invalidate_and_redraw()

    def _width_changed(self, new):
        item = self.selected_group.selected[0]
        item.width = new
        if self.selected_group.name == "Rects":
            self._rect_changes.append(item)

    def _height_changed(self, new):
        item = self.selected_group.selected[0]
        item.height = new
        if self.selected_group.name == "Rects":
            self._rect_changes.append(item)

    @on_trait_change("groups:selected")
    def _handle_selected(self, obj, name, old, new):
        if new:
            if self.selected_group.name == "Rects":
                self.width = new[0].width
                self.height = new[0].height
                self.color = new[0].default_color

    @on_trait_change("groups:items:[x,y,width,height]")
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
