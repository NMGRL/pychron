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

'''
    modified from chaco.image_inspector
'''
# ============= enthought library imports =======================
from enable.api import BaseTool, KeySpec
from traits.api import Any, Bool, Enum, Event, Tuple
# ============= standard library imports ========================
# ============= local library imports  ==========================

# Enthought library imports

# Chaco imports
from chaco.api import  TextBoxOverlay


class XYInspector(BaseTool):
    """ A tool that captures the color and underlying values of an image plot.
    """

    # This event fires whenever the mouse moves over a new image point.
    # Its value is a dict with a key "color_value", and possibly a key
    # "data_value" if the plot is a color-mapped image plot.
    new_value = Event

    # Indicates whether overlays listening to this tool should be visible.
    visible = Bool(True)

    # Stores the last mouse position.  This can be used by overlays to
    # position themselves around the mouse.
    last_mouse_position = Tuple

    # This key will show and hide any ImageInspectorOverlays associated
    # with this tool.
    inspector_key = KeySpec('p')

    # Stores the value of self.visible when the mouse leaves the tool,
    # so that it can be restored when the mouse enters again.
    _old_visible = Enum(None, True, False)  # Trait(None, Bool(True))

    def normal_key_pressed(self, event):
        if self.inspector_key.match(event):
            self.visible = not self.visible
            event.handled = True

    def normal_mouse_leave(self, event):
        if self._old_visible is None:
            self._old_visible = self.visible
            self.visible = False

    def normal_mouse_enter(self, event):
        if self._old_visible is not None:
            self.visible = self._old_visible
            self._old_visible = None

    def normal_mouse_move(self, event):
        """ Handles the mouse being moved.

        Fires the **new_value** event with the data (if any) from the event's
        position.
        """
        plot = self.component
        if plot is not None:
#            ndx = plot.map_index((event.x, event.y))
#            if ndx == (None, None):
#                self.new_value = None
#                return

            pos = plot.map_data((event.x, event.y), all_values=True)
#            x_index, y_index = ndx
            self.new_value = dict(pos=pos)
#            self.last_mouse_position = (event.x, event.y)


class XYInspectorOverlay(TextBoxOverlay):
    """ An overlay that displays a box containing values from an
    ImageInspectorTool instance.
    """
    # An instance of ImageInspectorTool; this overlay listens to the tool
    # for changes, and updates its displayed text accordingly.
    inspector = Any

    # Anchor the text to the mouse?  (If False, then the text is in one of the
    # corners.)  Use the **align** trait to determine which corner.
    tooltip_mode = Bool(False)

    # The default state of the overlay is invisible (overrides PlotComponent).
    visible = False

    # Whether the overlay should auto-hide and auto-show based on the
    # tool's location, or whether it should be forced to be hidden or visible.
    visibility = Enum("auto", True, False)

    def _inspector_changed(self, old, new):
        if old:
            old.on_trait_event(self._new_value_updated, 'new_value', remove=True)
            old.on_trait_change(self._tool_visible_changed, "visible", remove=True)
        if new:
            new.on_trait_event(self._new_value_updated, 'new_value')
            new.on_trait_change(self._tool_visible_changed, "visible")
            self._tool_visible_changed()

    def _new_value_updated(self, event):
        if event is None:
            self.text = ""
            if self.visibility == "auto":
                self.visible = False
            return
        elif self.visibility == "auto":
            self.visible = True

        if self.tooltip_mode:
            self.alternate_position = self.inspector.last_mouse_position
        else:
            self.alternate_position = None

        d = event
        newstring = ""
#        if 'indices' in d:
#            newstring += '(%d, %d)' % d['indices'] + '\n'
#        if 'color_value' in d:
#            newstring += "(%d, %d, %d)" % tuple(map(int, d['color_value'][:3])) + "\n"
#        if 'data_value' in d:
#            newstring += str(d['data_value'])

        if 'pos' in d:
            newstring += '({:0.2f},{:0.2f})'.format(*d['pos'])

        self.text = newstring
        self.component.request_redraw()

    def _visible_changed(self):
        self.component.request_redraw()

    def _tool_visible_changed(self):
        self.visibility = self.inspector.visible
        if self.visibility != "auto":
            self.visible = self.visibility


# ============= EOF =============================================
