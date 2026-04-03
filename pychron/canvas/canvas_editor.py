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
import copy
import os
import shutil
from operator import attrgetter
from typing import (
    Any as TypingAny,
    Dict as TypingDict,
    List as TypingList,
    Optional as TypingOptional,
)

import yaml
from pyface.ui_traits import PyfaceColor

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
    Int,
)

from traitsui.api import View, UItem, TableEditor, Item, HGroup, VGroup
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
                editor=TableEditor(columns=cols, selected="selected", selection_mode="rows"),
            ),
        )
        return v


class Command(HasTraits):
    """Base class for undoable commands."""

    name = Str
    _done = Bool(False)

    def do(self) -> None:
        self._done = True

    def undo(self) -> None:
        self._done = False


class MoveCommand(Command):
    """Command for moving items."""

    items = List
    old_positions = List
    new_positions = List

    def do(self) -> None:
        for item, (x, y) in zip(self.items, self.new_positions):
            item.x, item.y = x, y
            item.request_layout()
        self._done = True

    def undo(self) -> None:
        for item, (x, y) in zip(self.items, self.old_positions):
            item.x, item.y = x, y
            item.request_layout()
        self._done = False


class PropertyCommand(Command):
    """Command for changing a property on items."""

    items = List
    property_name = Str
    old_values = List
    new_values = List

    def do(self) -> None:
        for item, value in zip(self.items, self.new_values):
            setattr(item, self.property_name, value)
            item.request_layout()
        self._done = True

    def undo(self) -> None:
        for item, value in zip(self.items, self.old_values):
            setattr(item, self.property_name, value)
            item.request_layout()
        self._done = False


class UndoStack(HasTraits):
    """Undo/redo command stack."""

    _undo_stack: list[Command]
    _redo_stack: list[Command]
    max_depth = Int(50)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._undo_stack = []
        self._redo_stack = []

    def push(self, command: Command) -> None:
        if command._done:
            return
        if len(self._undo_stack) >= self.max_depth:
            self._undo_stack.pop(0)
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self) -> TypingOptional[Command]:
        if not self._undo_stack:
            return None
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return command

    def redo(self) -> TypingOptional[Command]:
        if not self._redo_stack:
            return None
        command = self._redo_stack.pop()
        command.do()
        self._undo_stack.append(command)
        return command

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)


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

    color = PyfaceColor
    add_item_button = Button("Add")
    new_item_kind = Enum(NULL_STR, "Valve", "Spectrometer", "Stage")
    new_item = Instance(Primitive)

    edit_mode = Bool(False)

    # Undo/redo
    undo_stack = Instance(UndoStack, ())
    undo_button = Button("Undo")
    redo_button = Button("Redo")

    # Selection info
    selection_count = Int
    selection_x = Float
    selection_y = Float
    selection_width = Float
    selection_height = Float
    selection_name = Str
    selection_description = Str

    # Alignment
    align_left_button = Button
    align_right_button = Button
    align_top_button = Button
    align_bottom_button = Button
    distribute_h_button = Button
    distribute_v_button = Button

    # Z-order
    bring_forward_button = Button
    send_backward_button = Button

    # Copy/paste
    copy_button = Button
    paste_button = Button
    duplicate_button = Button
    _clipboard: TypingList[TypingAny] = []

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
                items=sorted([v for v in vs.values() if v.name], key=attrgetter("name")),
            ),
            ItemGroup(
                name="Rects",
                items=sorted([v for v in rs.values() if v.name], key=attrgetter("name")),
            ),
        ]
        self.selected_group = self.groups[0]
        self.undo_stack.clear()

    def _increment(self, sign, axis):
        inc = sign * getattr(self, "{}_magnitude".format(axis))

        g = self.selected_group
        items = g.selected
        if not items:
            return

        old_positions = [(item.x, item.y) for item in items]
        for s in items:
            setattr(s, axis, getattr(s, axis) + inc)
            s.request_layout()

        new_positions = [(item.x, item.y) for item in items]

        cmd = MoveCommand(
            name="Move {}".format(axis),
            items=items,
            old_positions=old_positions,
            new_positions=new_positions,
        )
        cmd.do()
        self.undo_stack.push(cmd)

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

    def _validate_before_save(self) -> TypingList[str]:
        """Validate canvas state before saving. Returns list of error messages."""
        errors = []
        scene = self.canvas.scene

        # Check duplicate names
        names = []
        for item in scene.get_items():
            if hasattr(item, "name") and item.name:
                if item.name in names:
                    errors.append("Duplicate name: {}".format(item.name))
                names.append(item.name)

        # Check broken connections
        for conn in scene.get_items(Connection):
            if hasattr(conn, "start_point") and conn.start_point:
                pass  # Connections use Point objects, not name references

        # Check orphaned items (items with no layer)
        all_items = set()
        for layer in scene.layers:
            for item in layer.components:
                all_items.add(id(item))

        return errors

    def _save_button_fired(self):
        # Validate before saving
        errors = self._validate_before_save()
        if errors:
            msg = "Validation errors found:\n\n" + "\n".join(errors)
            msg += "\n\nSave anyway?"
            from pyface.api import confirm, YES

            if confirm(None, msg, "Validation Errors") != YES:
                return

        p = self.path
        if p.endswith(".yaml") or p.endswith(".yml"):
            self._save_yaml(p)
        else:
            yp = "{}.yaml".format(os.path.splitext(p)[0])

            self.warning_dialog(
                "The xml canvas format is deprecated. Please consider switching to YAML. "
                "Pychron will attempt to create a yaml file automatically at {}".format(yp)
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
        g = self.selected_group
        if not g.selected:
            return
        item = g.selected[0]
        old_color = item.default_color
        item.default_color = new

        cmd = PropertyCommand(
            name="Change Color",
            items=[item],
            property_name="default_color",
            old_values=[old_color],
            new_values=[item.default_color],
        )
        cmd.do()
        self.undo_stack.push(cmd)

        if self.selected_group.name == "Rects":
            if item not in self._rect_changes:
                self._rect_changes.append(item)

        self.canvas.invalidate_and_redraw()

    def _width_changed(self, new):
        g = self.selected_group
        if not g.selected:
            return
        item = g.selected[0]
        old_width = item.width
        item.width = new

        cmd = PropertyCommand(
            name="Change Width",
            items=[item],
            property_name="width",
            old_values=[old_width],
            new_values=[new],
        )
        cmd.do()
        self.undo_stack.push(cmd)

        if self.selected_group.name == "Rects":
            self._rect_changes.append(item)

    def _height_changed(self, new):
        g = self.selected_group
        if not g.selected:
            return
        item = g.selected[0]
        old_height = item.height
        item.height = new

        cmd = PropertyCommand(
            name="Change Height",
            items=[item],
            property_name="height",
            old_values=[old_height],
            new_values=[new],
        )
        cmd.do()
        self.undo_stack.push(cmd)

        if self.selected_group.name == "Rects":
            self._rect_changes.append(item)

    @on_trait_change("groups:selected")
    def _handle_selected(self, obj, name, old, new):
        if new:
            self.selection_count = len(new)
            if new:
                item = new[0]
                self.selection_x = item.x
                self.selection_y = item.y
                self.selection_width = item.width
                self.selection_height = item.height
                self.selection_name = getattr(item, "name", "")
                self.selection_description = getattr(item, "description", "")
                if self.selected_group.name == "Rects":
                    self.width = item.width
                    self.height = item.height
                    self.color = item.default_color

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

    # Undo/Redo

    def _undo_button_fired(self):
        cmd = self.undo_stack.undo()
        if cmd:
            self.canvas.scene.request_layout()
            self.canvas.invalidate_and_redraw()

    def _redo_button_fired(self):
        cmd = self.undo_stack.redo()
        if cmd:
            self.canvas.scene.request_layout()
            self.canvas.invalidate_and_redraw()

    # Alignment

    def _align_left_button_fired(self):
        self._align("x", "min")

    def _align_right_button_fired(self):
        self._align("x", "max")

    def _align_top_button_fired(self):
        self._align("y", "min")

    def _align_bottom_button_fired(self):
        self._align("y", "max")

    def _align(self, attr, mode):
        g = self.selected_group
        items = g.selected
        if len(items) < 2:
            return

        old_positions = [(item.x, item.y) for item in items]
        if mode == "min":
            target = min(getattr(item, attr) for item in items)
        else:
            target = max(
                getattr(item, attr)
                + getattr(item, attr.replace("x", "width").replace("y", "height"))
                for item in items
            )

        for item in items:
            if mode == "max":
                dim = "width" if attr == "x" else "height"
                setattr(item, attr, target - getattr(item, dim))
            else:
                setattr(item, attr, target)
            item.request_layout()

        new_positions = [(item.x, item.y) for item in items]
        cmd = MoveCommand(
            name="Align {}".format(attr),
            items=items,
            old_positions=old_positions,
            new_positions=new_positions,
        )
        cmd.do()
        self.undo_stack.push(cmd)
        self.canvas.scene.request_layout()
        self.canvas.invalidate_and_redraw()

    def _distribute_h_button_fired(self):
        self._distribute("x", "width")

    def _distribute_v_button_fired(self):
        self._distribute("y", "height")

    def _distribute(self, attr, dim_attr):
        g = self.selected_group
        items = sorted(g.selected, key=lambda i: getattr(i, attr))
        if len(items) < 3:
            return

        old_positions = [(item.x, item.y) for item in items]
        first = getattr(items[0], attr)
        last = getattr(items[-1], attr) + getattr(items[-1], dim_attr)
        step = (last - first) / (len(items) - 1)

        for i, item in enumerate(items[1:-1], 1):
            setattr(item, attr, first + i * step)
            item.request_layout()

        new_positions = [(item.x, item.y) for item in items]
        cmd = MoveCommand(
            name="Distribute {}".format("H" if attr == "x" else "V"),
            items=items,
            old_positions=old_positions,
            new_positions=new_positions,
        )
        cmd.do()
        self.undo_stack.push(cmd)
        self.canvas.scene.request_layout()
        self.canvas.invalidate_and_redraw()

    # Copy/Paste/Duplicate

    def _copy_button_fired(self):
        g = self.selected_group
        self._clipboard = list(g.selected)

    def _paste_button_fired(self):
        if not self._clipboard:
            return

        for item in self._clipboard:
            new_item = copy.copy(item)
            new_item.x += 1
            new_item.y += 1
            self.canvas.scene.add_item(new_item)
            new_item.request_layout()

        self.canvas.scene.request_layout()
        self.canvas.invalidate_and_redraw()

    def _duplicate_button_fired(self):
        g = self.selected_group
        items = g.selected
        if not items:
            return

        new_items = []
        for item in items:
            new_item = copy.copy(item)
            new_item.x += 1
            new_item.y += 1
            self.canvas.scene.add_item(new_item)
            new_items.append(new_item)

        self.canvas.clear_selection()
        self.canvas.selected_items = new_items
        for item in new_items:
            item.selected = True
            item.request_layout()

        self.canvas.scene.request_layout()
        self.canvas.invalidate_and_redraw()

    # Z-order

    def _bring_forward_button_fired(self):
        self._change_z_order(1)

    def _send_backward_button_fired(self):
        self._change_z_order(-1)

    def _change_z_order(self, direction):
        g = self.selected_group
        items = g.selected
        if not items:
            return

        scene = self.canvas.scene
        for layer in scene.layers:
            layer_items = [c for c in layer.components if c in items]
            for item in layer_items:
                idx = layer.components.index(item)
                new_idx = idx + direction
                if 0 <= new_idx < len(layer.components):
                    layer.components.remove(item)
                    layer.components.insert(new_idx, item)

        self.canvas.scene.request_layout()
        self.canvas.invalidate_and_redraw()


# ============= EOF =============================================
