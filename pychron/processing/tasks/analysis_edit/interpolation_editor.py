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

# ============= enthought library imports =======================
from chaco.tools.broadcaster import BroadcasterTool
from traits.api import List, on_trait_change, Bool, \
    Property, cached_property, HasTraits, Tuple

from pychron.core.helpers.formatting import floatfmt
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.graph.tools.rect_selection_tool import RectSelectionTool, RectSelectionOverlay
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor




# ============= standard library imports ========================
from numpy import Inf, asarray, array
from pychron.processing.fits.interpolation_fit_selector import InterpolationFitSelector
from pychron.core.regression.interpolation_regressor import InterpolationRegressor
from chaco.array_data_source import ArrayDataSource
from pychron.core.helpers.datetime_tools import convert_timestamp
# ============= local library imports  ==========================


def bin_analyses(ans):
    ans = iter(sorted(ans, key=lambda x: x.timestamp))

    def _bin():
        ai = ans.next()
        pt = ai.timestamp
        g = [ai]
        tol = 60 * 60
        while 1:
            try:
                ai = ans.next()
                dev = ai.timestamp - pt
                pt = ai.timestamp
                if dev > tol:
                    yield g
                    g = [ai]
                else:
                    g.append(ai)

            except StopIteration:
                break

        yield g

    return _bin()


def get_bounds(groups):
    bs = []
    for i, gi in enumerate(groups):

        try:
            gii = groups[i + 1]
        except IndexError:
            break

        ua = gi[-1].timestamp
        bi = (gii[0].timestamp - ua) / 2.0 + ua
        bs.append(bi)

    return bs


class BinGroup(HasTraits):
    unknowns = List
    references = List
    bounds = Tuple


class InterpolationEditor(GraphEditor):
    tool_klass = InterpolationFitSelector
    references = List

    auto_find = Bool(True)
    show_current = Bool(True)

    default_reference_analysis_type = 'air'
    sorted_analyses = Property(depends_on='analyses[]')
    sorted_references = Property(depends_on='references[]')
    binned_analyses = List
    bounds = List
    calculate_reference_age = Bool(False)

    _normalization_factor = 3600.

    def _get_min_max(self):
        mi = min(self.sorted_references[0].timestamp, self.sorted_analyses[0].timestamp)
        ma = max(self.sorted_references[-1].timestamp, self.sorted_analyses[-1].timestamp)
        return mi, ma

    def bin_analyses(self):
        groups = list(bin_analyses(self.analyses))
        self.binned_analyses = []
        self.bounds = []
        n = len(groups)
        if n > 1:
            mi, ma = self._get_min_max()
            mi -= 1
            ma += 1

            bounds = get_bounds(groups)
            self.bounds = map(lambda x: x - mi, bounds)

            gs = []
            low = None
            for i, gi in enumerate(groups):
                if low is None:
                    low = mi
                try:
                    high = bounds[i]
                except IndexError:
                    high = ma

                refs = filter(lambda x: low < x.timestamp < high, self.sorted_references)
                gs.append(BinGroup(unknowns=gi,
                                   references=refs,
                                   bounds=(
                                       (low - mi) / self._normalization_factor,
                                       (high - mi) / self._normalization_factor,
                                       i == 0, i == n - 1)))
                low = high

            self.binned_analyses = gs
            self.rebuild_graph()

    def rebuild_graph(self):
        super(InterpolationEditor, self).rebuild_graph()
        if self.bounds:
            for bi in self.bounds:
                self.add_group_divider(bi)

    def add_group_divider(self, cen):
        self.graph.add_vertical_rule(cen / self._normalization_factor, line_width=1.5,
                                     color='lightblue', line_style='solid')
        self.graph.redraw()

    def find_references(self, **kw):
        self._find_references(**kw)

    @on_trait_change('references[]')
    def _update_references(self):
        self._update_references_hook()
        self.rebuild_graph()

    def _update_references_hook(self):
        pass

    def _get_start_end(self, rxs, uxs):
        mrxs = min(rxs) if rxs else Inf
        muxs = min(uxs) if uxs else Inf

        marxs = max(rxs) if rxs else -Inf
        mauxs = max(uxs) if uxs else -Inf

        start = min(mrxs, muxs)
        end = max(marxs, mauxs)
        return start, end

    def set_auto_find(self, f):
        self.auto_find = f

    def _update_analyses_hook(self):
        self.debug('update analyses hook auto_find={}'.format(self.auto_find))
        if self.auto_find:
            self._find_references()

    def set_references(self, refs, is_append=False, **kw):
        ans = self.processor.make_analyses(refs,
                                           calculate_age=self.calculate_reference_age,
                                           unpack=self.unpack_peaktime,
                                           **kw)

        if is_append:
            pans = self.references
            pans.extend(ans)
            ans = pans

        self.references = ans

    def _find_references(self, progress=None):

        self.debug('find references {}'.format(progress))
        ans = []
        proc = self.processor
        uuids = []
        with proc.db.session_ctx():
            n = len(self.analyses)

            if n > 1:
                if progress is None:
                    progress = proc.open_progress(n + 1)
                else:
                    progress.increase_max(n)

            for ui in self.analyses:
                if progress:
                    progress.change_message('Finding associated analyses for {}'.format(ui.record_id))

                for ai in proc.find_associated_analyses(ui,
                                                        atype=self.default_reference_analysis_type,
                                                        exclude_uuids=uuids):
                    if not ai.uuid in uuids:
                        uuids.append(ai.uuid)
                        ans.append(ai)

            self.debug('find references pre make')

            ans = self.processor.make_analyses(ans, progress=progress)
            ans = sorted(list(ans), key=lambda x: x.analysis_timestamp)
            self.references = ans

            if progress:
                progress.soft_close()

            self.debug('find references finished')
            #self.task.references_pane.items = ans

    def set_interpolated_values(self, iso, reg, ans):
        mi, ma = self._get_min_max()
        if ans is None:
            ans = self.sorted_analyses

        xs = [(ai.timestamp - mi) / self._normalization_factor for ai in ans]

        p_uys = reg.predict(xs)
        p_ues = reg.predict_error(xs)
        self._set_interpolated_values(iso, ans, p_uys, p_ues)
        return p_uys, p_ues

    def _set_interpolated_values(self, *args, **kw):
        pass

    def _get_current_values(self, *args, **kw):
        pass

    def _get_reference_values(self, *args, **kw):
        pass

    def _get_isotope(self, ui, k, kind=None):
        if k in ui.isotopes:
            v = ui.isotopes[k]
            if kind is not None:
                v = getattr(v, kind)
            v = v.value, v.error
        else:
            v = 0, 0
        return v

    def _rebuild_graph(self):
        graph = self.graph

        uxs = [ui.timestamp for ui in self.analyses]
        rxs = [ui.timestamp for ui in self.references]
        # display_xs = asarray(map(convert_timestamp, rxs[:]))

        start, end = self._get_start_end(rxs, uxs)

        c_uxs = self.normalize(uxs, start)
        r_xs = self.normalize(rxs, start)

        '''
            c_... current value
            r... reference value
            p_... predicted value
        '''
        gen = self._graph_generator()
        for i, fit in enumerate(gen):
            iso = fit.name
            fit = fit.fit_tuple()
            # print i, fit, self.binned_analyses
            if self.binned_analyses:
                self._build_binned(i, iso, fit, start)
            else:
                self._build_non_binned(i, iso, fit, c_uxs, r_xs)

            if i == 0:
                self._add_legend()

        m = abs(end - start) / self._normalization_factor
        graph.set_x_limits(0, m, pad='0.1')
        graph.refresh()

    def _build_binned(self, i, iso, fit, start):
        # graph=self.graph
        # iso = fit.name
        # fit = fit.fit.lower()
        # set_x_flag = True
        graph = self.graph
        p = graph.new_plot(
            ytitle=iso,
            xtitle='Time (hrs)',
            padding=[80, 10, 5, 30])
        p.y_axis.title_spacing = 60
        p.value_range.tight_bounds = False

        for j, gi in enumerate(self.binned_analyses):
            bis = gi.unknowns
            refs = gi.references

            c_xs = self.normalize([bi.timestamp for bi in bis], start)
            rxs = [bi.timestamp for bi in refs]
            r_xs = self.normalize(rxs, start)
            dx = asarray(map(convert_timestamp, rxs))

            c_ys, c_es = None, None
            if self.show_current:
                c_ys, c_es = self._get_current_values(iso, bis)

            r_ys, r_es = None, None
            if refs:
                r_ys, r_es = self._get_reference_values(iso, refs)

            current_args = bis, c_xs, c_ys, c_es
            ref_args = refs, r_xs, r_ys, r_es, dx
            self._build_plot(i, iso, fit, current_args, ref_args,
                             series_id=j,
                             regression_bounds=gi.bounds)

    def _build_non_binned(self, i, iso, fit, c_xs, r_xs):

        c_ys, c_es = None, None
        if self.analyses and self.show_current:
            c_ys, c_es = self._get_current_values(iso)

        r_ys, r_es, dx = None, None, None
        if self.references:
            r_ys, r_es = self._get_reference_values(iso)
            dx = asarray(map(convert_timestamp, [ui.timestamp for ui in self.references]))

        current_args = self.sorted_analyses, c_xs, c_ys, c_es
        ref_args = self.sorted_references, r_xs, r_ys, r_es, dx

        graph = self.graph
        p = graph.new_plot(
            ytitle=iso,
            xtitle='Time (hrs)',
            # padding=[80, 10, 5, 30]
            padding=[80, 80, 80, 80])
        p.y_axis.title_spacing = 60
        p.value_range.tight_bounds = False

        self._build_plot(i, iso, fit, current_args, ref_args)

    def _plot_unknowns_current(self, ans, c_es, c_xs, c_ys, i):
        graph = self.graph
        if c_es and c_ys:
            # plot unknowns
            s, _p = graph.new_series(c_xs, c_ys,
                                     yerror=c_es,
                                     fit=False,
                                     type='scatter',
                                     plotid=i,
                                     marker='square',
                                     marker_size=3,
                                     bind_id=-1,
                                     color='black',
                                     add_inspector=False)
            self._add_inspector(s, ans)
            self._add_error_bars(s, c_es)

            graph.set_series_label('Unknowns-Current', plotid=i)

    def _plot_interpolated(self, ans, c_xs, i, iso, reg, series_id):
        p_uys, p_ues = self.set_interpolated_values(iso, reg, ans)
        if len(p_uys):
            graph = self.graph
            # display the predicted values
            s, p = graph.new_series(c_xs,
                                    p_uys,
                                    isotope=iso,
                                    yerror=ArrayDataSource(p_ues),
                                    fit=False,
                                    add_tools=False,
                                    add_inspector=False,
                                    type='scatter',
                                    marker_size=3,
                                    color='blue',
                                    plotid=i,
                                    bind_id=-1)
            series = len(p.plots) - 1
            graph.set_series_label('Unknowns-predicted{}'.format(series_id), plotid=i,
                                   series=series)

            self._add_error_bars(s, p_ues)

    def _plot_references(self, ref_args, fit, i, regression_bounds, series_id):
        refs, r_xs, r_ys, r_es, display_xs = ref_args
        graph = self.graph
        if not r_ys:
            return

        # plot references
        efit = fit[0]
        if efit in ['preceding', 'bracketing interpolate', 'bracketing average']:
            reg = InterpolationRegressor(xs=r_xs,
                                         ys=r_ys,
                                         yserr=r_es,
                                         kind=efit)
            s, _p = graph.new_series(r_xs, r_ys,
                                     yerror=r_es,
                                     type='scatter',
                                     plotid=i,
                                     fit=False,
                                     marker_size=3,
                                     color='red',
                                     add_inspector=False)
            self._add_inspector(s, refs)
            self._add_error_bars(s, r_es)
            # series_id = (series_id+1) * 2
        else:

            # series_id = (series_id+1) * 3
            _p, s, l = graph.new_series(r_xs, r_ys,
                                        display_index=ArrayDataSource(data=display_xs),
                                        yerror=ArrayDataSource(data=r_es),
                                        fit=fit,
                                        color='red',
                                        plotid=i,
                                        marker_size=3,
                                        add_inspector=False)
            if hasattr(l, 'regressor'):
                reg = l.regressor

            l.regression_bounds = regression_bounds

            self._add_inspector(s, refs)
            self._add_error_bars(s, array(r_es))

        return reg

    def _build_plot(self, i, iso, fit, current_args, ref_args,
                    series_id=0,
                    regression_bounds=None):
        ans, c_xs, c_ys, c_es = current_args

        self._plot_unknowns_current(ans, c_es, c_xs, c_ys, i)
        reg = self._plot_references(ref_args, fit, i, regression_bounds, series_id)
        if reg:
            self._plot_interpolated(ans, c_xs, i, iso, reg, series_id)

            # self._plot_unknowns_current(ans, c_es, c_xs, c_ys, i)

    def _add_legend(self):
        pass

    def _add_error_bars(self, scatter, errors,
                        orientation='y', visible=True, nsigma=1, line_width=1):
        from pychron.graph.error_bar_overlay import ErrorBarOverlay

        ebo = ErrorBarOverlay(component=scatter,
                              orientation=orientation,
                              nsigma=nsigma,
                              line_width=line_width,
                              visible=visible)

        scatter.underlays.append(ebo)
        # print len(errors),scatter.index.get_size()
        setattr(scatter, '{}error'.format(orientation), ArrayDataSource(errors))
        return ebo

    def _add_inspector(self, scatter, ans):
        broadcaster = BroadcasterTool()
        scatter.tools.append(broadcaster)

        rect_tool = RectSelectionTool(scatter)
        rect_overlay = RectSelectionOverlay(component=scatter,
                                            tool=rect_tool)

        scatter.overlays.append(rect_overlay)
        broadcaster.tools.append(rect_tool)

        point_inspector = AnalysisPointInspector(scatter,
                                                 value_format=floatfmt,
                                                 analyses=ans,
                                                 convert_index=lambda x: '{:0.3f}'.format(x))

        pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                   tool=point_inspector)

        scatter.overlays.append(pinspector_overlay)
        scatter.tools.append(point_inspector)
        broadcaster.tools.append(point_inspector)

        scatter.index.on_trait_change(self._update_metadata(ans), 'metadata_changed')
        # scatter.index.on_trait_change(self._test, 'metadata_changed')

    # def _test(self, obj, name, old, new):
    #     import inspect
    #     stack = inspect.stack()
    #     print stack
    #     print '{} called by {}'.format('test', stack[1][3])
    #     meta = obj.metadata
    #     print meta

    def _update_metadata(self, ans):
        def _handler(obj, name, old, new):
            meta = obj.metadata
            selections = meta['selections']
            for i, ai in enumerate(ans):
                ai.temp_status = i in selections

        return _handler

    @cached_property
    def _get_sorted_analyses(self):
        return sorted(self.analyses, key=lambda x: x.timestamp)

    @cached_property
    def _get_sorted_references(self):
        return sorted(self.references, key=lambda x: x.timestamp)

    @on_trait_change('graph:regression_results')
    def _update_regression(self, new):
        # return

        key = 'Unknowns-predicted{}'
        #necessary to handle user excluding points
        if self.binned_analyses:
            gen = self._graph_generator()

            c = 0
            for j, fit in enumerate(gen):
                for i, g in enumerate(self.binned_analyses):
                    try:
                        plotobj, reg = new[c]
                    except IndexError:
                        break

                    if issubclass(type(reg), BaseRegressor):
                        k = key.format(i)
                        self._set_values(fit, plotobj, reg, k, g.unknowns)
                    c += 1
        else:
            key = key.format(0)
            gen = self._graph_generator()
            for fit, (plotobj, reg) in zip(gen, new):
                if issubclass(type(reg), BaseRegressor):
                    self._set_values(fit, plotobj, reg, key)

    def _set_values(self, fit, plotobj, reg, key, ans=None):

        iso = fit.name
        if key in plotobj.plots:
            scatter = plotobj.plots[key][0]
            p_uys, p_ues = self.set_interpolated_values(iso, reg, ans)
            scatter.value.set_data(p_uys)
            scatter.yerror.set_data(p_ues)

    def _clean_references(self):
        return [ri for ri in self.references if ri.temp_status == 0]

# ============= EOF =============================================


