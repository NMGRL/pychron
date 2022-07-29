# ===============================================================================
# Copyright 2015 Jake Ross
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
from itertools import groupby
from operator import attrgetter

from chaco.overlays.scatter_inspector_overlay import ScatterInspectorOverlay
from chaco.plots.scatterplot import ScatterPlot
from enable.component_editor import ComponentEditor
from numpy import poly1d, linspace
from pyface.action.menu_manager import MenuManager
from traits.api import (
    Int,
    Property,
    List,
    Instance,
    Event,
    Bool,
    Button,
    List,
    Set,
    Dict,
    Str,
)
from traitsui.api import (
    View,
    UItem,
    TabularEditor,
    VGroup,
    HGroup,
    Item,
    Tabbed,
    VSplit,
    EnumEditor,
)
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.envisage.tasks.base_editor import BaseTraitsEditor, grouped_name
from pychron.graph.graph import Graph
from pychron.graph.stacked_graph import StackedGraph
from pychron.graph.tools.point_inspector import PointInspector, PointInspectorOverlay
from pychron.options.layout import filled_grid
from pychron.options.options_manager import (
    RegressionSeriesOptionsManager,
    OptionsController,
)
from pychron.options.views.views import view
from pychron.pipeline.plot.figure_container import FigureContainer
from pychron.pipeline.plot.models.regression_series_model import RegressionSeriesModel
from pychron.pipeline.results.iso_evo import ISO_EVO_RESULT_ARGS
from pychron.pychron_constants import (
    PLUSMINUS_ONE_SIGMA,
    LIGHT_RED,
    LIGHT_YELLOW,
    BAD,
    GOOD,
)


class IsoEvolutionResultsAdapter(TabularAdapter):
    columns = [
        ("RunID", "record_id"),
        ("UUID", "display_uuid"),
        ("Isotope", "isotope"),
        ("Fit", "fit"),
        ("N", "nstr"),
        ("Intercept", "intercept_value"),
        (PLUSMINUS_ONE_SIGMA, "intercept_error"),
        ("%", "percent_error"),
        ("Regression", "regression_str"),
    ]
    font = "10"
    record_id_width = Int(80)
    isotope_width = Int(50)
    fit_width = Int(80)
    intercept_value_width = Int(120)
    intercept_error_width = Int(80)
    percent_error_width = Int(60)

    intercept_value_text = Property
    intercept_error_text = Property
    percent_error_text = Property

    def get_tooltip(self, obj, trait, row, column):
        item = getattr(obj, trait)[row]

        return item.tooltip

    def get_bg_color(self, obj, trait, row, column=0):
        color = None
        item = getattr(obj, trait)[row]
        if not obj.display_only_bad:
            if not item.goodness:
                color = LIGHT_RED

        if not item.class_:
            color = LIGHT_YELLOW

        return color

    def _get_intercept_value_text(self):
        return self._format_number("intercept_value")

    def _get_intercept_error_text(self):
        return self._format_number("intercept_error")

    def _get_percent_error_text(self):
        return self._format_number("percent_error", n=3)

    def _format_number(self, attr, **kw):
        if self.item.record_id:
            v = getattr(self.item, attr)
            r = floatfmt(v, **kw)
        else:
            r = ""
        return r


class IsoResultInspector(PointInspector):
    results = List

    # def _generate_select_event(self):
    #     inds = self.get_selected_index()
    #     self.select_event = self.results[inds[0]]

    def assemble_lines(self):
        lines = []
        if self.current_position:
            inds = self.get_selected_index()
            for i, ind in enumerate(inds):
                result = self.results[ind]
                lines.extend(result.hover_text)

        return lines


class IsoEvolutionResultsEditor(BaseTraitsEditor, ColumnSorterMixin):
    results = List
    refresh_needed = Event
    adapter = Instance(IsoEvolutionResultsAdapter, ())
    dclicked = Event
    display_only_bad = Bool
    view_bad_button = Button("View Flagged")
    view_selected_button = Button("View Selected")
    classify_good_button = Button("Classify Good")
    classify_bad_button = Button("Classify Bad")

    selected = List
    xarg = Str("intercept_value")
    yarg = Str("slope")
    xargs = List(ISO_EVO_RESULT_ARGS)
    yargs = List(ISO_EVO_RESULT_ARGS)
    graph = Instance(Graph)
    iso_evo_graph = Instance(Graph)
    _selected_set = Set

    def __init__(self, results, fits, *args, **kw):
        super(IsoEvolutionResultsEditor, self).__init__(*args, **kw)

        na = grouped_name([r.identifier for r in results if r.identifier])
        self.name = "IsoEvo Results {}".format(na)

        self.oresults = self.results = results
        self.fits = fits
        self._make_graph()
        self._make_iso_evo_graph()
        # self.results = sorted(results, key=lambda x: x.goodness)

    def _make_iso_evo_graph(self):
        g = Graph()
        g.new_plot(show_legend=True)
        g.set_y_title("Intensity")
        g.set_x_title("Time (s)")
        self.iso_evo_graph = g

    def _make_graph(self):
        results = self.results
        fits = self.fits
        # a = 0.0003
        # b = 0.5
        # c = 0.00005
        # d = 0.015
        isos = len({r.isotope for r in results})
        g = Graph(container_dict={"kind": "g", "shape": filled_grid(isos)})

        for i, fit in enumerate(self.fits):
            rs = [ri for ri in results if ri.isotope == fit.name]

            x, y = zip(*((getattr(r, self.xarg), getattr(r, self.yarg)) for r in rs))

            self.debug("add plot {}, {}".format(i, fit.name))
            p = g.new_plot()
            g.add_limit_tool(p, "x")
            g.add_limit_tool(p, "y")

            scatter, _ = g.new_series(x, y, plotid=i, type="scatter", marker="plus")

            inspector = IsoResultInspector(
                scatter,
                # use_pane=False,
                results=rs,
                # convert_index=convert_index,
                # index_tag=index_tag,
                # index_attr=index_attr,
                # value_format=value_format,
                # additional_info=additional_info
            )

            inspector.on_trait_change(self._handle_inspection, "inspector_event")
            pinspector_overlay = PointInspectorOverlay(
                component=scatter, tool=inspector
            )
            scatter.overlays.append(pinspector_overlay)
            scatter.tools.append(inspector)

            overlay = ScatterInspectorOverlay(scatter)
            scatter.overlays.append(overlay)

            # g.new_series(xx, yy, plotid=i)
            g.set_x_title(self.xarg, plotid=i)
            g.set_y_title(self.yarg, plotid=i)
            g.set_plot_title(fit.name, plotid=i)

        self.graph = g

    def _xarg_changed(self):
        self._make_graph()

    def _yarg_changed(self):
        self._make_graph()

    def _handle_inspection(self, obj, name, old, event):
        results = obj.results
        result = results[event.event_index]
        rid = "{}-{}".format(result.record_id, result.isotope)

        g = self.iso_evo_graph
        if event.event_type == "select":
            if rid not in self._selected_set:
                # an = result.analysis
                # iso = an.get_isotope(result.isotope)
                # print(result.isotope, iso)
                iso = result.isotope_obj
                x = iso.offset_xs
                y = iso.ys
                scatter, _ = g.new_series(x, y, type="scatter", marker_size=1.5)
                g.set_series_label(rid)

                fx = linspace(0, x.max() * 1.2)
                fy = iso.regressor.predict(fx)
                g.new_series(fx, fy, color=scatter.color)
                g.set_series_label("{}-fit".format(rid))
                self._selected_set.add(rid)
            else:
                self.iso_evo_graph.set_series_visibility(True, series=rid)
                self.iso_evo_graph.set_series_visibility(
                    True, series="{}-fit".format(rid)
                )
        elif event.event_type == "deselect":
            self.iso_evo_graph.set_series_visibility(False, series=rid)
            self.iso_evo_graph.set_series_visibility(False, series="{}-fit".format(rid))

        ymin = 1e20
        ymax = -1
        xmax = -1
        xmin = 1e20
        for ps in g.plots[0].plots.values():
            for p in ps:
                if p.visible and isinstance(p, ScatterPlot):
                    a, b = p.value.get_bounds()
                    ymin = min(ymin, a)
                    ymax = max(ymax, b)

                    a, b = p.index.get_bounds()
                    xmin = min(xmin, a)
                    xmax = max(xmax, b)

        g.set_y_limits(ymin, ymax, pad="0.1")
        g.set_x_limits(0, xmax, pad="0.1", pad_style="upper")
        g.redraw(force=True)

    def _view_selected_button_fired(self):
        ans = list({r.analysis for r in self.selected})

        self._show_results(ans)

    def _classify_good_button_fired(self):
        for s in self.selected:
            s.class_ = GOOD
            s.isotope_obj.class_ = GOOD

        self.refresh_needed = True

    def _classify_bad_button_fired(self):
        for s in self.selected:
            s.class_ = BAD
            s.isotope_obj.class_ = BAD
        self.refresh_needed = True

    def _view_bad_button_fired(self):
        ans = list({r.analysis for r in self.oresults if not r.goodness})
        self._show_results(ans)

    def _show_results(self, ans):

        c = FigureContainer()
        pom = RegressionSeriesOptionsManager()
        names = list({k for a in ans for k in a.isotope_keys})
        pom.set_names(names)
        pom.selected = "multiregression"

        info = OptionsController(model=pom).edit_traits(
            view=view("Regression Options"), kind="livemodal"
        )
        if info.result:
            m = RegressionSeriesModel(analyses=ans, plot_options=pom.selected_options)
            c.model = m
            v = View(
                UItem("component", style="custom", editor=ComponentEditor()),
                title="Regression Results",
                width=0.90,
                height=0.75,
                resizable=True,
            )

            c.edit_traits(view=v)

    def _display_only_bad_changed(self, new):
        if new:
            self.results = [r for r in self.results if not r.goodness]
        else:
            self.results = self.oresults

    def _dclicked_fired(self, new):
        if new:
            result = new.item
            result.analysis.show_isotope_evolutions((result.isotope,))

    def traits_view(self):
        filter_grp = HGroup(
            Item("display_only_bad", label="Show Flagged Only"),
            UItem("view_bad_button"),
            UItem("view_selected_button"),
            UItem("classify_good_button"),
            UItem("classify_bad_button"),
        )
        ggrp = VGroup(
            VSplit(
                VGroup(
                    HGroup(
                        Item("xarg", editor=EnumEditor(name="xargs")),
                        Item("yarg", editor=EnumEditor(name="yargs")),
                    ),
                    UItem("graph", style="custom"),
                ),
                UItem("iso_evo_graph", style="custom"),
            ),
            label="Graph",
        )
        tgrp = VGroup(
            filter_grp,
            UItem(
                "results",
                editor=TabularEditor(
                    adapter=self.adapter,
                    editable=False,
                    refresh="refresh_needed",
                    multi_select=True,
                    selected="selected",
                    column_clicked="column_clicked",
                    dclicked="dclicked",
                ),
            ),
            label="Table",
        )
        v = View(VGroup(Tabbed(ggrp, tgrp)))
        return v


# ============= EOF =============================================
