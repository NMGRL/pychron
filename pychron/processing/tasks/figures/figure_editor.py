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
from chaco.base_plot_container import BasePlotContainer
from numpy import isnan
from traits.api import Any, on_trait_change, \
    List, Event, Int
from traitsui.api import View, UItem
from enable.component_editor import ComponentEditor as EnableComponentEditor
#============= standard library imports ========================
from itertools import groupby
import os
#============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.core.csv.csv_parser import CSVParser
from pychron.processing.analyses.analysis_group import InterpretedAge
from pychron.processing.plotters.options.isochron import InverseIsochronOptions
from pychron.processing.plotters.options.spectrum import SpectrumOptions
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
from pychron.processing.tasks.figures.annotation import AnnotationTool, AnnotationOverlay
from pychron.processing.tasks.figures.interpreted_age_factory import InterpretedAgeFactory


class FigureEditor(GraphEditor):
    table_editor = Any
    component = Any
    plotter_options_manager = Any
    associated_editors = List

    tool = Any

    annotation_tool = Any
    figure_model = Any
    figure_container = Any

    tag = Event
    save_db_figure = Event
    invalid = Event

    saved_figure_id = Int
    titles = List

    update_graph_on_set_items = True

    show_caption = False

    def enable_aux_plots(self):
        po = self.plotter_options_manager.plotter_options
        for ap in po.aux_plots:
            ap.enabled = True

    def clear_aux_plot_limits(self):
        po = self.plotter_options_manager.plotter_options
        for ap in po.aux_plots:
            ap.clear_ylimits()
            ap.clear_xlimits()

    def set_items_from_file(self, p):
        if os.path.isfile(p):
            # def construct(d):
            if p.endswith('.xls'):
                self.information_dialog('Plotting Spectra from Excel file not yet implemented')
            else:
                par = CSVParser()
                par.load(p)
                self.analyses = self._get_items_from_file(par)
                self._update_analyses()
                self.dump_tool()

    def _get_items_from_file(self, parser):
        pass

    def save_figure(self, name, project, labnumbers):
        db = self.processor.db
        with db.session_ctx():

            figure = db.add_figure(project=project, name=name)
            for li in labnumbers:
                db.add_figure_labnumber(figure, li)

            for ai in self.analyses:
                dban = db.get_analysis_uuid(ai.uuid)
                aid = ai.record_id
                if dban:
                    db.add_figure_analysis(figure, dban,
                                           status=ai.is_omitted('omit_{}'.format(self.basename)),
                                           graph=ai.graph_id,
                                           group=ai.group_id)
                    self.debug('adding analysis {} to figure'.format(aid))
                else:
                    self.debug('{} not in database'.format(aid))

            po = self.plotter_options_manager.plotter_options
            blob = po.dump_yaml()
            pref = db.add_figure_preference(figure, options=blob, kind=self.basename)
            figure.preference = pref
            return int(figure.id)

    def set_interpreted_age(self):
        ias = self.get_interpreted_ages()

        iaf = InterpretedAgeFactory(groups=ias)
        info = iaf.edit_traits()
        if info.result:
            self.add_interpreted_ages(ias)

    def add_interpreted_ages(self, ias):
        db = self.processor.db
        with db.session_ctx():
            for g in ias:
                if g.use:
                    ln = db.get_labnumber(g.identifier)
                    if not ln:
                        continue

                    self.add_interpreted_age(ln, g)

    def add_interpreted_age(self, ln, ia):
        db = self.processor.db
        with db.session_ctx():
            hist = db.add_interpreted_age_history(ln)

            a = ia.get_ma_scaled_age()

            mswd = ia.preferred_mswd

            if isnan(mswd):
                mswd = 0

            db_ia = db.add_interpreted_age(hist,
                                           age=float(nominal_value(a)),
                                           age_err=float(std_dev(a)),
                                           display_age_units=ia.age_units,
                                           age_kind=ia.preferred_age_kind,
                                           kca_kind=ia.preferred_kca_kind,
                                           kca=float(ia.preferred_kca_value),
                                           kca_err=float(ia.preferred_kca_error),
                                           mswd=float(mswd),

                                           include_j_error_in_mean=ia.include_j_error_in_mean,
                                           include_j_error_in_plateau=ia.include_j_error_in_plateau,
                                           include_j_error_in_individual_analyses=
                                           ia.include_j_error_in_individual_analyses)

            for ai in ia.all_analyses:
                plateau_step = ia.get_is_plateau_step(ai)

                ai = db.get_analysis_uuid(ai.uuid)

                db.add_interpreted_age_set(db_ia, ai,
                                           tag=ai.tag,
                                           plateau_step=plateau_step)

    def save_interpreted_ages(self):
        ias = self.get_interpreted_ages()
        self._set_preferred_age_kind(ias)

        self.add_interpreted_ages(ias)

    def _set_preferred_age_kind(self, ias):
        pass

    def get_interpreted_ages(self):
        key = lambda x: x.group_id
        unks = sorted(self.analyses, key=key)
        ias = []
        ok = 'omit_{}'.format(self.basename)
        po = self.plotter_options_manager.plotter_options
        additional = {}
        if isinstance(po, SpectrumOptions):
            ek = po.plateau_age_error_kind
            pk = 'Plateau'
            additional['include_j_error_in_plateau'] = po.include_j_error_in_plateau
        elif isinstance(po, InverseIsochronOptions):
            pk = 'Isochron'
            ek = po.error_calc_method
            additional['include_j_error_in_mean'] = True

        else:
            ek = po.error_calc_method
            pk = 'Weighted Mean'
            additional['include_j_error_in_individual_analyses'] = po.include_j_error
            additional['include_j_error_in_mean'] = po.include_j_error_in_mean

        for gid, oans in groupby(unks, key=key):
            oans = list(oans)
            ans = filter(lambda x: not x.is_omitted(ok), oans)
            ias.append(InterpretedAge(analyses=ans,
                                      all_analyses=oans,
                                      preferred_age_kind=pk,
                                      preferred_age_error_kind=ek,
                                      use=True,
                                      **additional))

        return ias

    def add_text_box(self):
        if self.annotation_tool is None:
            an = AnnotationOverlay(component=self.component)
            at = AnnotationTool(an, components=[an])
            an.tools.append(at)
            self.annotation_tool = at
            self.component.overlays.append(an)

        elif not self.annotation_tool.active:
            an = AnnotationOverlay(component=self.component)
            self.annotation_tool.components.append(an)
            self.annotation_tool.component = an
            an.tools.append(self.annotation_tool)
            self.component.overlays.append(an)

        else:
            self.annotation_tool = None

    def set_group(self, idxs, gid, **kw):
        self._set_group(idxs, gid, 'group_id', **kw)

    def set_graph_group(self, idxs, gid, **kw):

        self._set_group(idxs, gid, 'graph_id', **kw)

    def _set_group(self, idxs, gid, attr, refresh=True):
        ans = self.analyses
        for i in idxs:
            a = ans[i]
            setattr(a, attr, gid)

            # if refresh:
            #     self.rebuild()

    def rebuild(self):
        # ans = self._gather_unknowns(refresh_data, compress_groups=compress_groups)
        ans = self.analyses
        if ans:
            po = self.plotter_options_manager.plotter_options
            #model, comp = timethis(self.get_component, args=(ans, po),
            #                       msg='get_component {}'.format(self.__class__.__name__))
            model, comp = self.get_component(ans, po)
            if comp:
                comp.invalidate_and_redraw()
                self.figure_model = model
                self.component = comp
                self.component_changed = True

    def get_component(self, ans, po):
        pass

    def _null_component(self):
        self.component = BasePlotContainer()

    @on_trait_change('figure_model:panels:graph:[tag, save_db_figure, invalid]')
    def _handle_graph_event(self, name, new):
        #propograte event to task
        setattr(self, name, new)

    # @on_trait_change('figure_model:panels:graph:save_db')
    # def _handle_save_db(self, new):
    #     #propograte event to task
    #     self.save_db_figure=new

    @on_trait_change('figure_model:panels:figures:refresh_unknowns_table')
    def _handle_refresh(self, obj, name, old, new):
        self.refresh_unknowns_table = True
        #if not obj.suppress_associated:
        #print 'figure editor refresh', id(self)
        for e in self.associated_editors:
            if isinstance(e, FigureEditor):
                #e.rebuild_graph()
                if e.model:
                    for p in e.model.panels:
                        for f in p.figures:
                            f.replot()

    def traits_view(self):
        v = View(UItem('component',
                       style='custom',
                       width=650,
                       editor=EnableComponentEditor()))
        return v

    def _rebuild_graph(self):
        self.rebuild()

    def _update_analyses_hook(self):
        ans = self.analyses
        for e in self.associated_editors:
            e.set_items(ans)
            # if isinstance(e, FigureEditor):
            #     pass
            # e.unknowns = ans
            # else:
            #     e.items = ans

    def update_figure(self):
        sid = self.saved_figure_id

        db = self.processor.db
        with db.session_ctx() as sess:
            fig = db.get_figure(sid, key='id')
            if fig:
                pom = self.plotter_options_manager
                blob = pom.dump_yaml()
                fig.preference.options = blob

                for dbai in fig.analyses:
                    sess.delete(dbai)

                for ai in self.analyses:
                    dbai = db.get_analysis_uuid(ai.uuid)
                    db.add_figure_analysis(fig, dbai,
                                           status=ai.is_omitted('omit_{}'.format(self.basename)),
                                           graph=ai.graph_id,
                                           group=ai.group_id)

#============= EOF =============================================
# dbans = fig.analyses
# uuids = [ai.uuid for ai in self.analyses]

# for dbai in fig.analyses:
#     if not dbai.analysis.uuid in uuids:
#         #remove analysis
#         sess.delete(dbai)
#
# for ai in self.analyses:
#     if not next((dbai for dbai in dbans if dbai.analysis.uuid == ai.uuid), None):
#         #add analysis
#         ai = db.get_analysis_uuid(ai.uuid)
#         db.add_figure_analysis(fig, ai)
#
#     def _gather_unknowns_cached(self):
#         if self._cached_unknowns:
#             # removed items:
# #             if len(self.unknowns) < len(self._cached_unknowns):
#             # added items
# #             else:
#
#             # get analyses not loaded
#             cached_recids = [ui.record_id for ui in self._cached_unknowns]
#             nonloaded = [ui for ui in self.unknowns
#                             if not ui.record_id in cached_recids]
#             if nonloaded:
#                 nonloaded = self.processor.make_analyses(nonloaded)
#                 self.processor.load_analyses(nonloaded)
#                 self._unknowns.extend(nonloaded)
#
#             # remove analyses in _unknowns but not in unknowns
#             recids = [ui.record_id for ui in self.unknowns]
#             ans = [ui for ui in  self._unknowns
#                    if ui.record_id in recids]
# #             for i,ci in enumerate(self._cached_unknowns):
# #                 if ci in self.unknowns:
# #             ans = self._unknowns
# #             ans = [ui for ui, ci in zip(self._unknowns, self._cached_unknowns)
# #                                     if ci in self.unknowns]
#         else:
#             unks = self.unknowns
#             unks = self.processor.make_analyses(unks)
#             self.processor.load_analyses(unks)
#             ans = unks
#
# #         self._cached_unknowns = self.unknowns[:]
#         if ans:
#
#             # compress groups
#             self._compress_unknowns(ans)
#
#             self._unknowns = ans
#             return ans
