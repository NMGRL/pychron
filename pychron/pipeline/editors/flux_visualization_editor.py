# ===============================================================================
# Copyright 2018 ross
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
from operator import itemgetter

from numpy import linspace, meshgrid, arctan2, sin, cos, vstack, array, zeros, diff, argwhere
from traits.api import Instance, Int, Str, Float, Property, List, on_trait_change
from traitsui.api import View, UItem, VGroup, HGroup, TableEditor, Tabbed
from traitsui.table_column import ObjectColumn
from uncertainties import nominal_value, std_dev

from pychron.core.fits.fit_selector import CheckboxColumn
from pychron.core.geometry.affine import AffineTransform
from pychron.core.helpers.formatting import floatfmt
from pychron.core.regression.flux_regressor import BowlFluxRegressor, PlaneFluxRegressor, MatchingFluxRegressor, \
    BracketingFluxRegressor
from pychron.core.regression.mean_regressor import WeightedMeanRegressor
from pychron.core.regression.ols_regressor import OLSRegressor
from pychron.core.stats.monte_carlo import FluxEstimator
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.contour_graph import FluxVisualizationGraph
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.error_envelope_overlay import ErrorEnvelopeOverlay
from pychron.graph.explicit_legend import ExplicitLegend
from pychron.graph.graph import container_factory, Graph
from pychron.graph.regression_graph import RegressionGraph
from pychron.graph.stacked_graph import StackedGraph
from pychron.graph.tools.data_tool import DataTool, DataToolOverlay
from pychron.options.layout import FigureLayout
from pychron.pipeline.editors.irradiation_tray_overlay import IrradiationTrayOverlay
from pychron.pychron_constants import LEAST_SQUARES_1D, MATCHING, BRACKETING, WEIGHTED_MEAN, BOWL, PLANE, \
    WEIGHTED_MEAN_1D, MSEM


def make_grid(r, n):
    xi = linspace(-r, r, n)
    yi = linspace(-r, r, n)
    return meshgrid(xi, yi)


def add_inspector(scatter, func, **kw):
    from pychron.graph.tools.point_inspector import PointInspector
    from pychron.graph.tools.point_inspector import PointInspectorOverlay

    point_inspector = PointInspector(scatter, additional_info=func, **kw)
    pinspector_overlay = PointInspectorOverlay(component=scatter,
                                               tool=point_inspector)

    scatter.overlays.append(pinspector_overlay)
    scatter.tools.append(point_inspector)


def add_analysis_inspector(scatter, items, add_selection=True, value_format=None, convert_index=None):
    from chaco.tools.broadcaster import BroadcasterTool
    from pychron.graph.tools.rect_selection_tool import RectSelectionTool
    from pychron.graph.tools.rect_selection_tool import RectSelectionOverlay
    from pychron.graph.tools.point_inspector import PointInspectorOverlay
    from pychron.graph.tools.analysis_inspector import AnalysisPointInspector

    broadcaster = BroadcasterTool()
    scatter.tools.append(broadcaster)
    if add_selection:
        rect_tool = RectSelectionTool(scatter)
        rect_overlay = RectSelectionOverlay(component=scatter,
                                            tool=rect_tool)

        scatter.overlays.append(rect_overlay)
        broadcaster.tools.append(rect_tool)

    if value_format is None:
        value_format = lambda x: '{:0.5f}'.format(x)

    if convert_index is None:
        convert_index = lambda x: '{:0.3f}'.format(x)

    point_inspector = AnalysisPointInspector(scatter,
                                             analyses=items,
                                             convert_index=convert_index,
                                             value_format=value_format)

    pinspector_overlay = PointInspectorOverlay(component=scatter,
                                               tool=point_inspector)

    scatter.overlays.append(pinspector_overlay)
    broadcaster.tools.append(point_inspector)


def add_axes_tools(g, p):
    g.add_limit_tool(p, 'x')
    g.add_limit_tool(p, 'y')
    g.add_axis_tool(p, p.x_axis)
    g.add_axis_tool(p, p.y_axis)


class BaseFluxVisualizationEditor(BaseTraitsEditor):
    graph = Instance('pychron.graph.graph.Graph')
    levels = 10
    show_labels = False

    color_map_name = 'jet'
    marker_size = Int(5)
    plotter_options = None
    irradiation = Str
    level = Str
    holder = Str

    max_j = Float
    min_j = Float
    percent_j_change = Property

    geometry = List
    monitor_positions = List
    unknown_positions = List
    rotation = Float(auto_set=False, enter_set=True)

    _regressor = None
    _analyses = List
    _individual_analyses_enabled = True

    @on_trait_change('monitor_positions:use')
    def handle_use(self):
        self.predict_values()

    def _rotation_changed(self):
        self.predict_values()

    def predict_values(self, refresh=False):
        self.debug('predict values {}'.format(refresh))
        try:
            x, y, z, ze, j, je, sj, sje = self._extract_position_arrays()
            t = AffineTransform()
            t.rotate(self.rotation)

            x, y = t.transforms(x, y)
            # print(x)
        except ValueError as e:
            self.debug('no monitor positions to fit, {}'.format(e))
            return

        # print(x)
        # print(y)
        # print(z)
        # print(ze)
        n = x.shape[0]
        if n >= 3 or self.plotter_options.model_kind in (WEIGHTED_MEAN, MATCHING, BRACKETING):
            # n = z.shape[0] * 10
            r = max((max(abs(x)), max(abs(y))))
            # r *= 1.25
            reg = self._regressor_factory(x, y, z, ze)
            self._regressor = reg
        else:
            msg = 'Not enough monitor positions. At least 3 required. Currently only {} active'.format(n)
            self.debug(msg)
            self.information_dialog(msg)
            return

        options = self.plotter_options
        ipositions = self.unknown_positions + self.monitor_positions

        if options.model_kind == LEAST_SQUARES_1D:
            k = options.one_d_axis.lower()
            pts = array([getattr(p, k) for p in ipositions])
        else:
            pts = array([[p.x, p.y] for p in ipositions])

        if options.use_monte_carlo and options.model_kind not in (MATCHING, BRACKETING):
            fe = FluxEstimator(options.monte_carlo_ntrials, reg)

            split = len(self.unknown_positions)
            nominals, errors = fe.estimate(pts)
            if options.position_error:
                _, pos_errors = fe.estimate_position_err(pts, options.position_error)
            else:
                pos_errors = zeros(pts.shape[0])

            for positions, s, e in ((self.unknown_positions, 0, split),
                                    (self.monitor_positions, split, None)):
                noms, es, ps = nominals[s:e], errors[s:e], pos_errors[s:e]
                for p, j, je, pe in zip(positions, noms, es, ps):
                    oj = p.saved_j
                    p.j = j
                    p.jerr = je
                    p.position_jerr = pe
                    p.dev = (oj - j) / j * 100
        else:
            js = reg.predict(pts)
            jes = reg.predict_error(pts)

            for j, je, p in zip(js, jes, ipositions):
                p.j = float(j)
                p.jerr = float(je)

                p.dev = (p.saved_j - j) / j * 100
                p.mean_dev = (p.mean_j - j) / j * 100

        if options.plot_kind == '2D':
            self._graph_contour(x, y, z, r, reg, refresh)
        elif options.plot_kind == 'Grid':
            self._graph_grid(x, y, z, ze, r, reg, refresh)
        else:
            if options.model_kind in (LEAST_SQUARES_1D, WEIGHTED_MEAN_1D):
                self._graph_linear_j(x, y, r, reg, refresh)
            else:
                self._graph_hole_vs_j(x, y, r, reg, refresh)

    def _get_percent_j_change(self):
        maj, mij = self.max_j, self.min_j
        try:
            return (maj - mij) / maj * 100
        except ZeroDivisionError:
            return 0

    def _regressor_factory(self, x, y, z, ze, model_kind=None):
        po = self.plotter_options
        if model_kind is None:
            model_kind = po.model_kind

        x = array(x)
        y = array(y)
        kw = {}
        if model_kind == LEAST_SQUARES_1D:
            klass = OLSRegressor
            xs = x if po.one_d_axis == 'X' else y
            kw['fit'] = po.least_squares_fit
        elif model_kind in (WEIGHTED_MEAN, WEIGHTED_MEAN_1D):
            xs = x if po.one_d_axis == 'X' else y
            klass = WeightedMeanRegressor
        else:
            if model_kind == BOWL:
                klass = BowlFluxRegressor
            elif model_kind == PLANE:
                klass = PlaneFluxRegressor
            elif model_kind == MATCHING:
                klass = MatchingFluxRegressor
            elif model_kind == BRACKETING:
                klass = BracketingFluxRegressor

            xs = vstack((x, y)).T

        wf = po.use_weighted_fit
        ec = po.predicted_j_error_type

        reg = klass(xs=xs, ys=z, yserr=ze,
                    error_calc_type=ec,
                    use_weighted_fit=wf,
                    **kw)
        reg.calculate()
        return reg

    def _model_flux(self, reg, r):

        n = reg.n * 10
        gx, gy = make_grid(r, n)

        nz = zeros((n, n))
        ne = zeros((n, n))
        for i in range(n):
            pts = vstack((gx[i], gy[i])).T

            nominals = reg.predict(pts)
            nz[i] = nominals

        self.max_j = nz.max()
        self.min_j = nz.min()

        return gx, gy, nz, ne

    # graphing
    def _graph_contour(self, x, y, z, r, reg, refresh):
        cg = self.graph
        if not isinstance(cg, FluxVisualizationGraph):
            cg = FluxVisualizationGraph(container_dict={'kind': 'h',
                                                        'bgcolor': self.plotter_options.bgcolor})
            self.graph = cg
        else:
            cg.clear()

        center_plot = cg.new_plot(xtitle='X', ytitle='Y', add=False,
                                  padding=0,
                                  width=550,
                                  height=550,
                                  resizable='',
                                  aspect_ratio=1)

        ito = IrradiationTrayOverlay(component=center_plot,
                                     geometry=self.geometry,
                                     show_labels=self.show_labels)
        self.irradiation_tray_overlay = ito
        center_plot.overlays.append(ito)

        gx, gy, m, me = self._model_flux(reg, r)
        # self._visualization_update(gx, gy, m, me, reg.xs, reg.ys)

        r = r * 1.1
        s, p = cg.new_series(z=m,
                             xbounds=(-r, r),
                             ybounds=(-r, r),
                             levels=self.levels,
                             cmap=self.color_map_name,
                             colorbar=True,
                             style='contour')

        # add data tool
        def predict_func(ptx, pty):
            return floatfmt(reg.predict([(ptx, pty)])[0], n=2, use_scientific=True, s=6)

        dt = DataTool(plot=s,
                      filter_components=False,
                      predict_value_func=predict_func,
                      use_date_str=False, component=p)
        dto = DataToolOverlay(component=p, tool=dt)
        p.tools.append(dt)
        p.overlays.append(dto)

        # add slice inspectors
        cg.add_inspectors(s)

        # add 1D slices
        bottom_plot = cg.new_plot(add=False,
                                  height=175,
                                  resizable='h',
                                  padding=0,
                                  xtitle='mm',
                                  ytitle='J')

        right_plot = cg.new_plot(add=False,
                                 width=175,
                                 resizable='v',
                                 padding=0,
                                 # xtitle='J',
                                 ytitle='mm')

        center = center_plot.plots['plot0'][0]
        options = dict(style='cmap_scatter',
                       type='cmap_scatter',
                       marker='circle',
                       color_mapper=center.color_mapper)

        cg.new_series(plotid=1, render_style='connectedpoints')
        cg.new_series(plotid=1, **options)
        s = cg.new_series(plotid=1, type='scatter',
                          marker_size=2,
                          color='red', style='xy', marker='circle')[0]
        ebo = ErrorBarOverlay(component=s, orientation='y', use_component=False)
        s.underlays.append(ebo)
        x, y = reg.xs.T
        ebo.index, ebo.value, ebo.error = x, reg.ys, reg.yserr
        cg.bottom_error_bars = ebo

        center_plot.x_axis.orientation = 'top'

        right_plot.orientation = 'v'
        right_plot.x_axis.orientation = 'top'
        right_plot.x_axis.tick_label_rotate_angle = 45
        right_plot.y_axis.orientation = 'right'
        right_plot.x_axis.axis_line_visible = False
        right_plot.y_axis.axis_line_visible = False

        s = cg.new_series(plotid=2, render_style='connectedpoints')[0]
        s.orientation = 'v'
        s = cg.new_series(plotid=2, **options)[0]
        s.orientation = 'v'
        ss = cg.new_series(plotid=2, type='scatter',
                           marker_size=2,
                           color='red', style='xy', marker='circle')[0]
        ss.orientation = 'v'

        ebo = ErrorBarOverlay(component=ss, orientation='x', use_component=False)
        ss.underlays.append(ebo)
        x, y = reg.xs.T
        ebo.index, ebo.value, ebo.error = y, reg.ys, reg.yserr
        cg.right_error_bars = ebo

        center.index.on_trait_change(cg.metadata_changed, 'metadata_changed')

        gridcontainer = container_factory(kind='g',
                                          # fill_padding=True,
                                          # bgcolor='red',
                                          padding_left=100,
                                          padding_right=20,
                                          padding_top=100,
                                          padding_bottom=40,
                                          shape=(2, 2),
                                          spacing=(5, 5))

        gridcontainer.add(center_plot)
        gridcontainer.add(right_plot)
        gridcontainer.add(bottom_plot)

        # cb = cg.make_colorbar(center)
        # cb.width = 50
        # cb.padding_left = 50
        # cg.plotcontainer.add(cb)

        # plot means
        s = cg.new_series(x, y,
                          z=z,
                          style='cmap_scatter',
                          color_mapper=s.color_mapper,
                          marker='circle',
                          marker_size=self.marker_size)

        cg.errors = reg.yserr
        cg.x = reg.xs
        cg.y = reg.ys

        cg.plotcontainer.add(gridcontainer)

    def _graph_linear_j(self, x, y, r, reg, refresh):

        g = self.graph
        if not isinstance(g, RegressionGraph):
            g = RegressionGraph(container_dict={'bgcolor': self.plotter_options.bgcolor})
            self.graph = g

        po = self.plotter_options
        g.clear()

        plot = g.new_plot(padding=po.get_paddings())
        if po.model_kind == WEIGHTED_MEAN_1D:
            fit = 'weighted mean'
        else:
            fit = po.least_squares_fit

        _, scatter, line = g.new_series(x=reg.xs, y=reg.ys,
                                        yerror=reg.yserr,
                                        fit=fit)
        ebo = ErrorBarOverlay(component=scatter,
                              orientation='y')
        scatter.underlays.append(ebo)
        scatter.error_bars = ebo

        add_inspector(scatter, self._additional_info)

        add_axes_tools(g, plot)

        g.set_x_title(po.one_d_axis)
        g.set_y_title('J')

        g.add_statistics()

        miy = 100
        may = -1

        if self._individual_analyses_enabled:
            sel = [i for i, (a, x, y, e) in enumerate(zip(*self._analyses)) if a.is_omitted()]

            # plot the individual analyses
            iscatter, iys = self._graph_individual_analyses(fit=None, add_tools=False)
            miy = min(iys)
            may = max(iys)

            # set metadata last because it will trigger a refresh
            self.suppress_metadata_change = True
            iscatter.index.metadata['selections'] = sel
            self.suppress_metadata_change = False

        g.set_y_limits(min_=miy, max_=may, pad='0.1')
        g.set_x_limits(pad='0.1')

        g.refresh()

        fys = line.value.get_data()
        self.max_j = fys.max()
        self.min_j = fys.min()

    def _graph_hole_vs_j(self, x, y, r, reg, refresh):

        if self._individual_analyses_enabled:
            sel = [i for i, (a, x, y, e) in enumerate(zip(*self._analyses)) if a.is_omitted()]

        g = self.graph
        if not isinstance(g, Graph):
            g = Graph(container_dict={'bgcolor': self.plotter_options.bgcolor})
            self.graph = g

        po = self.plotter_options
        is_matching = po.model_kind == MATCHING

        ys = reg.ys
        xs = arctan2(x, y)

        yserr = reg.yserr
        lyy = ys - yserr
        uyy = ys + yserr
        a = max((abs(min(xs)), abs(max(xs))))
        fxs = linspace(-a, a)

        a = r * sin(fxs)
        b = r * cos(fxs)
        pts = vstack((a, b)).T
        fys = reg.predict(pts)

        if not is_matching:
            try:
                l, u = reg.calculate_error_envelope(fxs, rmodel=fys)
            except BaseException:
                l, u = reg.calculate_error_envelope(pts, rmodel=fys)

        if not refresh:
            g.clear()
            p = g.new_plot(xtitle='Hole (Theta)',
                           ytitle='J',
                           # padding=[90, 5, 5, 40],
                           padding=po.get_paddings())
            p.bgcolor = po.plot_bgcolor

            add_axes_tools(g, p)

            def label_fmt(xx):
                return floatfmt(xx, n=2, s=4, use_scientific=True)

            p.y_axis.tick_label_formatter = label_fmt

            # plot fit line
            # plot0 == line
            if not is_matching:
                line, _p = g.new_series(fxs, fys)

                ee = ErrorEnvelopeOverlay(component=line,
                                          xs=fxs, lower=l, upper=u)
                line.error_envelope = ee
                line.underlays.append(ee)

            miy = 100
            may = -1

            if self._individual_analyses_enabled:
                # plot the individual analyses
                # plot1 == scatter
                iscatter, iys = self._graph_individual_analyses()
                miy = min(iys)
                may = max(iys)

            # plot means
            # plot2 == scatter
            scatter, _ = g.new_series(xs, ys,
                                      yerror=yserr,
                                      type='scatter',
                                      marker_size=4, marker='diamond')

            ebo = ErrorBarOverlay(component=scatter,
                                  orientation='y')
            scatter.underlays.append(ebo)
            scatter.error_bars = ebo

            add_inspector(scatter, self._additional_info)

            ymi = min(lyy.min(), miy)
            yma = max(uyy.max(), may)
            g.set_x_limits(-3.5, 3.5)
            g.set_y_limits(ymi, yma, pad='0.1')

            if self._individual_analyses_enabled:
                # set metadata last because it will trigger a refresh
                self.suppress_metadata_change = True
                iscatter.index.metadata['selections'] = sel
                self.suppress_metadata_change = False

            if self._individual_analyses_enabled:
                # add a legend
                if not is_matching:
                    labels = [('plot1', 'Individual'),
                              ('plot2', 'Mean'),
                              ('plot0', 'Fit'),
                              ]
                else:
                    labels = [('plot0', 'Individual'),
                              ('plot1', 'Mean')]
            else:
                labels = [('plot0', 'Mean')]

            legend = ExplicitLegend(plots=self.graph.plots[0].plots,
                                    labels=labels)
            p.overlays.append(legend)

        else:
            plot = g.plots[0]

            s1 = plot.plots['plot1' if is_matching else 'plot2'][0]
            s1.yerror.set_data(yserr)
            s1.error_bars.invalidate()

            g.set_data(ys, plotid=0, series=1 if is_matching else 2, axis=1)

            if not is_matching:
                l1 = plot.plots['plot0'][0]
                l1.error_envelope.trait_set(xs=fxs, lower=l, upper=u)
                l1.error_envelope.invalidate()
                g.set_data(fys, plotid=0, series=0, axis=1)

            s2 = plot.plots['plot1' if is_matching else 'plot0'][0]
            s2.index.metadata['selections'] = sel

        self.max_j = fys.max()
        self.min_j = fys.min()

    def _additional_info(self, ind):
        fm = self.monitor_positions[ind]
        return ['Pos: {}'.format(fm.hole_id),
                'Identifier: {}'.format(fm.identifier)]

    def _grid_additional_info(self, ind, y):
        ps = [p for p in self.monitor_positions if p.y == y]
        fm = ps[ind]
        return ['Pos: {}'.format(fm.hole_id),
                'Identifier: {}'.format(fm.identifier)]

    def _grid_update_graph_metadata(self, ans):
        if not self.suppress_metadata_change:
            def wrapper(obj, name, old, new):
                def mwrapper(sel):
                    self._recalculate_means(sel, ans)

                self._filter_metadata_changes(obj, ans, mwrapper)
        return wrapper

    def _graph_grid(self, x, y, z, ze, r, reg, refresh):
        self.min_j = min(z)
        self.max_j = max(z)

        g = self.graph
        layout = FigureLayout(fixed='filled_grid')
        nrows, ncols = layout.calculate(len(x))

        if not isinstance(g, Graph):
            g = RegressionGraph(container_dict={'bgcolor': 'gray',
                                                'kind': 'g',
                                                'shape': (nrows, ncols)})
            self.graph = g

        def get_ip(xi, yi):
            return next(
                (ip for ip in self.monitor_positions if ((ip.x - xi) ** 2 + (ip.y - yi) ** 2) ** 0.5 < 0.01), None)

        opt = self.plotter_options
        monage = opt.monitor_age * 1e6
        lk = opt.lambda_k
        ans = self._analyses[0]
        scale = opt.flux_scalar
        for r in range(nrows):
            for c in range(ncols):
                idx = c + ncols * r

                if refresh:
                    try:
                        yy = z[idx] * scale
                        ye = ze[idx] * scale
                    except IndexError:
                        continue
                    # if hasattr(g, 'rules'):
                    #     if idx in g.rules:
                    #         l1, l2, l3 = g.rules[idx]
                    #         l1.value = yy
                    #         l2.value = yy + ye
                    #         l3.value = yy - ye


                else:
                    plot = g.new_plot(padding_left=65, padding_right=5, padding_top=30, padding_bottom=5)
                    try:
                        ip = get_ip(x[idx], y[idx])
                    except IndexError:
                        continue

                    add_axes_tools(g, plot)
                    yy = z[idx] * scale
                    ye = ze[idx] * scale
                    plot.title = 'Identifier={} Position={}'.format(ip.identifier, ip.hole_id)

                    plot.x_axis.visible = False
                    if c == 0 and r == nrows // 2:
                        plot.y_axis.title = 'J x{}'.format(scale)

                    if not ip.use:
                        continue

                    # get ip via x,y
                    ais = [a for a in ans if a.irradiation_position == ip.hole_id]
                    n = len(ais)

                    # plot mean value
                    # l1 = g.add_horizontal_rule(yy, color='black', line_style='solid', plotid=idx)
                    # l2 = g.add_horizontal_rule(yy + ye, plotid=idx)
                    # l3 = g.add_horizontal_rule(yy - ye, plotid=idx)
                    # rs = (l1, l2, l3)
                    # d = {idx: rs}
                    # if hasattr(g, 'rules'):
                    #     g.rules.update(d)
                    # else:
                    #     g.rules = d

                    # plot individual analyses
                    fs = [a.model_j(monage, lk) * scale for a in ais]
                    fs = sorted(fs)
                    iys = array([nominal_value(fi) for fi in fs])
                    ies = array([std_dev(fi) for fi in fs])

                    if self.plotter_options.use_weighted_fit:
                        fit = 'weighted mean'
                    else:
                        fit = 'average'

                    ek = self.plotter_options.error_kind
                    if ek == MSEM:
                        ek = 'msem'

                    fit = '{}_{}'.format(fit, ek)

                    p_, s, l_ = g.new_series(linspace(0, n - 1, n), iys, yerror=ies, type='scatter',
                                             fit=fit,
                                             add_point_inspector=False,
                                             add_inspector=False,
                                             marker='circle', marker_size=3)
                    g.set_x_limits(0, n - 1, pad='0.1', plotid=idx)
                    g.set_y_limits(min(iys - ies), max(iys + ies), pad='0.1', plotid=idx)
                    g.add_statistics(plotid=idx)

                    ebo = ErrorBarOverlay(component=s, orientation='y')
                    s.underlays.append(ebo)
                    s.error_bars = ebo

                    add_analysis_inspector(s, ais)
                    s.index.on_trait_change(self._grid_update_graph_metadata(ais), 'metadata_changed')
                    self.suppress_metadata_change = True
                    sel = [i for i, a in enumerate(ais) if a.is_omitted()]
                    s.index.metadata['selections'] = sel
                    self.suppress_metadata_change = False
        g.refresh()

    def _graph_individual_analyses(self, *args, **kw):
        g = self.graph

        ans, ixs, iys, ies = self._analyses

        s, _p = g.new_series(ixs, iys, yerror=ies, type='scatter', marker='circle', marker_size=1.5, **kw)

        ebo = ErrorBarOverlay(component=s,
                              orientation='y')
        s.underlays.append(ebo)
        s.error_bars = ebo

        add_analysis_inspector(s, ans)

        s.index.on_trait_change(self._update_graph_metadata, 'metadata_changed')
        return s, iys

    def _sort_individuals(self, p, m, k, slope, padding):
        if self.plotter_options.model_kind in (LEAST_SQUARES_1D, WEIGHTED_MEAN_1D):
            pp = p.x if self.plotter_options.one_d_axis == 'X' else p.y
        else:
            pp = arctan2(p.x, p.y)

        xx = linspace(pp - padding, pp + padding, len(p.analyses))
        ys = [a.model_j(m, k) for a in p.analyses]
        yy = [nominal_value(a) for a in ys]
        es = [std_dev(a) for a in ys]

        data = zip(p.analyses, xx, yy, es)
        data = sorted(data, key=itemgetter(2), reverse=not slope)
        return list(zip(*data))

    def _extract_position_arrays(self, poss=None):
        if poss is None:
            poss = self.monitor_positions

        data = array([(pos.x, pos.y, pos.mean_j, pos.mean_jerr, pos.j, pos.jerr, pos.saved_j, pos.saved_jerr)
                      for pos in poss
                      if pos.use]).T
        return data


class FluxVisualizationEditor(BaseFluxVisualizationEditor):
    ring_graph = Instance(StackedGraph)
    deviation_graph = Instance(StackedGraph)
    spoke_graph = Instance(StackedGraph)

    _individual_analyses_enabled = False

    def model_plane(self, x, y, z, ze, model_points=None):
        r = max((max(abs(x)), max(abs(y))))
        reg = self._regressor_factory(x, y, z, ze, model_kind='Plane')
        ys = reg.ys
        xs = arctan2(x, y)

        yserr = reg.yserr
        lyy = ys - yserr
        uyy = ys + yserr
        a = max((abs(min(xs)), abs(max(xs))))
        fxs = linspace(-a, a)

        a = r * sin(fxs)
        b = r * cos(fxs)
        pts = vstack((a, b)).T
        fys = reg.predict(pts)

        if model_points is None:
            model_points = vstack((x, y)).T

        my = reg.predict(model_points)
        return fxs, fys, xs, my

    def _update_half_ring_graph(self):
        self.ring_graph = g = StackedGraph()
        g.plotcontainer.spacing = 10
        g.plotcontainer.stack_order = 'top_to_bottom'
        poss = list(self._group_rings())[0]
        g.new_plot()
        for m in (2, 3, 5, 10):
            monitors, unknowns = [], []
            for i, p in enumerate(poss):
                if not i % m:
                    monitors.append(p)
                else:
                    unknowns.append(p)

            # monitors = poss[::5]
            # unknowns = poss[1::2]

            x, y, z, ze, j, je, sj, sje = self._extract_position_arrays(monitors)

            unkpts = [(p.x, p.y) for p in unknowns]
            unkj = [p.mean_j for p in unknowns]
            fx, fy, mx, my = self.model_plane(x, y, z, ze, model_points=unkpts)

            x, y = zip(*unkpts)
            mx = arctan2(x, y)
            ys = (unkj - my) / unkj * 100
            s = g.new_series(mx, ys)[0]

    def _update_ring_graph(self):
        self.ring_graph = g = StackedGraph()
        g.plotcontainer.spacing = 10
        g.plotcontainer.stack_order = 'top_to_bottom'

        self.deviation_graph = dg = StackedGraph()
        dg.plotcontainer.spacing = 10
        dg.plotcontainer.stack_order = 'top_to_bottom'

        self.spoke_graph = sg = StackedGraph()
        sg.plotcontainer.spacing = 10
        sg.plotcontainer.stack_order = 'top_to_bottom'

        l, h = 0, 0
        dl, dh = 0, 0
        for poss in self._group_rings():
            poss = list(poss)

            x, y, z, ze, j, je, sj, sje = self._extract_position_arrays(poss)

            fx, fy, mx, my = self.model_plane(x, y, z, ze)

            x = arctan2(x, y)
            plot = g.new_plot(padding_left=100, padding_top=20, padding_right=10,
                              padding_bottom=30)

            s = g.new_series(x, z, yerror=ze, type='scatter')[0]
            ebo = ErrorBarOverlay(component=s,
                                  orientation='y')

            s.underlays.append(ebo)

            g.new_series(x, j, color='green')
            # g.new_series(x, sj)
            g.new_series(fx, fy, color='blue')

            l = min(min(x), l)
            h = max(max(x), h)

            plot = dg.new_plot(padding_left=100, padding_top=20, padding_right=10,
                               padding_bottom=30)

            ds = (j - z) / z * 100
            ds2 = (my - z) / z * 100

            # dg.new_series(x, (my-j)/j*100)
            dg.new_series(x, ds, color='green')
            dg.new_series(mx, ds2, color='blue')

            dl = min(min(ds), dl)
            dh = max(max(ds), dh)

        for i, p in enumerate(g.plots):
            g.set_x_limits(l, h, plotid=i, pad='0.05')

            dg.set_x_limits(l, h, plotid=i, pad='0.05')
            dg.set_y_limits(dl, dh, plotid=i, pad='0.05')

        for spoke, poss in self._group_spokes():
            print(spoke)
            x, y, z, ze, j, je, sj, sje = self._extract_position_arrays(poss)
            x = (x ** 2 + y ** 2) ** 0.5
            plot = sg.new_plot(padding_left=100, padding_top=20, padding_right=10,
                               padding_bottom=30)

            s = sg.new_series(x, z, yerror=ze, type='scatter')[0]
            ebo = ErrorBarOverlay(component=s,
                                  orientation='y')

            s.underlays.append(ebo)
            sg.new_series(x, j, color='green')

    def _group_spokes(self):
        """

        groups = [(angle, []),]

        :return:
        """
        tol = 1e-2

        def ingroups(ang, gg):
            return next((g[1] for g in gg if abs(g[0] - ang) < tol), None)

        spokes = []
        for p in self.monitor_positions:
            a = arctan2(p.x, p.y)
            gs = ingroups(a, spokes)
            if gs is not None:
                gs.append(p)
            else:
                spokes.append((a, [p]))
        return [s for s in spokes if len(s[1]) > 1]

    def _group_rings(self):
        rs = array([p.x ** 2 + p.y ** 2 for p in self.monitor_positions])

        split_idx = abs(diff(rs)) > 1e-3

        pidx = 0
        for idx in argwhere(split_idx):
            idx = idx[0]

            yield sorted(self.monitor_positions[pidx:idx + 1], key=lambda p: arctan2(p.x, p.y))
            pidx = idx + 1

        yield sorted(self.monitor_positions[pidx:], key=lambda p: arctan2(p.x, p.y))

    def predict_values(self, refresh=False):
        super(FluxVisualizationEditor, self).predict_values()
        self._update_ring_graph()
        # self._update_half_ring_graph()

    def set_positions(self, pos):
        self.monitor_positions = pos
        self.predict_values()

    def traits_view(self):
        cols = [CheckboxColumn(name='use'),
                ObjectColumn(name='hole_id'),
                ObjectColumn(name='identifier'),
                ObjectColumn(name='mean_j', format='%0.5e'),
                ObjectColumn(name='mean_jerr', format='%0.5e'),
                ObjectColumn(name='j', label='Pred. J', format='%0.5e'),
                ObjectColumn(name='mean_dev', label='Mean Dev.', format='%0.2f')
                ]
        g3d = VGroup(UItem('rotation'),
                     HGroup(UItem('graph', style='custom'),
                            UItem('monitor_positions',
                                  width=-400,
                                  editor=TableEditor(columns=cols, sortable=False))))

        rings = VGroup(HGroup(UItem('ring_graph', style='custom'),
                              UItem('deviation_graph', style='custom'),
                              UItem('spoke_graph', style='custom')))
        return View(Tabbed(rings, g3d))
# ============= EOF =============================================
