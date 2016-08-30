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
from numpy import linspace
from traits.api import List, Any, Event, Callable, Dict

from pychron.core.helpers.fits import convert_fit
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.graph.context_menu_mixin import RegressionContextMenuMixin
from pychron.graph.error_envelope_overlay import ErrorEnvelopeOverlay
from pychron.graph.graph import Graph
from pychron.graph.tools.point_inspector import PointInspector, \
    PointInspectorOverlay
from pychron.graph.tools.rect_selection_tool import RectSelectionTool, \
    RectSelectionOverlay
from pychron.graph.tools.regression_inspector import RegressionInspectorTool, \
    RegressionInspectorOverlay


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
    # regressors = List
    regression_results = Event
    suppress_regression = False

    use_data_tool = True
    use_inspector_tool = True
    use_point_inspector = True
    convert_index_func = Callable

    # def __init__(self, *args, **kw):
    #     super(RegressionGraph, self).__init__(*args, **kw)
    #     self._regression_lock = Lock()

    # ===============================================================================
    # context menu handlers
    # ===============================================================================
    def cm_linear(self):
        self.set_fit('linear')
        self._update_graph()

    def cm_parabolic(self):
        self.set_fit('parabolic')
        self._update_graph()

    def cm_cubic(self):
        self.set_fit('cubic')
        self._update_graph()

    def cm_average_std(self):
        self.set_fit('average_std')
        self._update_graph()

    def cm_average_sem(self):
        self.set_fit('average_sem')
        self._update_graph()

    # ===============================================================================
    #
    # ===============================================================================
    def new_series(self, x=None, y=None,
                   ux=None, uy=None, lx=None, ly=None,
                   fx=None, fy=None,
                   fit='linear',
                   filter_outliers_dict=None,
                   use_error_envelope=True,
                   truncate='',
                   marker='circle',
                   marker_size=2,
                   add_tools=True,
                   add_inspector=True,
                   add_point_inspector=True,
                   convert_index=None,
                   plotid=None, *args,
                   **kw):

        kw['marker'] = marker
        kw['marker_size'] = marker_size

        if plotid is None:
            plotid = len(self.plots) - 1

        if not fit:
            s, p = super(RegressionGraph, self).new_series(x, y,
                                                           plotid=plotid,
                                                           *args, **kw)
            if add_tools:
                self.add_tools(p, s, None, convert_index, add_inspector, add_point_inspector)
            return s, p

        scatter, si = self._new_scatter(kw, marker, marker_size,
                                        plotid, x, y, fit,
                                        filter_outliers_dict, truncate)
        lkw = kw.copy()
        lkw['color'] = 'black'
        lkw['type'] = 'line'
        lkw['render_style'] = 'connectedpoints'
        plot, names, rd = self._series_factory(fx, fy, plotid=plotid,
                                               **lkw)
        line = plot.plot(names, add=False, **rd)[0]
        line.index.sort_order = 'ascending'
        self.set_series_label('fit{}'.format(si), plotid=plotid)

        plot.add(line)
        plot.add(scatter)

        if use_error_envelope:
            self._add_error_envelope_overlay(line)

            # # test
            # o = ErrorEnvelopeOverlay(component=line, line_color=(0,1,0))
            # line.underlays.append(o)
            # line.error_envelope2 = o

        # print x, y
        if x is not None and y is not None:
            if not self.suppress_regression:
                self._regress(plot, scatter, line)

        try:
            self._set_bottom_axis(plot, plot, plotid)
        except:
            pass

        # self._bind_index(scatter, **kw)

        if add_tools:
            self.add_tools(plot, scatter, line,
                           convert_index, add_inspector, add_point_inspector)

        return plot, scatter, line

    def add_tools(self, plot, scatter, line=None,
                  convert_index=None, add_inspector=True, add_point_inspector=True):

        if add_inspector:
            # add a regression inspector tool to the line
            if line:
                tool = RegressionInspectorTool(component=line)
                overlay = RegressionInspectorOverlay(component=line,
                                                     tool=tool)
                line.tools.append(tool)
                line.overlays.append(overlay)

        if add_point_inspector:
            point_inspector = PointInspector(scatter,
                                             convert_index=convert_index or self.convert_index_func)
            pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                       tool=point_inspector)

            scatter.overlays.append(pinspector_overlay)
            scatter.tools.append(point_inspector)

        rect_tool = RectSelectionTool(scatter)
        rect_overlay = RectSelectionOverlay(tool=rect_tool)

        scatter.overlays.append(rect_overlay)
        scatter.tools.append(rect_tool)
        # broadcaster.tools.append(rect_tool)

    def set_filter_outliers(self, fi, plotid=0, series=0):
        plot = self.plots[plotid]
        scatter = plot.plots['data{}'.format(series)][0]
        scatter.filter_outliers_dict['filter_outliers'] = fi
        self.redraw()

    def get_filter_outliers(self, fi, plotid=0, series=0):
        plot = self.plots[plotid]
        scatter = plot.plots['data{}'.format(series)][0]
        return scatter.filter_outliers_dict['filter_outliers']

    def set_fit(self, fi, plotid=0, series=0, redraw=True):

        fi = fi.lower()
        plot = self.plots[plotid]
        # for idx in range(series, -1, -1):
        key = 'data{}'.format(series)
        # print 'set fit', fi, plotid, key, plot.plots.keys()
        if key in plot.plots:
            scatter = plot.plots[key][0]
            # print key
            if scatter.fit != fi:
                lkey = 'line{}'.format(series)
                if lkey in plot.plots:
                    line = plot.plots[lkey][0]
                    line.regressor = None

                # print 'fit for {}={}'.format(key, fi)
                scatter.fit = fi
                scatter.index.metadata['selections'] = []
                scatter.index.metadata['filtered'] = None

                if redraw:
                    self.redraw()
                # break

    def get_fit(self, plotid=0, series=0):
        try:
            plot = self.plots[plotid]
            scatter = plot.plots['data{}'.format(series)][0]
            return scatter.fit
        except IndexError:
            pass

    def clear(self):
        # self.regressors = []
        self.selected_component = None

        for p in self.plots:
            for pp in p.plots.values():
                if hasattr(pp, 'error_envelope'):
                    pp.error_envelope.component = None
                    del pp.error_envelope

                if hasattr(pp, 'regressor'):
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
        if hasattr(obj, 'suppress_hover_update'):
            if obj.suppress_hover_update:
                return

        self._update_graph()

    def _update_graph(self, *args, **kw):
        regs = []
        for i, plot in enumerate(self.plots):
            ps = plot.plots
            ks = ps.keys()
            try:
                scatters, idxes = zip(*[(ps[k][0], k[4:]) for k in ks if k.startswith('data')])

                fls = [ps['fit{}'.format(idx)][0] for idx in idxes]
                for si, fl in zip(scatters, fls):
                    if not si.no_regression:
                        r = self._plot_regression(plot, si, fl)
                        regs.append((plot, r))

            except ValueError, e:
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
        if line and hasattr(line, 'regressor'):
            r = line.regressor

        if fit in [1, 2, 3]:
            r = self._poly_regress(scatter, r, fit)

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
                if hasattr(line, 'regression_bounds') and line.regression_bounds:
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
                except BaseException:
                    return

                if hasattr(line, 'error_envelope'):
                    # ly, uy, x = r.calculate_error_envelope2(fx, fy)
                    # print 'fff', ly
                    # print 'x',x
                    # print 'ly',ly
                    # line.error_envelope2.xs = x
                    # line.error_envelope2.lower = ly
                    # line.error_envelope2.upper = uy
                    # line.error_envelope2.invalidate()
                    ci = r.calculate_error_envelope(fx, fy)
                    # ci = r.calculate_ci(fx, fy)
                    #                 print ci
                    if ci is not None:
                        ly, uy = ci
                    else:
                        ly, uy = fy, fy

                    line.error_envelope.lower = ly
                    line.error_envelope.upper = uy
                    line.error_envelope.invalidate()

        return r

    def _set_regressor(self, scatter, r):

        selection = scatter.index.metadata['selections']

        selection = set(selection) ^ set(r.outlier_excluded + r.truncate_excluded)
        x = scatter.index.get_data()
        y = scatter.value.get_data()

        sel = list(selection)
        # print sel
        if hasattr(scatter, 'yerror'):
            yserr = scatter.yerror.get_data()
            r.trait_set(yserr=yserr)

        r.trait_set(xs=x, ys=y,
                    user_excluded=sel,
                    filter_outliers_dict=scatter.filter_outliers_dict)
        r.dirty = True

    def _set_excluded(self, scatter, r):
        scatter.no_regression = True
        d = scatter.index.metadata.copy()
        d['selections'] = x = r.get_excluded()
        scatter.index.trait_setq(metadata=d)
        # scatter.invalidate_and_redraw()
        # scatter.index.metadata['selections'] = r.get_excluded()
        scatter.no_regression = False

    def _poly_regress(self, scatter, r, fit):
        from pychron.core.regression.ols_regressor import PolynomialRegressor
        from pychron.core.regression.wls_regressor import WeightedPolynomialRegressor

        if hasattr(scatter, 'yerror'):
            if r is None or not isinstance(r, WeightedPolynomialRegressor):
                r = WeightedPolynomialRegressor()
        else:
            if r is None or not isinstance(r, PolynomialRegressor):
                r = PolynomialRegressor()

        self._set_regressor(scatter, r)
        r.trait_set(degree=fit)
        r.set_truncate(scatter.truncate)

        if r.ys.shape[0] < fit + 1:
            return

        r.calculate()

        self._set_excluded(scatter, r)
        return r

    def _least_square_regress(self, scatter, r, fit):
        from pychron.core.regression.least_squares_regressor import LeastSquaresRegressor

        func, initial_guess = fit
        if r is None or not isinstance(r, LeastSquaresRegressor):
            r = LeastSquaresRegressor()

        self._set_regressor(scatter, r)
        r.trait_set(fitfunc=func,
                    initial_guess=initial_guess,
                    trait_change_notify=False)
        r.calculate()
        self._set_excluded(scatter, r)
        return r

    def _mean_regress(self, scatter, r, fit):
        from pychron.core.regression.mean_regressor import MeanRegressor, WeightedMeanRegressor

        if hasattr(scatter, 'yerror') and fit == 'weighted mean':
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
        if hasattr(scatter, 'yerror'):
            es = scatter.yerror.get_data()
            kw['yserr'] = es

        if hasattr(scatter, 'xerror'):
            es = scatter.xerror.get_data()
            kw['xserr'] = es

        if r is None or not isinstance(r, fit):
            r = fit()

        self._set_regressor(scatter, r)
        # r.trait_set(trait_change_notify=False,
        #             **kw)
        r.trait_setq(**kw)
        r.calculate()

        self._set_excluded(scatter, r)
        return r

    def _new_scatter(self, kw, marker, marker_size, plotid,
                     x, y, fit, filter_outliers_dict, truncate):
        kw['type'] = 'scatter'
        plot, names, rd = self._series_factory(x, y, plotid=plotid, **kw)

        rd['selection_color'] = 'white'
        rd['selection_outline_color'] = rd['color']
        rd['selection_marker'] = marker
        rd['selection_marker_size'] = marker_size + 1
        scatter = plot.plot(names, add=False, **rd)[0]
        si = len([p for p in plot.plots.keys() if p.startswith('data')])

        self.set_series_label('data{}'.format(si), plotid=plotid)
        if filter_outliers_dict is None:
            filter_outliers_dict = dict(filter_outliers=False)
        else:
            filter_outliers_dict = filter_outliers_dict.copy()

        scatter.fit = fit
        scatter.filter = None
        scatter.filter_outliers_dict = filter_outliers_dict
        scatter.truncate = truncate
        scatter.index.on_trait_change(self.update_metadata, 'metadata_changed')
        scatter.no_regression = False

        return scatter, si

    def _add_error_envelope_overlay(self, line):
        o = ErrorEnvelopeOverlay(component=line)
        line.underlays.append(o)
        line.error_envelope = o



        # def _bind_index(self, *args, **kw):
        #     pass

        # ============= EOF =============================================
        # @classmethod
        #     def _apply_block_filter(cls, xs, ys):
        #         '''
        #             filter data using stats
        #
        #             1. group points into blocks
        #             2. find mean of block
        #             3. find outliers
        #             4. exclude outliers
        #         '''
        #
        #         try:
        #             import numpy as np
        #
        #             sf = StatsFilterParameters()
        #             blocksize = sf.blocksize
        #             tolerance_factor = sf.tolerance_factor
        #
        #             # group into blocks
        #             n = ys.shape[0]
        #             r = n / blocksize
        #             c = blocksize
        #
        #             dev = n - (r * c)
        #             #            remainder_block = None
        #             if dev:
        #                 ys = ys[:-dev]
        #                 #                remainder_block = ys[-dev:]
        #             #            remainder_
        #
        #             blocks = ys.reshape(r, c)
        #
        #             # calculate stats
        #             block_avgs = average(blocks, axis=1)
        #             block_stds = np.std(blocks, axis=1)
        #             devs = (blocks - block_avgs.reshape(r, 1)) ** 2
        #             #        devs = abs(blocks - block_avgs.reshape(r, 1))
        #
        #             # find outliers
        #             tol = block_stds.reshape(r, 1) * tolerance_factor
        #             exc_r, exc_c = np.where(devs > tol)
        #             #            inc_r, inc_c = np.where(devs <= tol)
        #             #            ny = blocks[inc_r, inc_c]
        #             #            nx = xs[inc_c + inc_r * blocksize]
        #             exc_xs = list(exc_c + exc_r * blocksize)
        #
        #             #        if remainder_block:
        #             #        #do filter on remainder block
        #             #            avg = average(remainder_block)
        #             #            stds = np.std(remainder_block)
        #             #            tol = stds * tolerance_factor
        #             #            devs = (remainder_block - avg) ** 2
        #             #            exc_i, _ = np.where(devs > tol)
        #             #            inc_i, _ = np.where(devs < tol)
        #             #            exc_i = exc_i + n - 1
        #             #            nnx = xs[inc_i + n - 1]
        #             #            nny = ys[inc_i + n - 1]
        #             #
        #             #            nx = hstack((nx, nnx))
        #             #            ny = hstack((ny, nny))
        #             #            exc_xs += exc_i
        # #        print 'exception', exc_xs
        #             #        return nx, ny, exc_xs
        #         except:
        #             exc_xs = []
        #
        #         return exc_xs
        # def _apply_outlier_filter(self, reg, ox, oy, index, fod):
        #     try:
        #         if fod['filter_outliers']:
        #         #                 t_fx, t_fy = ox[:], oy[:]
        #             t_fx, t_fy = ox, oy
        #             niterations = fod['filter_outlier_iterations']
        #             n = fod['filter_outlier_std_devs']
        #             for _ in range(niterations):
        #                 excludes = list(reg.calculate_outliers(nsigma=n))
        #                 oxcl = excludes[:]
        #                 sels = index.metadata['selections']
        #
        #                 excludes = sorted(list(set(sels + excludes)))
        #                 index.metadata['filtered'] = oxcl
        #                 index.metadata['selections'] = excludes
        #
        #                 t_fx = delete(t_fx, excludes, 0)
        #                 t_fy = delete(t_fy, excludes, 0)
        #                 reg.trait_set(xs=t_fx, ys=t_fy)
        #
        #     except (KeyError, TypeError), e:
        #         print 'apply outlier filter', e
        #         index.metadata['selections'] = []
        #         index.metadata['filtered'] = None
        #
        #     # return reg
        #
        # def _apply_truncation(self, reg, index, filt):
        #     """
        #        filt: str   x>10 remove all points greater than 10
        #        xs: index array
        #     """
        #     m = re.match(r'[A-Za-z]+', filt)
        #     if m:
        #         k = m.group(0)
        #         xs,ys=reg.xs, reg.ys
        #         exclude=eval(filt, {k:xs})
        #         excludes=list(exclude.nonzero()[0])
        #
        #         sels = index.metadata['selections']
        #         index.metadata['filtered'] = sels
        #         excludes=list(set(excludes+sels))
        #         index.metadata['selections'] = excludes
        #
        #         t_fx = delete(xs, excludes, 0)
        #         t_fy = delete(ys, excludes, 0)
        #         reg.trait_set(xs=t_fx, ys=t_fy)

        # def set_filter(self, fi, plotid=0, series=0):
        #     plot = self.plots[plotid]
        #     scatter = plot.plots['data{}'.format(series)][0]
        #     scatter.filter = fi
        #     self.redraw()
        # def get_filter(self, plotid=0, series=0):
        #     plot = self.plots[plotid]
        #     scatter = plot.plots['data{}'.format(series)][0]
        #     return scatter.filter
