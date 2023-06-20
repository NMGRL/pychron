# ===============================================================================
# Copyright 2023 Jake Ross
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
from chaco.abstract_overlay import AbstractOverlay
from enable.component import Component
from enable.tools.drag_tool import DragTool
from numpy import array, polyfit, polyval
from traits.api import (
    HasTraits,
    Instance,
    Int,
    Tuple,
    Event,
    List,
    Float,
    Property,
    Bool,
)
from traitsui.api import View, UItem, HGroup, HSplit, VGroup, Item
from chaco.tools.api import MoveTool
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.formatting import floatfmt
from pychron.graph.graph import Graph
from pychron.graph.stacked_graph import StackedGraph
from pychron.processing.argon_calculations import (
    calculate_f,
    age_equation,
    get_isochron_regressors,
)


class PointDraggingTool(DragTool):
    component = Instance(Component)

    # The pixel distance from a point that the cursor is still considered
    # to be 'on' the point
    threshold = Int(5)

    # The index of the point being dragged
    _drag_index = Int(-1)

    # The original dataspace values of the index and value datasources
    # corresponding to _drag_index
    _orig_value = Tuple

    def is_draggable(self, x, y):
        # Check to see if (x,y) are over one of the points in self.component
        if self._lookup_point(x, y) is not None:
            return True
        else:
            return False

    def normal_mouse_move(self, event):
        plot = self.component

        ndx = plot.map_index((event.x, event.y), self.threshold)
        if ndx is None:
            if "selections" in plot.index.metadata:
                del plot.index.metadata["selections"]
        else:
            plot.index.metadata["selections"] = [ndx]

        plot.invalidate_draw()
        plot.request_redraw()

    def drag_start(self, event):
        plot = self.component
        ndx = plot.map_index((event.x, event.y), self.threshold)
        if ndx is None:
            return
        self._drag_index = ndx
        self._orig_value = (
            plot.index.get_data()[ndx],
            plot.value.get_data()[ndx],
        )

    def dragging(self, event):
        plot = self.component

        data_x, data_y = plot.map_data((event.x, event.y))

        plot.index._data[self._drag_index] = data_x
        plot.value._data[self._drag_index] = data_y
        plot.index.data_changed = True
        plot.value.data_changed = True
        plot.request_redraw()

    def drag_cancel(self, event):
        plot = self.component
        plot.index._data[self._drag_index] = self._orig_value[0]
        plot.value._data[self._drag_index] = self._orig_value[1]
        plot.index.data_changed = True
        plot.value.data_changed = True
        plot.request_redraw()

    def drag_end(self, event):
        plot = self.component
        if "selections" in plot.index.metadata:
            del plot.index.metadata["selections"]
        plot.invalidate_draw()
        plot.request_redraw()

    def _lookup_point(self, x, y):
        """Finds the point closest to a screen point if it is within self.threshold

        Parameters
        ==========
        x : float
            screen x-coordinate
        y : float
            screen y-coordinate

        Returns
        =======
        (screen_x, screen_y, distance) of datapoint nearest to the input *(x,y)*.
        If no data points are within *self.threshold* of *(x,y)*, returns None.
        """

        if hasattr(self.component, "get_closest_point"):
            # This is on BaseXYPlots
            return self.component.get_closest_point((x, y), threshold=self.threshold)

        return None


class IsochronMoveTool(PointDraggingTool):
    updated = Event

    def dragging(self, event):
        super().dragging(event)
        self.updated = True

    def drag_end(self, event):
        self.updated = True


def calculate_spectrum(ar39s, values):
    xs = []
    ys = []
    es = []
    sar = sum(ar39s)
    prev = 0
    c39s = []
    # steps = []
    for i, (aa, ar) in enumerate(zip(values, ar39s)):
        if isinstance(aa, tuple):
            ai, ei = aa
        else:
            if aa is None:
                ai, ei = 0, 0
            else:
                ai, ei = nominal_value(aa), std_dev(aa)

        xs.append(prev)

        # if i in excludes:
        #     ei = 0
        #     ai = ys[-1]

        ys.append(ai)
        es.append(ei)
        try:
            s = 100 * ar / sar + prev
        except ZeroDivisionError:
            s = 0
        c39s.append(s)
        xs.append(s)
        ys.append(ai)
        es.append(ei)
        prev = s

    return array(xs), array(ys), array(es), array(c39s), array(ar39s), array(values)


class AnalysisAdapter(TabularAdapter):
    columns = [("Ar40", "ar40"), ("Ar39", "ar39"), ("Ar36", "ar36"), ("Rad40", "rad40")]

    ar40_text = Property
    ar39_text = Property
    ar36_text = Property
    rad40_text = Property

    def _get_ar40_text(self):
        return self._get_value("ar40")

    def _get_ar39_text(self):
        return self._get_value("ar39")

    def _get_ar36_text(self):
        return self._get_value("ar36")

    def _get_rad40_text(self):
        return self._get_value("rad40")

    def _get_value(self, key):
        return floatfmt(getattr(self.item, key))


class Analysis(HasTraits):
    ar40 = Float
    ar39 = Float
    ar36 = Float

    @property
    def rad40(self):
        return (self.ar40 - self.ar36 * 295.5) / self.ar40 * 100


IATM = 1 / 295.5


class TieLineOverlay(AbstractOverlay):
    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            xs = other_component.index.get_data()
            ys = other_component.value.get_data()
            gc.set_line_width(1)
            gc.set_stroke_color((0, 0, 1))

            x0, y0 = (0, IATM)

            for i, (x, y) in enumerate(zip(xs, ys)):
                coeffs = polyfit((y0, y), (x0, x), 1)
                xint = polyval(coeffs, (0,))

                ((x1, y1), (x2, y2)) = other_component.map_screen([(x0, y0), (xint, 0)])

                gc.move_to(x1, y1)
                gc.line_to(x2, y2)
                gc.draw_path()

    def update(self, ans):
        pass


class IsochronSandbox(HasTraits):
    spec = Instance(StackedGraph)
    isochron = Instance(Graph)

    analyses = List
    refresh_table = Event
    j = 1e-3

    show_tie_lines = Bool(True)
    tie_lines_overlay = Instance(TieLineOverlay)

    def init(self):
        self.spec = StackedGraph(
            container_dict=dict(padding=5, spacing=5, bgcolor="lightgray")
        )
        self.isochron = Graph()

        # plot the spectrum

        self.analyses = [
            Analysis(ar40=10, ar39=1.5, ar36=0.001),
            Analysis(ar40=10, ar39=1.1, ar36=0.0015),
            Analysis(ar40=10, ar39=1, ar36=0.0018),
        ]

        ar40 = array([a.ar40 for a in self.analyses])
        ar39 = array([a.ar39 for a in self.analyses])
        ar36 = array([a.ar36 for a in self.analyses])

        fs = [
            calculate_f((a40, a39, 0, 0, a36), decay_time=0)
            for a40, a39, a36 in zip(ar40, ar39, ar36)
        ]
        ages = [age_equation(self.j, f[0]) for f in fs]
        xs, ys, es, c39s, s39, vs = calculate_spectrum(ar39, ages)
        self.spec.new_plot()
        self.spec.new_series(xs, ys)
        self.spec.set_y_limits(min(ys), max(ys), pad="0.1", plotid=0)

        rad40s = [a.rad40 for a in self.analyses]
        xs, ys, es, c39s, s39, vs = calculate_spectrum(ar39, rad40s)
        self.spec.new_plot(padding=[60, 40, 30, 10])
        self.spec.new_series(xs, ys, plotid=1)
        self.spec.set_y_limits(min(ys), max(ys), pad="0.1", plotid=1)

        reg, regx = get_isochron_regressors(ar40, ar39, ar36)

        self.isochron.new_plot()
        iso, p = self.isochron.new_series(
            reg.xs, reg.ys, type="scatter", marker="circle", marker_size=5
        )

        to = TieLineOverlay(component=iso)
        iso.overlays.append(to)
        self.tie_lines_overlay = to

        # iso.selection_marker = "circle"
        # iso.selection_marker_size = 5
        tool = IsochronMoveTool(component=iso)
        iso.tools.append(tool)
        tool.on_trait_change(self.update_spec, "updated")
        # iso.index.on_trait_change(self.update_spec, "data_changed")
        # iso.value.on_trait_change(self.update_spec, "data_changed")

        self.isochron.set_x_limits(0, max(reg.xs), pad="0.1", pad_style="upper")
        self.isochron.set_y_limits(0, 1 / 295.5, pad="0.1", pad_style="upper")

        self.isochron.set_y_title("Ar36/Ar40")
        self.isochron.set_x_title("Ar39/Ar40")

        self.spec.set_x_title("Cumulative %39Ar")
        self.spec.set_y_title("Apparent Age (Ma)", plotid=0)
        self.spec.set_y_title("*Ar40%", plotid=1)

        self.ar40 = array([a.ar40 for a in self.analyses])

    # def updated_index(self, obj, name, old, new):
    #     self._update('index', obj, name, old, new)

    # def updated_value(self, obj, name, old, new):
    def update_spec(self):
        # a3640 = obj.get_data()
        ar40 = self.ar40
        isochron = self.isochron.plots[0].plots["plot0"][0]
        a3940 = isochron.index.get_data()
        a3640 = isochron.value.get_data()

        ar36 = [ai * a40 for ai, a40 in zip(a3640, ar40)]
        ar39 = [ai * a40 for ai, a40 in zip(a3940, ar40)]

        for a, a36, a39 in zip(self.analyses, ar36, ar39):
            a.ar36 = a36
            a.ar39 = a39

        fs = [
            calculate_f((a40, a39, 0, 0, a36), decay_time=0)
            for a40, a39, a36 in zip(ar40, ar39, ar36)
        ]
        ages = [age_equation(self.j, f[0]) for f in fs]
        xs, ys, es, c39s, s39, vs = calculate_spectrum(ar39, ages)

        specplot = self.spec.plots[0].plots["plot0"][0]
        specplot.index.set_data(xs)
        specplot.value.set_data(ys)
        self.spec.set_y_limits(min(ys), max(ys), pad="0.1", plotid=1)

        # radiogenic yield
        rad40s = [a.rad40 for a in self.analyses]
        xs, ys, es, c39s, s39, vs = calculate_spectrum(ar39, rad40s)

        specplot = self.spec.plots[1].plots["plot0"][0]
        specplot.index.set_data(xs)
        specplot.value.set_data(ys)
        self.spec.set_y_limits(min(ys), max(ys), pad="0.1", plotid=1)

        if self.show_tie_lines:
            self.tie_lines_overlay.update(self.analyses)

        self.refresh_table = True

        # self._update('value', obj, name, old, new)

    # def _update(self, key, obj, name, old, new):
    # print('updated', key, obj, name, old, new)
    # source = getattr(specplot, key)
    # source.set_data(new)

    def traits_view(self):
        v = View(
            HSplit(
                UItem(
                    "analyses",
                    width=300,
                    editor=TabularEditor(
                        refresh="refresh_table",
                        stretch_last_section=False,
                        adapter=AnalysisAdapter(),
                    ),
                ),
                VGroup(
                    Item("show_tie_lines", label="Tie Lines"),
                    HGroup(
                        UItem("spec", style="custom"), UItem("isochron", style="custom")
                    ),
                ),
            ),
            title="Isochron Sandbox",
            resizable=True,
        )
        return v


def main():
    s = IsochronSandbox()
    s.init()
    s.configure_traits()


if __name__ == "__main__":
    main()

# ============= EOF =============================================
