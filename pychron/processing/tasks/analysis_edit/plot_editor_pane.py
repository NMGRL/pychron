# ===============================================================================
# Copyright 2013 Jake Ross
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

#============= enthought library imports =======================
from traits.api import Any, Event, Instance, List
from traitsui.api import View, UItem, Group, VGroup
from enable.base_tool import BaseTool
from chaco.abstract_overlay import AbstractOverlay
from enable.colors import ColorTrait
from pyface.tasks.traits_dock_pane import TraitsDockPane
from chaco.plot import Plot

from pychron.processing.tasks.plot_editor import PlotEditor, AnnotationEditor




#============= standard library imports ========================
#============= local library imports  ==========================
class SelectorTool(BaseTool):
    editor = Any
    editor_event = Event

    def normal_key_pressed(self, event):
        if event.character == 's':
            self._toggle_state()

    def select_key_pressed(self, event):
        self.normal_key_pressed(event)

    def _toggle_state(self):
        if self.event_state == 'normal':
            self.event_state = 'select'
            self.editor_event = self.editor
        else:
            self.event_state = 'normal'
            self.editor_event = None

        self.component.invalidate_and_redraw()


#     def normal_left_dclick(self, event):

#     def select_left_dclick(self, event):
#         self.event_state = 'normal'
#         self.editor_event = None
#         self.component.invalidate_and_redraw()

class SelectorOverlay(AbstractOverlay):
    tool = Any
    color = ColorTrait('green')

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        if self.tool.event_state == 'select':
            with gc:
                w, h = self.component.bounds
                x, y = self.component.x, self.component.y

                gc.set_stroke_color(self.color_)
                gc.set_line_width(4)
                gc.rect(x, y, w, h)
                gc.stroke_path()


def flatten_container(container):
    """
        input a nested container and
        return a list of Plots
    """
    return list(flatten(container))


def flatten(nested):
    try:
        if isinstance(nested, Plot):
            yield nested

        for sublist in nested.components:
            for element in flatten(sublist):
                yield element
    except AttributeError:
        pass
    except TypeError:
        yield nested


class PlotEditorPane(TraitsDockPane):
    component = Any
    analyses = Any

    name = 'Plot Editor'
    id = 'pychron.plot_editor'
    current_editor = Instance(PlotEditor)
    selectors = List
    index_attr = 'uage'

    annotation_editor = Instance(AnnotationEditor, ())
    suppress_pane_change = False

    def set_annotation_tool(self, tool):
        self.set_annotation_component(tool.component)

    def set_annotation_component(self, comp):
        self.annotation_editor.component = comp

    def _component_changed(self):
        if self.component:
            if hasattr(self.component, 'plotcontainer'):
                comp = self.component.plotcontainer
            else:
                comp = self.component

            ncomps = flatten_container(comp)
            if ncomps:
                self.selectors = []
                self.current_editor = None
                for plot in ncomps:
                    editor = PlotEditor(plot=plot)

                    if self.current_editor is None:
                        self.suppress_pane_change = True
                        self.current_editor = editor
                        self.suppress_pane_change = False

                    st = SelectorTool(comp, editor=editor)
                    st.on_trait_change(self.set_editor, 'editor_event')

                    so = SelectorOverlay(tool=st, component=plot)

                    plot.tools.append(st)
                    plot.underlays.append(so)
                    self.selectors.append(so)


    def set_editor(self, new):
        self.current_editor = new
        for overlay in self.selectors:
            if overlay.tool.editor != new:
                overlay.tool.event_state = 'normal'

        self.component.invalidate_and_redraw()

    def traits_view(self):
        annotation_grp = Group(
            UItem('annotation_editor',
                  style='custom'),
            label='Annotations')
        plot_grp = Group(
            UItem('current_editor',
                  style='custom'),
            label='Plot')

        v = View(VGroup(plot_grp, annotation_grp))
        return v

# ============= EOF =============================================
