#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import List, on_trait_change, Bool, \
    Property, cached_property
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor

#============= standard library imports ========================
from numpy import Inf, asarray, array
from pychron.processing.fits.interpolation_fit_selector import InterpolationFitSelector
from pychron.core.regression.interpolation_regressor import InterpolationRegressor
from chaco.array_data_source import ArrayDataSource
from pychron.core.helpers.datetime_tools import convert_timestamp
#============= local library imports  ==========================


class InterpolationEditor(GraphEditor):
    tool_klass = InterpolationFitSelector
    references = List
    #     _references = List

    auto_find = Bool(True)
    show_current = Bool(True)

    default_reference_analysis_type = 'air'
    sorted_analyses = Property(depends_on='analyses[]')
    sorted_references = Property(depends_on='references[]')

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

    def _update_analyses_hook(self):
        if self.auto_find:
            self._find_references()

    def _find_references(self, progress=None):

        self.debug('find references {}'.format(progress))
        ans = []
        proc = self.processor
        uuids = []
        with proc.db.session_ctx():
            n = len(self.analyses)

            if n > 1:
                if progress is None:
                    progress = proc.open_progress(n)
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

            ans = sorted(list(ans), key=lambda x: x.analysis_timestamp)
            ans = self.processor.make_analyses(ans, progress=progress)
            self.references = ans

            if progress:
                progress.soft_close()
                #self.task.references_pane.items = ans

    def _get_current_values(self, *args, **kw):
        pass

    def _get_reference_values(self, *args, **kw):
        pass

    def _set_interpolated_values(self, iso, reg, c_uxs):
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

        display_xs = asarray(map(convert_timestamp, rxs[:]))

        start, end = self._get_start_end(rxs, uxs)

        c_uxs = self.normalize(uxs, start)
        r_xs = self.normalize(rxs, start)

        '''
            c_... current value
            r... reference value
            p_... predicted value
        '''
        set_x_flag = False
        gen = self._graph_generator()
        for i, fit in enumerate(gen):
            iso = fit.name
            set_x_flag = True
            fit = fit.fit.lower()
            c_uys, c_ues = None, None

            if self.analyses and self.show_current:
                c_uys, c_ues = self._get_current_values(iso)

            r_ys, r_es = None, None
            if self.references:
                r_ys, r_es = self._get_reference_values(iso)

            p = graph.new_plot(
                ytitle=iso,
                xtitle='Time (hrs)',
                padding=[80, 10, 5, 30])
            p.y_axis.title_spacing = 60
            p.value_range.tight_bounds = False

            if c_ues and c_uys:
                # plot unknowns
                s, _p = graph.new_series(c_uxs, c_uys,
                                         yerror=c_ues,
                                         fit=False,
                                         type='scatter',
                                         plotid=i,
                                         marker='square',
                                         marker_size=3,
                                         bind_id=-1,
                                         add_inspector=False)
                self._add_inspector(s, self.sorted_analyses)
                self._add_error_bars(s, c_ues)

                graph.set_series_label('Unknowns-Current', plotid=i)

            if r_ys:
                reg = None
                # plot references

                if fit in ['preceding', 'bracketing interpolate', 'bracketing average']:
                    reg = InterpolationRegressor(xs=r_xs,
                                                 ys=r_ys,
                                                 yserr=r_es,
                                                 kind=fit)
                    s, _p = graph.new_series(r_xs, r_ys,
                                             yerror=r_es,
                                             type='scatter',
                                             plotid=i,
                                             fit=False,
                                             marker_size=3,
                                             add_inspector=False, )
                    self._add_inspector(s, self.sorted_references)
                    self._add_error_bars(s, r_es)

                else:
                    _p, s, l = graph.new_series(r_xs, r_ys,
                                                display_index=ArrayDataSource(data=display_xs),
                                                yerror=ArrayDataSource(data=r_es),
                                                fit=fit,
                                                plotid=i,
                                                marker_size=3,
                                                add_inspector=False)
                    if hasattr(l, 'regressor'):
                        reg = l.regressor

                    self._add_inspector(s, self.sorted_references)
                    self._add_error_bars(s, array(r_es))

                if reg:
                    p_uys, p_ues = self._set_interpolated_values(iso, reg, c_uxs)

                    p_uys=[p if p is not None else 0 for p in p_uys]
                    p_ues=[p if p is not None else 0 for p in p_ues]
                    ids=[ai.record_id for ai in self.sorted_analyses]

                    # display the predicted values
                    s, _p = graph.new_series(c_uxs,
                                             p_uys,
                                             isotope=iso,
                                             yerror=ArrayDataSource(p_ues),
                                             display_index=ArrayDataSource(data=ids),
                                             fit=False,
                                             type='scatter',
                                             marker_size=3,
                                             plotid=i,
                                             bind_id=-1)
                    graph.set_series_label('Unknowns-predicted', plotid=i)
                    self._add_error_bars(s, p_ues)

        if set_x_flag:
            m = abs(end - start) / 3600.
            graph.set_x_limits(0, m, pad='0.1')
            graph.refresh()

    def _add_error_bars(self, scatter, errors,
                        orientation='y', visible=True, nsigma=1):
        from pychron.graph.error_bar_overlay import ErrorBarOverlay

        ebo = ErrorBarOverlay(component=scatter,
                              orientation=orientation,
                              nsigma=nsigma,
                              visible=visible)

        scatter.underlays.append(ebo)
        setattr(scatter, '{}error'.format(orientation), ArrayDataSource(errors))
        return ebo

    def _add_inspector(self, scatter, ans):
        point_inspector = AnalysisPointInspector(scatter,
                                                 analyses=ans,
                                                 convert_index=lambda x: '{:0.3f}'.format(x))

        pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                   tool=point_inspector)

        scatter.overlays.append(pinspector_overlay)
        scatter.tools.append(point_inspector)
        scatter.index.on_trait_change(self._update_metadata(ans), 'metadata_changed')

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
        key='Unknowns-predicted'
        #necessary to handle user excluding points
        gen = self._graph_generator()
        for fit, (plotobj, reg) in zip(gen, new):
            if issubclass(type(reg), BaseRegressor):
                iso = fit.name
                if key in plotobj.plots:
                    scatter = plotobj.plots[key][0]
                    xs = scatter.index.get_data()

                    p_uys, p_ues = self._set_interpolated_values(iso, reg, xs)
                    scatter.value.set_data(p_uys)
                    scatter.yerror.set_data(p_ues)

    def _clean_references(self):
        return [ri for ri in self.references if ri.temp_status == 0]

        #============= EOF =============================================