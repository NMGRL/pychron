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

from chaco.array_data_source import ArrayDataSource
from numpy import zeros_like, array, asarray, isinf, isnan
from pyface.message_dialog import warning
from pyface.timer.do_later import do_later
from traits.api import Property, on_trait_change, List, Array
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.formatting import floatfmt
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.core.regression.interpolation_regressor import InterpolationRegressor
from pychron.graph.explicit_legend import ExplicitLegend
from pychron.graph.offset_plot_label import OffsetPlotLabel
from pychron.pipeline.plot.plotter.series import BaseSeries
from pychron.pychron_constants import PLUSMINUS


def calc_limits(ys, ye, n):
    try:
        ymi = (ys - (ye * n)).min()
    except BaseException:
        ymi = 0
    try:
        yma = (ys + (ye * n)).max()
    except BaseException:
        yma = 0

    return ymi, yma


def unzip_data(data):
    try:
        return array([nominal_value(ri) for ri in data]), array(
            [std_dev(ri) for ri in data]
        )
    except ValueError as e:
        print(e)


class ReferencesSeries(BaseSeries):
    references = List
    sorted_references = Property(depends_on="references")
    show_current = True
    rxs = Array
    references_name = "References"
    xtitle = "Time (hrs)"
    _normalization_factor = 3600.0

    def set_interpolated_values(self, iso, reg, fit):
        mi, ma = self._get_min_max()
        # mi =
        ans = self.sorted_analyses

        xs = [(ai.timestamp - ma) / self._normalization_factor for ai in ans]
        p_uys = reg.predict(xs)
        p_ues = reg.predict_error(xs)

        if p_ues is None or any(isnan(p_ues)) or any(isinf(p_ues)):
            p_ues = zeros_like(xs)

        if p_uys is None or any(isnan(p_uys)) or any(isinf(p_uys)):
            p_uys = zeros_like(xs)

        self._set_interpolated_values(iso, fit, ans, p_uys, p_ues)
        return asarray(p_uys), asarray(p_ues)

    def post_make(self):
        self._fix_log_axes()
        do_later(self.graph.refresh)

    def plot(self, plots, legend=None):
        if plots:
            _, mx = self._get_min_max()

            self.xs = self._get_xs(plots, self.sorted_analyses, tzero=mx)
            self.rxs = self._get_xs(plots, self.sorted_references, tzero=mx)
            graph = self.graph
            for i, p in enumerate(plots):
                self._new_fit_series(i, p)
                self._add_plot_label(i, p)
                if self.options.show_statistics:
                    graph.add_statistics(plotid=i)

            mi, ma = self._get_min_max()
            self.xmi, self.xma = (mi - ma) / 3600.0, 0
            self.xpad = "0.1"

            legend = ExplicitLegend(
                plots=self.graph.plots[0].plots,
                labels=[
                    ("plot1", self.references_name),
                    ("data0", self.references_name),
                    ("plot0", "Unk. Current"),
                    ("Unknowns-predicted0", "Unk. Predicted"),
                ],
            )
            self.graph.plots[-1].overlays.append(legend)

    # private
    @on_trait_change("graph:regression_results")
    def _update_regression(self, new):
        key = "Unknowns-predicted{}"
        key = key.format(0)
        for plotobj, reg in new:
            if isinstance(reg, BaseRegressor):

                excluded = reg.get_excluded()
                for i, r in enumerate(self.sorted_references):
                    r.set_temp_status("omit" if i in excluded else "ok")

                self._set_values(plotobj, reg, key)

    def _get_signal_intensity(self, po, analysis):
        v, e = 0, 0
        iso = self._get_isotope(po, analysis)
        if iso:
            i = iso.get_intensity()
            v, e = nominal_value(i), std_dev(i)
        return v, e

    def _get_isotope(self, po, analysis):
        return analysis.get_isotope(po.name)

    def _calc_limits(self, ys, ye):
        return calc_limits(ys, ye, self.options.nsigma)

    def _add_plot_label(
        self, pid, po, overlay_position="inside top", hjustify="left", **kw
    ):
        txt = self._get_plot_label_text(po)
        if txt:
            comp = self.graph.plots[pid]
            pl = OffsetPlotLabel(
                txt,
                component=comp,
                overlay_position=overlay_position,
                hjustify=hjustify,
                **kw
            )
            comp.overlays.append(pl)

    def _get_plot_label_text(self, po):
        pass

    def _new_fit_series(self, pid, po):
        ymi, yma = self._plot_unknowns_current(pid, po)
        args = self._plot_references(pid, po)
        if args:
            reg, a, b = args
            ymi = min(ymi, a)
            yma = max(yma, b)
            if reg:
                a, b = self._plot_interpolated(pid, po, reg)
                ymi = min(ymi, a)
                yma = max(yma, b)

            self.graph.set_y_limits(ymi, yma, pad="0.05", plotid=pid)
        else:
            warning(
                None, "Invalid Detector choices for these analyses. {}".format(po.name)
            )

    def _get_min_max(self):
        mi = min(self.sorted_references[0].timestamp, self.sorted_analyses[0].timestamp)
        ma = max(
            self.sorted_references[-1].timestamp, self.sorted_analyses[-1].timestamp
        )
        return mi, ma

    def _get_sorted_references(self):
        return sorted(
            self.references,
            key=self._cmp_analyses,
            reverse=self._reverse_sorted_analyses,
        )

    def _set_values(self, plotobj, reg, key):
        iso = plotobj.isotope
        fit = plotobj.fit
        if key in plotobj.plots:
            scatter = plotobj.plots[key][0]
            p_uys, p_ues = self.set_interpolated_values(iso, reg, fit)
            scatter.value.set_data(p_uys)
            scatter.yerror.set_data(p_ues)
            scatter._layout_needed = True

    def reference_data(self, po):

        data = self._get_reference_data(po)
        if data:
            ans, xs, ys = data
            return (
                ans,
                array(xs),
                array([nominal_value(ri) for ri in ys]),
                array([std_dev(ri) for ri in ys]),
            )

    def current_data(self, po):
        data = self._get_current_data(po)
        return array([nominal_value(ri) for ri in data]), array(
            [std_dev(ri) for ri in data]
        )

    def _get_current_data(self, po):
        return self._unpack_attr(po.name)

    def _get_reference_data(self, po):
        raise NotImplementedError

    # plotting
    def _plot_unknowns_current(self, pid, po):
        ymi, yma = 0, 0

        if self.analyses and self.show_current:
            graph = self.graph
            n = [ai.record_id for ai in self.sorted_analyses]

            ys, ye = self.current_data(po)
            ymi, yma = self._calc_limits(ys, ye)

            scatter, plot = graph.new_series(
                x=self.xs,
                y=ys,
                yerror=ye,
                type="scatter",
                display_index=ArrayDataSource(data=n),
                fit=False,
                plotid=pid,
                bind_id=-2,
                add_tools=False,
                add_inspector=False,
                marker=po.marker,
                marker_size=po.marker_size,
            )

            def af(i, x, y, analysis):
                v, e = self._get_interpolated_value(po, analysis)
                s, se = self._get_signal_intensity(po, analysis)
                return (
                    "Interpolated: {} {} {}".format(
                        floatfmt(v), PLUSMINUS, floatfmt(e)
                    ),
                    "Run Date: {}".format(analysis.rundate.strftime("%m-%d-%Y %H:%M")),
                    "Rel. Time: {:0.4f}".format(x),
                    "Signal: {} {} {}".format(floatfmt(s), PLUSMINUS, floatfmt(se)),
                )

            self._add_error_bars(scatter, ye, "y", self.options.nsigma, True)
            self._add_scatter_inspector(
                scatter, add_selection=False, additional_info=af
            )
        return ymi, yma

    def _plot_interpolated(self, pid, po, reg, series_id=0):
        iso = po.name
        p_uys, p_ues = self.set_interpolated_values(iso, reg, po.fit)
        ymi, yma = 0, 0
        if len(p_uys):
            ymi, yma = self._calc_limits(p_uys, p_ues)

            graph = self.graph
            # display the predicted values
            s, p = graph.new_series(
                self.xs,
                p_uys,
                isotope=iso,
                yerror=ArrayDataSource(p_ues),
                fit=False,
                add_tools=False,
                add_inspector=False,
                type="scatter",
                marker=po.marker,
                marker_size=po.marker_size,
                plotid=pid,
                bind_id=-1,
            )
            series = len(p.plots) - 1
            graph.set_series_label(
                "Unknowns-predicted{}".format(series_id), plotid=pid, series=series
            )

            self._add_error_bars(s, p_ues, "y", self.options.nsigma, True)
        return ymi, yma

    def _plot_references(self, pid, po):
        graph = self.graph
        efit = po.fit.lower()
        # r_xs = self.rxs
        data = self.reference_data(po)
        if data:
            refs, r_xs, r_ys, r_es = data

            ymi, yma = self._calc_limits(r_ys, r_es)

            reg = None
            kw = dict(
                add_tools=True,
                add_inspector=True,
                add_point_inspector=False,
                add_selection=False,
                # color='red',
                plotid=pid,
                selection_marker=po.marker,
                marker=po.marker,
                marker_size=po.marker_size,
            )

            update_meta_func = None
            if efit in [
                "preceding",
                "bracketing interpolate",
                "bracketing average",
                "succeeding",
            ]:
                reg = InterpolationRegressor(xs=r_xs, ys=r_ys, yserr=r_es, kind=efit)
                kw["add_tools"] = False
                scatter, _p = graph.new_series(
                    r_xs, r_ys, yerror=r_es, type="scatter", fit=False, **kw
                )

                def update_meta_func(obj, b, c, d):
                    self.update_interpolation_regressor(po.name, reg, obj, refs)

                self._add_error_bars(scatter, r_es, "y", self.options.nsigma, True)

                ffit = po.fit
            else:
                bind_id = None
                if self.options.link_plots:
                    bind_id = hash(tuple([r.uuid for r in refs]))

                ffit = "{}_{}".format(po.fit, po.error_type)
                _, scatter, l = graph.new_series(
                    r_xs,
                    r_ys,
                    yerror=ArrayDataSource(data=r_es),
                    fit=ffit,
                    bind_id=bind_id,
                    **kw
                )
                if hasattr(l, "regressor"):
                    reg = l.regressor
                self._add_error_bars(scatter, r_es, "y", self.options.nsigma, True)

            def af(i, x, y, analysis):
                return (
                    "Run Date: {}".format(analysis.rundate.strftime("%m-%d-%Y %H:%M")),
                    "Rel. Time: {:0.4f}".format(x),
                )

            self._add_scatter_inspector(
                scatter,
                update_meta_func=update_meta_func,
                add_selection=True,
                additional_info=af,
                items=refs,
            )
            plot = graph.plots[pid]
            plot.isotope = po.name
            plot.fit = ffit
            scatter.index.metadata["selections"] = [
                i for i, r in enumerate(refs) if r.temp_selected
            ]
            return reg, ymi, yma

    def _set_interpolated_values(self, iso, fit, ans, p_uys, p_ues):
        pass

    def update_interpolation_regressor(self, isotope, reg, obj, references):
        sel = self._filter_metadata_changes(obj, references)
        reg.user_excluded = sel
        key = "Unknowns-predicted0"
        for plotobj in self.graph.plots:
            if hasattr(plotobj, "isotope"):
                if plotobj.isotope == isotope:
                    self._set_values(plotobj, reg, key)


# ============= EOF =============================================
