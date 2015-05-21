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
from traits.api import Property, on_trait_change, List, Array
# ============= standard library imports ========================
from math import isnan, isinf
from uncertainties import nominal_value, std_dev
from numpy import array, zeros_like
# ============= local library imports  ==========================
from pychron.core.regression.interpolation_regressor import InterpolationRegressor
from pychron.processing.plot.plotter.series import BaseSeries


class ReferencesSeries(BaseSeries):
    references = List
    sorted_references = Property(depends_on='references')
    show_current = True
    rxs = Array

    _normalization_factor = 3600.

    def set_interpolated_values(self, iso, reg, fit):
        mi, ma = self._get_min_max()
        # mi =
        ans = self.sorted_analyses

        xs = [(ai.timestamp - ma) / self._normalization_factor for ai in ans]

        p_uys = reg.predict(xs)
        p_ues = reg.predict_error(xs)

        if any(map(isnan, p_ues)) or any(map(isinf, p_ues)):
            p_ues = zeros_like(p_ues)

        if any(map(isnan, p_uys)) or any(map(isinf, p_uys)):
            p_uys = zeros_like(p_uys)

        self._set_interpolated_values(iso, fit, ans, p_uys, p_ues)
        return p_uys, p_ues

    def post_make(self):
        self.graph.refresh()

    def plot(self, plots, legend):
        if plots:
            _, mx = self._get_min_max()

            self.xs = self._get_xs(plots, self.sorted_analyses, tzero=mx)
            self.rxs = self._get_xs(plots, self.sorted_references, tzero=mx)

            for i, p in enumerate(plots):
                self._new_fit_series(i, p)

            mi, ma = self._get_min_max()
            self.xmi, self.xma = (mi - ma) / 3600., 0
            self.xpad = '0.1'

    # private
    @on_trait_change('graph:regression_results')
    def _update_regression(self, new):
        key = 'Unknowns-predicted{}'
        key = key.format(0)
        for plotobj, reg in new:
            self._set_values(plotobj, reg, key)

    def _handle_limits(self):
        self.graph.refresh()

    def _new_fit_series(self, pid, po):
        self._plot_unknowns_current(pid, po)
        reg = self._plot_references(pid, po)
        if reg:
            self._plot_interpolated(pid, po, reg)

    def _get_min_max(self):
        mi = min(self.sorted_references[0].timestamp, self.sorted_analyses[0].timestamp)
        ma = max(self.sorted_references[-1].timestamp, self.sorted_analyses[-1].timestamp)
        return mi, ma

    def _get_reference_values(self, name):
        ys = self._get_references_ve(name)
        return array(map(nominal_value, ys))

    def _get_reference_errors(self, name):
        ys = self._get_references_ve(name)
        return array(map(std_dev, ys))

    def _get_references_ve(self, name):
        raise NotImplementedError

    def _get_sorted_references(self):
        return sorted(self.references,
                      key=self._cmp_analyses,
                      reverse=self._reverse_sorted_analyses)

    def _set_values(self, plotobj, reg, key):
        iso = plotobj.isotope
        fit = plotobj.fit
        if key in plotobj.plots:
            scatter = plotobj.plots[key][0]
            p_uys, p_ues = self.set_interpolated_values(iso, reg, fit)
            scatter.value.set_data(p_uys)
            scatter.yerror.set_data(p_ues)

    # plotting
    def _plot_unknowns_current(self, pid, po):
        if self.analyses and self.show_current:
            graph = self.graph
            n = [ai.record_id for ai in self.sorted_analyses]
            ys = array([ai.nominal_value for ai in self._unpack_attr(po.name)])
            yerr = array([ai.std_dev for ai in self._unpack_attr(po.name)])
            kw = dict(y=ys, yerror=yerr, type='scatter')

            args = graph.new_series(x=self.xs,
                                    display_index=ArrayDataSource(data=n),
                                    fit=False,
                                    # fit=po.fit,
                                    plotid=pid,
                                    # type='scatter',
                                    add_tools=False,
                                    add_inspector=False,
                                    marker=po.marker,
                                    marker_size=po.marker_size, **kw)
            if len(args) == 2:
                scatter, p = args
            else:
                p, scatter, l = args

            sel = scatter.index.metadata.get('selections', [])
            # sel += omits
            scatter.index.metadata['selections'] = list(set(sel))

            def af(i, x, y, analysis):
                return ('Run Date: {}'.format(analysis.rundate.strftime('%m-%d-%Y %H:%M')),
                        'Rel. Time: {:0.4f}'.format(x))

            self._add_scatter_inspector(scatter,
                                        add_selection=False,
                                        additional_info=af)

            # self.graph.new_series([1,2,3,4], [2,3,4,1],
            #
            #                       plotid=i)

    def _plot_interpolated(self, pid, po, reg, series_id=0):
        iso = po.name
        p_uys, p_ues = self.set_interpolated_values(iso, reg, po.fit)
        if len(p_uys):
            graph = self.graph
            # display the predicted values
            s, p = graph.new_series(self.xs,
                                    p_uys,
                                    isotope=iso,
                                    yerror=ArrayDataSource(p_ues),
                                    fit=False,
                                    add_tools=False,
                                    add_inspector=False,
                                    type='scatter',
                                    marker_size=3,
                                    color='blue',
                                    plotid=pid,
                                    bind_id=-1)
            series = len(p.plots) - 1
            graph.set_series_label('Unknowns-predicted{}'.format(series_id), plotid=pid,
                                   series=series)

            # self._add_error_bars(s, p_ues)

    def _plot_references(self, pid, po):
        graph = self.graph
        efit = po.fit
        r_xs = self.rxs
        r_ys = self._get_reference_values(po.name)
        r_es = self._get_reference_errors(po.name)

        reg = None
        kw = dict(add_tools=False, add_inspector=False, color='red',
                  plotid=pid,
                  selection_marker=po.marker,
                  marker=po.marker,
                  marker_size=po.marker_size, )
        if efit in ['preceding', 'bracketing interpolate', 'bracketing average']:
            reg = InterpolationRegressor(xs=r_xs,
                                         ys=r_ys,
                                         yserr=r_es,
                                         kind=efit)
            scatter, _p = graph.new_series(r_xs, r_ys,
                                           yerror=r_es,
                                           type='scatter',
                                           fit=False,
                                           **kw
                                           )
            # self._add_inspector(s, self.sorted_references)
            # self._add_error_bars(s, r_es)
            # series_id = (series_id+1) * 2
        else:

            # series_id = (series_id+1) * 3
            _, scatter, l = graph.new_series(r_xs, r_ys,
                                             # display_index=ArrayDataSource(data=display_xs),
                                             yerror=ArrayDataSource(data=r_es),
                                             fit=po.fit,

                                             **kw)
            # print self.graph, po.fit, args
            # print l
            if hasattr(l, 'regressor'):
                reg = l.regressor

                # l.regression_bounds = regression_bounds

                # self._add_inspector(s, self.sorted_references)
                # self._add_error_bars(s, array(r_es))

        def af(i, x, y, analysis):
            return ('Run Date: {}'.format(analysis.rundate.strftime('%m-%d-%Y %H:%M')),
                    'Rel. Time: {:0.4f}'.format(x))

        self._add_scatter_inspector(scatter,
                                    add_selection=True,
                                    additional_info=af,
                                    items=self.sorted_references)
        plot = self.graph.plots[pid]
        plot.isotope = po.name
        plot.fit = po.fit
        # scatter.index.on_trait_change(self._update_metadata, 'metadata_changed')

        return reg

# ============= EOF =============================================
