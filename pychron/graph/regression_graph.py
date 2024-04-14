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
# ============= enthought library imports =======================

from chaco.api import LinePlot
from chaco.api import TextBoxOverlay
from enable.component_editor import ComponentEditor
from numpy import linspace
from traits.api import List, Any, Event, Callable, Dict, Int, Bool
from traitsui.api import View, UItem

from pychron.core.helpers.fits import convert_fit
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.graph.context_menu_mixin import RegressionContextMenuMixin
from pychron.graph.error_envelope_overlay import ErrorEnvelopeOverlay
from pychron.graph.graph import Graph
from pychron.graph.tools.point_inspector import PointInspector, PointInspectorOverlay
from pychron.graph.tools.rect_selection_tool import (
    RectSelectionTool,
    RectSelectionOverlay,
)
from pychron.graph.tools.regression_inspector import (
    RegressionInspectorTool,
    RegressionInspectorOverlay,
    make_statistics,
    make_correlation_statistics,
)
from pychron.pychron_constants import AUTO_LINEAR_PARABOLIC, EXPONENTIAL


class StatisticsTextBoxOverlay(TextBoxOverlay):
    pass


class CorrelationTextBoxOverlay(TextBoxOverlay):
    pass


class NoRegressionCTX(object):
    def __init__(self, obj, refresh=False):
        self._refresh = refresh
        self._obj = obj

    def __enter__(self):
        self._obj.suppress_regression = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._obj.suppress_regression = False
        if self._refresh:
            self._obj.refresh()


class RegressionGraph(Graph, RegressionContextMenuMixin):
    _cached_hover = Dict
    _cached_sel = Dict
    indices = List
    filters = List
    selected_component = Any
    regression_results = Event
    suppress_regression = False

    use_data_tool = True
    use_inspector_tool = True
    use_point_inspector = True
    convert_index_func = Callable
    grouping = Int
    show_grouping = Bool

    # def __init__(self, *args, **kw):
    #     super(RegressionGraph, self).__init__(*args, **kw)
    #     self._regression_lock = Lock()

    # ===============================================================================
    # context menu handlers
    # ===============================================================================
    def cm_toggle_filtering(self):
        regs = {}
        for plot in self.plots:
            for k, v in plot.plots.items():
                if k.startswith("fit"):
                    pp = v[0]
                    # regs.append(pp.regressor)
                    regs[k[3:]] = pp.regressor

                    fo = pp.regressor.filter_outliers_dict["filter_outliers"]
                    pp.regressor.filter_outliers_dict["filter_outliers"] = not fo
                    pp.regressor.dirty = True
                    pp.regressor.calculate()
                # if hasattr(v[0], 'filter_outliers_dict'):
                #     fo = v[0].filter_outliers_dict['filter_outliers']
                #     v[0].filter_outliers_dict['filter_outliers'] = not fo
                # if not fo:
                #     v[0].index.metadata['selections'] = []
                # else:

        for plot in self.plots:
            for k, v in plot.plots.items():
                if k.startswith("data"):
                    scatter = v[0]
                    idx = k[4:]
                    reg = regs[idx]

                    fo = scatter.filter_outliers_dict["filter_outliers"]
                    scatter.filter_outliers_dict["filter_outliers"] = fo = not fo
                    self._set_regressor(scatter, reg)
                    scatter.index.metadata["selections"] = (
                        reg.get_excluded() if fo else []
                    )

        self.redraw()

    def cm_toggle_filter_bounds_all(self):
        for plot in self.plots:
            self.cm_toggle_filter_bounds(plot, redraw=False)
        self.redraw()

    def cm_toggle_filter_bounds(self, plot=None, redraw=True):
        if plot is None:
            plot = self.plots[self.selected_plotid]

        for k, v in plot.plots.items():
            if k.startswith("fit"):
                pp = v[0]
                pp.filter_bounds.visible = not pp.filter_bounds.visible

        if redraw:
            self.redraw()

    def cm_linear(self):
        self.set_fit("linear", plotid=self.selected_plotid)
        self._update_graph()

    def cm_parabolic(self):
        self.set_fit("parabolic", plotid=self.selected_plotid)
        self._update_graph()

    def cm_cubic(self):
        self.set_fit("cubic", plotid=self.selected_plotid)
        self._update_graph()

    def cm_quartic(self):
        self.set_fit("quartic", plotid=self.selected_plotid)
        self._update_graph()

    def cm_exponential(self):
        self.set_fit(EXPONENTIAL, plotid=self.selected_plotid)
        self._update_graph()

    def cm_auto_linear_parabolic(self):
        self.set_fit(AUTO_LINEAR_PARABOLIC, plotid=self.selected_plotid)
        self._update_graph()

    def cm_average_std(self):
        self.set_fit("average_std", plotid=self.selected_plotid)
        self._update_graph()

    def cm_average_sem(self):
        self.set_fit("average_sem", plotid=self.selected_plotid)
        self._update_graph()

    def cm_sd(self):
        self.set_error_calc_type("sd", plotid=self.selected_plotid)
        self._update_graph()

    def cm_sem(self):
        self.set_error_calc_type("sem", plotid=self.selected_plotid)
        self._update_graph()

    def cm_ci(self):
        self.set_error_calc_type("ci", plotid=self.selected_plotid)
        self._update_graph()

    def cm_mc(self):
        self.set_error_calc_type("mc", plotid=self.selected_plotid)
        self._update_graph()

    # ===============================================================================
    #
    # ===============================================================================
    def new_series(
        self,
        x=None,
        y=None,
        ux=None,
        uy=None,
        lx=None,
        ly=None,
        fx=None,
        fy=None,
        fit="linear",
        display_filter_bounds=False,
        filter_outliers_dict=None,
        use_error_envelope=True,
        truncate="",
        marker="circle",
        marker_size=2,
        add_tools=True,
        add_inspector=True,
        add_point_inspector=True,
        add_selection=True,
        convert_index=None,
        plotid=None,
        *args,
        **kw
    ):
        kw["marker"] = marker
        kw["marker_size"] = marker_size

        if plotid is None:
            plotid = len(self.plots) - 1

        if not fit:
            s, p = super(RegressionGraph, self).new_series(
                x, y, plotid=plotid, *args, **kw
            )
            if add_tools:
                self.add_tools(
                    p, s, None, convert_index, add_inspector, add_point_inspector
                )
            return s, p

        scatter, si = self._new_scatter(
            kw, marker, marker_size, plotid, x, y, fit, filter_outliers_dict, truncate
        )
        lkw = kw.copy()
        lkw["color"] = "black"
        lkw["type"] = "line"
        lkw["render_style"] = "connectedpoints"
        plot, names, rd = self._series_factory(fx, fy, plotid=plotid, **lkw)
        line = plot.plot(names, add=False, **rd)[0]
        line.index.sort_order = "ascending"
        self.set_series_label("fit{}".format(si), plotid=plotid)

        plot.add(line)
        plot.add(scatter)

        if use_error_envelope:
            self._add_error_envelope_overlay(line)

        o = self._add_filter_bounds_overlay(line)
        if filter_outliers_dict and display_filter_bounds:
            o.visible = True

        if x is not None and y is not None:
            if not self.suppress_regression:
                self._regress(plot, scatter, line)

        try:
            self._set_bottom_axis(plot, plot, plotid)
        except:
            pass

        if add_tools:
            self.add_tools(
                plot,
                scatter,
                line,
                convert_index,
                add_inspector,
                add_point_inspector,
                add_selection,
            )

        return plot, scatter, line

    def regression_inspector_factory(self, line):
        tool = RegressionInspectorTool(component=line)
        return tool

    def add_tools(
        self,
        plot,
        scatter,
        line=None,
        convert_index=None,
        add_inspector=True,
        add_point_inspector=True,
        add_selection=True,
    ):
        if add_inspector:
            # add a regression inspector tool to the line
            if line:
                tool = self.regression_inspector_factory(line)
                overlay = RegressionInspectorOverlay(component=line, tool=tool)
                line.tools.append(tool)
                line.overlays.append(overlay)

        if add_point_inspector:
            point_inspector = PointInspector(
                scatter, convert_index=convert_index or self.convert_index_func
            )
            pinspector_overlay = PointInspectorOverlay(
                component=scatter, tool=point_inspector
            )

            scatter.overlays.append(pinspector_overlay)
            scatter.tools.append(point_inspector)
        if add_selection:
            rect_tool = RectSelectionTool(scatter)
            rect_overlay = RectSelectionOverlay(tool=rect_tool)

            scatter.overlays.append(rect_overlay)
            scatter.tools.append(rect_tool)

    def add_correlation_statistics(self, plotid=0):
        plot = self.plots[plotid]
        for k, v in plot.plots.items():
            if k.startswith("fit"):
                pp = v[0]
                text = "\n".join(make_correlation_statistics(pp.regressor))
                label = CorrelationTextBoxOverlay(text=text, border_color="black")
                pp.overlays.append(label)
                break

    def add_statistics(self, plotid=0, options=None):
        plot = self.plots[plotid]
        for k, v in plot.plots.items():
            if k.startswith("fit"):
                pp = v[0]
                if hasattr(pp, "regressor"):
                    pp.statistics_options = options
                    text = "\n".join(make_statistics(pp.regressor, options=options))
                    label = StatisticsTextBoxOverlay(text=text, border_color="black")
                    pp.underlays.append(label)
                    break

    # def set_filter_outliers(self, fi, plotid=0, series=0):
    #     plot = self.plots[plotid]
    #     scatter = plot.plots['data{}'.format(series)][0]
    #     scatter.filter_outliers_dict['filter_outliers'] = fi
    #     self.redraw()

    # def get_filter_outliers(self, fi, plotid=0, series=0):
    #     plot = self.plots[plotid]
    #     scatter = plot.plots['data{}'.format(series)][0]
    #     return scatter.filter_outliers_dict['filter_outliers']

    def set_error_calc_type(self, fi, plotid=0, series=0, redraw=True):
        fi = fi.lower()
        plot = self.plots[plotid]
        key = "data{}".format(series)

        if key in plot.plots:
            scatter = plot.plots[key][0]
            f = scatter.fit
            if "_" in f:
                f = f.split("_")[0]
            scatter.fit = "{}_{}".format(f, fi)

    def set_fit(self, fi, plotid=0, series=0):
        fi = fi.lower()
        plot = self.plots[plotid]
        key = "data{}".format(series)
        if key in plot.plots:
            scatter = plot.plots[key][0]
            # print key
            if scatter.fit != fi:
                lkey = "fit{}".format(series)
                if lkey in plot.plots:
                    line = plot.plots[lkey][0]
                    line.regressor = None

                # print('fit for {}={}, {}'.format(key, fi, scatter))
                scatter.ofit = scatter.fit
                scatter.fit = fi

        else:
            print("invalid key", fi, plotid, key, plot.plots.keys())

    def get_fit(self, plotid=0, series=0):
        try:
            plot = self.plots[plotid]
            scatter = plot.plots["data{}".format(series)][0]
            return scatter.fit
        except IndexError:
            pass

    _outside_regressor = False

    def set_regressor(self, reg, plotid=0):
        self._outside_regressor = True
        plot = self.plots[plotid]
        for pp in plot.plots.values():
            for ppp in pp:
                if isinstance(ppp, LinePlot):
                    ppp.regressor = reg

    def clear(self):
        self.selected_component = None

        for p in self.plots:
            for pp in p.plots.values():
                if hasattr(pp, "error_envelope"):
                    pp.error_envelope.component = None
                    del pp.error_envelope

                if hasattr(pp, "regressor"):
                    del pp.regressor

        super(RegressionGraph, self).clear()

    def no_regression(self, refresh=False):
        return NoRegressionCTX(self, refresh=refresh)

    def refresh(self, **kw):
        self._update_graph()

    def update_metadata(self, obj, name, old, new):
        """
        fired when the index metadata changes e.i user selection
        """
        # don't update if hover metadata change
        if hasattr(obj, "suppress_hover_update"):
            if obj.suppress_hover_update:
                return

        self._update_graph()

    # private
    def _update_graph(self, *args, **kw):
        regs = []
        for i, plot in enumerate(self.plots):
            ps = plot.plots
            ks = list(ps.keys())
            try:
                scatters, idxes = list(
                    zip(*[(ps[k][0], k[4:]) for k in ks if k.startswith("data")])
                )

                fls = [ps["fit{}".format(idx)][0] for idx in idxes]
                for si, fl in zip(scatters, fls):
                    if not si.no_regression:
                        r = self._plot_regression(plot, si, fl)
                        regs.append((plot, r))

            except ValueError as e:
                # add a float instead of regressor to regs
                try:
                    si = ps[ks[0]][0]
                    regs.append((plot, si.value.get_data()[-1]))
                except IndexError:
                    break

        self.regression_results = regs

        # force layout updates. i.e for ErrorBarOverlay
        for plot in self.plots:
            for p in plot.plots.values():
                p[0]._layout_needed = True

        self.redraw(force=False)

    def _plot_regression(self, plot, scatter, line):
        if not plot.visible:
            return

        return self._regress(plot, scatter, line)

    def _regress(self, plot, scatter, line):
        fit, err = convert_fit(scatter.fit)
        if fit is None:
            return

        r = None
        if line and hasattr(line, "regressor"):
            r = line.regressor

        if fit in [1, 2, 3, 4, AUTO_LINEAR_PARABOLIC.lower()]:
            r = self._poly_regress(scatter, r, fit)
        elif fit == "exponential":
            r = self._exponential_regress(scatter, r, fit)
        elif fit.startswith("custom:"):
            r = self._least_square_regress(scatter, r, fit)
        elif isinstance(fit, tuple):
            r = self._least_square_regress(scatter, r, fit)
        elif isinstance(fit, BaseRegressor):
            r = self._custom_regress(scatter, r, fit)
        else:
            r = self._mean_regress(scatter, r, fit)

        if r:
            r.error_calc_type = err
            if line:
                plow = plot.index_range._low_value
                phigh = plot.index_range._high_value
                # print plow, phigh
                if hasattr(line, "regression_bounds") and line.regression_bounds:
                    low, high, first, last = line.regression_bounds
                    if first:
                        low = min(low, plow)
                    elif last:
                        high = max(high, phigh)
                else:
                    low, high = plow, phigh

                fx = linspace(low, high, 100)
                fy = r.predict(fx)

                line.regressor = r

                try:
                    line.index.set_data(fx)
                    line.value.set_data(fy)
                except BaseException as e:
                    print("Regerssion Exception, {}".format(e))
                    return

                if hasattr(line, "error_envelope"):
                    ci = r.calculate_error_envelope(fx, fy)
                    if ci is not None:
                        ly, uy = ci
                    else:
                        ly, uy = fy, fy

                    line.error_envelope.lower = ly
                    line.error_envelope.upper = uy
                    line.error_envelope.invalidate()

                if hasattr(line, "filter_bounds"):
                    ci = r.calculate_filter_bounds(fy)
                    if ci is not None:
                        ly, uy = ci
                    else:
                        ly, uy = fy, fy

                    line.filter_bounds.lower = ly
                    line.filter_bounds.upper = uy
                    line.filter_bounds.invalidate()

        return r

    def _set_regressor(self, scatter, r):
        selection = scatter.index.metadata["selections"]

        selection = set(selection) - set(r.outlier_excluded + r.truncate_excluded)

        x = scatter.index.get_data()
        y = scatter.value.get_data()
        sel = list(selection)
        if hasattr(scatter, "yerror"):
            yserr = scatter.yerror.get_data()
            r.trait_set(yserr=yserr)

        r.trait_set(
            xs=x,
            ys=y,
            user_excluded=sel,
            filter_outliers_dict=scatter.filter_outliers_dict,
        )
        r.dirty = True

    def _set_excluded(self, scatter, r):
        scatter.no_regression = True
        d = scatter.index.metadata.copy()
        d["selections"] = x = r.get_excluded()
        scatter.index.trait_setq(metadata=d)
        # scatter.invalidate_and_redraw()
        # scatter.index.metadata['selections'] = r.get_excluded()
        scatter.no_regression = False

    def _poly_regress(self, scatter, r, fit):
        from pychron.core.regression.ols_regressor import PolynomialRegressor
        from pychron.core.regression.wls_regressor import WeightedPolynomialRegressor

        if hasattr(scatter, "yerror") and any(scatter.yerror.get_data()):
            if r is None or not isinstance(r, WeightedPolynomialRegressor):
                r = WeightedPolynomialRegressor()
        else:
            if r is None or not isinstance(r, PolynomialRegressor):
                r = PolynomialRegressor()

        self._set_regressor(scatter, r)
        minpoints = 3
        r.trait_set(degree=fit)
        if isinstance(fit, int):
            minpoints = fit + 1

        if r.ys.shape[0] < minpoints:
            return

        r.set_truncate(scatter.truncate)
        r.determine_fit(fit)
        r.calculate()

        self._set_excluded(scatter, r)
        return r

    def _exponential_regress(self, scatter, r, fit):
        from pychron.core.regression.least_squares_regressor import (
            ExponentialRegressor,
            FitError,
        )

        if r is None or not isinstance(r, ExponentialRegressor):
            r = ExponentialRegressor()

        self._set_regressor(scatter, r)
        try:
            r.calculate()
            self._set_excluded(scatter, r)
        except FitError:
            f, e = convert_fit(scatter.ofit)
            r = self._poly_regress(scatter, r, f)

        return r

    def _least_square_regress(self, scatter, r, fit):
        from pychron.core.regression.least_squares_regressor import (
            LeastSquaresRegressor,
        )

        if r is None or not isinstance(r, LeastSquaresRegressor):
            r = LeastSquaresRegressor()

        self._set_regressor(scatter, r)
        if isinstance(fit, tuple):
            func, initial_guess = fit
            r.trait_setq(fitfunc=func, initial_guess=initial_guess)
        else:
            r.construct_fitfunc(fit)

        r.calculate()
        self._set_excluded(scatter, r)
        return r

    def _mean_regress(self, scatter, r, fit):
        from pychron.core.regression.mean_regressor import (
            MeanRegressor,
            WeightedMeanRegressor,
        )

        if hasattr(scatter, "yerror") and fit == "weighted mean":
            if r is None or not isinstance(r, WeightedMeanRegressor):
                r = WeightedMeanRegressor()
        else:
            if r is None or not isinstance(r, MeanRegressor):
                r = MeanRegressor()

        self._set_regressor(scatter, r)
        # r.trait_setq(fit=fit)
        r.calculate()

        self._set_excluded(scatter, r)
        return r

    def _custom_regress(self, scatter, r, fit):
        kw = {}
        if hasattr(scatter, "yerror"):
            es = scatter.yerror.get_data()
            kw["yserr"] = es

        if hasattr(scatter, "xerror"):
            es = scatter.xerror.get_data()
            kw["xserr"] = es

        if r is None or not isinstance(r, fit):
            r = fit()

        self._set_regressor(scatter, r)
        # r.trait_set(trait_change_notify=False,
        #             **kw)
        r.trait_setq(**kw)
        r.calculate()

        self._set_excluded(scatter, r)
        return r

    def _new_scatter(
        self, kw, marker, marker_size, plotid, x, y, fit, filter_outliers_dict, truncate
    ):
        kw["type"] = "scatter"
        plot, names, rd = self._series_factory(x, y, plotid=plotid, **kw)

        rd["selection_color"] = "white"
        rd["selection_outline_color"] = rd["color"]
        rd["selection_marker"] = marker
        rd["selection_marker_size"] = marker_size + 1
        scatter = plot.plot(names, add=False, **rd)[0]
        si = len([p for p in plot.plots.keys() if p.startswith("data")])

        self.set_series_label("data{}".format(si), plotid=plotid)
        if filter_outliers_dict is None:
            filter_outliers_dict = dict(filter_outliers=False)
        else:
            filter_outliers_dict = filter_outliers_dict.copy()

        scatter.fit = fit
        scatter.filter = None
        scatter.filter_outliers_dict = filter_outliers_dict
        scatter.truncate = truncate
        scatter.index.on_trait_change(self.update_metadata, "metadata_changed")
        scatter.no_regression = False

        return scatter, si

    def _add_filter_bounds_overlay(self, line):
        o = ErrorEnvelopeOverlay(component=line, use_region=True, color=(1))
        line.underlays.append(o)
        line.filter_bounds = o
        o.visible = False
        return o

    def _add_error_envelope_overlay(self, line):
        o = ErrorEnvelopeOverlay(component=line)
        line.underlays.append(o)
        line.error_envelope = o

    def _regression_results_changed(self):
        for plot in self.plots:
            for k, v in plot.plots.items():
                if k.startswith("fit"):
                    pp = v[0]
                    o = next(
                        (
                            oo
                            for oo in pp.underlays
                            if isinstance(oo, StatisticsTextBoxOverlay)
                        ),
                        None,
                    )
                    if o:
                        o.text = "\n".join(
                            make_statistics(pp.regressor, options=pp.statistics_options)
                        )
                        o.request_redraw()
                        break

                    o = next(
                        (
                            oo
                            for oo in pp.overlays
                            if isinstance(oo, CorrelationTextBoxOverlay)
                        ),
                        None,
                    )
                    if o:
                        o.text = "\n".join(make_correlation_statistics(pp.regressor))
                        o.request_redraw()
                        break

    def traits_view(self):
        v = View(
            UItem("grouping", defined_when="show_grouping"),
            UItem("plotcontainer", style="custom", editor=ComponentEditor()),
            title=self.window_title,
            width=self.window_width,
            height=self.window_height,
            x=self.window_x,
            y=self.window_y,
            resizable=self.resizable,
        )
        return v


# ============= EOF =============================================
