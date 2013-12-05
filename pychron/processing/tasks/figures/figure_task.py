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
from traits.api import on_trait_change, Instance
from pyface.tasks.task_layout import TaskLayout, PaneItem, Tabbed, \
    HSplitter
from pyface.tasks.action.schema import SToolBar
#============= standard library imports ========================
from itertools import groupby
import cPickle as pickle
#============= local library imports  ==========================
from pychron.processing.analysis_group import InterpretedAge
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.figures.interpreted_age_factory import InterpretedAgeFactory
from pychron.processing.tasks.figures.panes import PlotterOptionsPane, \
    FigureSelectorPane
from pychron.processing.tasks.figures.actions import SaveFigureAction, \
    OpenFigureAction, NewIdeogramAction, AppendIdeogramAction, NewSpectrumAction, \
    AppendSpectrumAction, AddTextBoxAction

import weakref

from .editors.spectrum_editor import SpectrumEditor
from .editors.isochron_editor import InverseIsochronEditor
from .editors.ideogram_editor import IdeogramEditor
from pychron.processing.tasks.figures.figure_editor import FigureEditor
from pychron.processing.tasks.figures.editors.series_editor import SeriesEditor
from pychron.processing.utils.grouping import group_analyses_by_key

#@todo: add layout editing.
#@todo: add vertical stack. link x-axes


class FigureTask(AnalysisEditTask):
    name = 'Figure'
    id = 'pychron.processing.figures'
    plotter_options_pane = Instance(PlotterOptionsPane)
    tool_bars = [
        SToolBar(
            SaveFigureAction(),
            OpenFigureAction(),
            name='Figure',
            image_size=(16, 16)),
        SToolBar(
            NewIdeogramAction(),
            AppendIdeogramAction(),
            name='Ideogram',
            image_size=(16, 16)),
        SToolBar(
            NewSpectrumAction(),
            AppendSpectrumAction(),
            name='Spectrum',
            image_size=(16, 16)),
        SToolBar(AddTextBoxAction(),
                 image_size=(16, 16)
        )
    ]

    auto_select_analysis = False

    #===============================================================================
    # task protocol
    #===============================================================================
    def prepare_destroy(self):
        for ed in self.editor_area.editors:
            if isinstance(ed, FigureEditor):
                pom = ed.plotter_options_manager
                pom.close()
        super(FigureTask, self).prepare_destroy()

        #def activated(self):
        #    super(FigureTask, self).activated()

        #uk=self.unknowns_pane
        #uk.previous_selection=uk.previous_selections[0]

        #comp=self.active_editor.component
        #print 'comp', comp
        #self.plot_editor_pane.component=comp
        #self.plot_editor_pane._component_changed()

    def create_dock_panes(self):
        panes = super(FigureTask, self).create_dock_panes()
        self.plotter_options_pane = PlotterOptionsPane()
        self.figure_selector_pane = FigureSelectorPane()

        #fs = [fi.name for fi in self.manager.db.get_figures()]
        #if fs:
        #    self.figure_selector_pane.trait_set(figures=fs, figure=fs[0])

        return panes + [self.plotter_options_pane,
                        self.figure_selector_pane,
                        #MultiSelectAnalysisBrowser(model=self)
        ]

    def _create_control_pane(self):
        pass

    #===============================================================================
    # grouping
    #===============================================================================
    def group_by_aliquot(self):
        key = lambda x: x.aliquot
        self._group_by(key)

    def group_by_labnumber(self):
        key = lambda x: x.labnumber

        self._group_by(key)

    def group_selected(self):
        if self.unknowns_pane.selected:
            self.active_editor.set_group(
                self._get_selected_indices(),
                self._get_unique_group_id())

    def clear_grouping(self):
        """
            if selected then set selected group_id to 0
            else set all to 0
        """
        if self.active_editor:
            sel = self.unknowns_pane.selected
            if sel:
                idx = self._get_selected_indices()
            else:
                idx = range(len(self.unknowns_pane.items))

            self.active_editor.set_group(idx, 0)
            #             self.unknowns_pane.update_needed = True
            self.unknowns_pane.refresh_needed = True

    #===============================================================================
    # figures
    #===============================================================================

    def add_text_box(self):
        ac = self.active_editor
        if ac and ac.component and hasattr(ac, 'add_text_box'):

            self.active_editor.add_text_box()

            at = self.active_editor.annotation_tool
            if at:
                at.on_trait_change(self.plot_editor_pane.set_annotation_component,
                                   'component')

                self.plot_editor_pane.set_annotation_tool(at)

    def tb_new_ideogram(self):
        if isinstance(self.active_editor, IdeogramEditor) and \
                not self.unknowns_pane.items:
            self.append_ideogram()
        else:
            self.new_ideogram()

    def tb_new_spectrum(self):
        if isinstance(self.active_editor, SpectrumEditor) and \
                not self.unknowns_pane.items:
            self.append_spectrum()
        else:
            self.new_spectrum()

    def append_spectrum(self):
        self._append_figure(SpectrumEditor)

    def append_ideogram(self):
        self._append_figure(IdeogramEditor)

    def new_ideogram(self, ans=None, klass=None, tklass=None,
                     name='Ideo', set_ans=True,
                     add_table=True, add_iso=True):

        if klass is None:
            klass = IdeogramEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import \
                FusionTableEditor as tklass
#            from pychron.processing.tasks.tables.editors.fusion_table_editor \
#                import FusionTableEditor as tklass
             
        return self._new_figure(ans, name, klass, tklass,
                                set_ans=set_ans,
                                add_iso=add_iso,
                                add_table=add_table)

    def new_spectrum(self, ans=None, klass=None,
                     tklass=None,
                     name='Spec',
                     add_table=True, add_iso=True):
        if klass is None:
            klass = SpectrumEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.step_heat.step_heat_table_editor import \
                StepHeatTableEditor as tklass

        return self._new_figure(ans, name, klass, tklass,
                                add_iso=add_iso,
                                add_table=add_table)

    def new_inverse_isochron(self, ans=None, name='Inv. Iso.',
                             klass=None, tklass=None, plotter_kw=None):
        if klass is None:
            klass = InverseIsochronEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import \
                FusionTableEditor as tklass
                
        feditor = self._new_figure(ans, name, klass, tklass,
                                   add_iso=False)

    def new_series(self, ans=None, name='Series',
                   klass=None, tklass=None,
                   add_iso=False,
                   add_table=True):
        if klass is None:
            klass = SeriesEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import \
                FusionTableEditor as tklass

        return self._new_figure(ans, name, klass, tklass,
                                add_iso=add_iso,
                                add_table=add_table)


    #===============================================================================
    # actions
    #===============================================================================
    def save_figure(self):
        self._save_figure()

    def open_figure(self):
        self._open_figure()

    def set_interpreted_age(self):
        key=lambda x: x.group_id
        unks=sorted(self.active_editor.unknowns, key=key)
        ias=[]
        ok='omit_{}'.format(self.active_editor.basename)
        for gid, ans in groupby(unks, key=key):
            ans=filter(lambda x: not x.is_omitted(ok), ans)
            ias.append(InterpretedAge(analyses=ans, use=True))

        iaf=InterpretedAgeFactory(groups=ias)
        info=iaf.edit_traits()
        if info.result:
            for g in iaf.groups:
                db=self.manager.db
                if g.use:
                    with db.session_ctx():
                        ln=db.get_labnumber(g.identifier)
                        if not ln:
                            continue

                        hist=db.add_interpreted_age_history(ln)
                        ia=db.add_interpreted_age(hist, age=g.preferred_age_value or 0,
                                                  age_err=g.preferred_age_error or 0,
                                                  age_kind=g.preferred_age_kind)
                        for ai in g.analyses:
                            ai=db.get_analysis_uuid(ai.uuid)
                            db.add_interpreted_age_set(ia, ai)


    #===============================================================================
    # db persistence
    #===============================================================================
    def _open_figure(self, name=None):
        if name is None:
            name = self.figure_selector_pane.figure

        if not name:
            return

        db = self.manager.db

        # get the name of the figure for the user
        fig = db.get_figure(name)
        if not fig:
            return
            # load options

        # load analyses
        items = [self._record_view_factory(ai.analysis) for ai in fig.analyses]
        self.unknowns_pane.items = items

    def _save_figure(self):
        db = self.manager.db
        if not isinstance(self.active_editor, FigureEditor):
            return

        with db.session_ctx():
            figure = db.add_figure()

            for ai in self.active_editor.unknowns:
                dban = db.get_analysis_uuid(ai.uuid)
                aid = ai.record_id
                if dban:
                    db.add_figure_analysis(figure, dban,
                                           status=ai.temp_status and ai.status,
                                           graph=ai.graph_id,
                                           group=ai.group_id,
                    )
                    self.debug('adding analysis {} to figure'.format(aid))
                else:
                    self.debug('{} not in database'.format(aid))

            po = self.active_editor.plotter_options_manager.plotter_options

            #             refg = self.active_editor.graphs[0]

            panel = self.active_editor._model.panels[0]
            refg = panel.graph

            r = refg.plots[0].index_mapper.range
            xbounds = '{}, {}'.format(r.low, r.high)
            ys = []
            for pi in refg.plots:
                r = pi.value_mapper.range
                ys.append('{},{}'.format(r.low, r.high))

            ybounds = '|'.join(ys)

            blob = pickle.dumps(po)
            db.add_figure_preference(figure,
                                     xbounds=xbounds,
                                     ybounds=ybounds,
                                     options_pickle=blob)

            #===============================================================================
            #
            #===============================================================================

    def _append_figure(self, klass):
        """
            if selected_samples append all analyses
            else append selected analyses

        """
        return

        if isinstance(self.active_editor, klass):
            sa = self.analysis_table.selected
            if sa:
                ts = self.manager.make_analyses(sa)
            else:
                ts = [ai for si in self.selected_sample
                      for ai in self._get_sample_analyses(si)]

            ans = self.manager.make_analyses(ts)
            if ans:
                pans = self.active_editor.unknowns
                uuids = [p.uuid for p in pans]
                fans = [ai for ai in ans if ai.uuid not in uuids]

                pans.extend(fans)
                self.active_editor.trait_set(unknowns=pans)

            gid = 0
            for _, gans in groupby(self.active_editor.unknowns, key=lambda x: x.sample):
                for ai in gans:
                    ai.group_id = gid
                gid += 1

            self.active_editor.rebuild(compress_groups=False)

    def _new_figure(self, ans, name, klass, tklass=None,
                    add_table=True,
                    add_iso=True,
                    set_ans=True):
        # new figure editor
        editor = klass(
            name=name,
            processor=self.manager,
        )

        if ans is None:
            ans = self.unknowns_pane.items

        if ans:
            editor.unknowns = ans
            if set_ans:
                self.unknowns_pane.items = ans

        self._open_editor(editor)

        if tklass and add_table:
            # open table
            teditor = self._new_table(ans, name, tklass)
            if teditor:
                editor.associated_editors.append(weakref.ref(teditor)())

        if add_iso:
            # open associated isochron
            ieditor = self._new_associated_isochron(ans, name)
            if ieditor:
                editor.associated_editors.append(weakref.ref(ieditor)())
                ieditor.parent_editor = editor

        # activate figure editor
        self.editor_area.activate_editor(editor)
        return editor

    def _new_associated_isochron(self, ans, name):
        name = '{}-isochron'.format(name)
        editor = InverseIsochronEditor(name=name,
                                       processor=self.manager
        )
        return self._add_editor(editor, ans)

    def _new_table(self, ans, name, klass):
        name = '{}-table'.format(name)
        editor = klass(name=name)
        return self._add_editor(editor, ans)

    def _add_editor(self, editor, ans):
        ed = None
        if ans:
            if isinstance(editor, FigureEditor):
                editor.unknowns = ans
            else:
                editor.items = ans

            ed = next((e for e in self.editor_area.editors
                       if e.name == editor.name), None)

        if not ed:
            self.editor_area.add_editor(editor)
        else:
            editor = None

        return editor

    def _get_unique_group_id(self):
        gids = {i.group_id for i in self.unknowns_pane.items}
        return max(gids) + 1

    def _get_selected_indices(self):
        items = self.unknowns_pane.items
        return [items.index(si) for si in self.unknowns_pane.selected]

    def _add_unknowns_hook(self, *args, **kw):
        self.group_by_labnumber()

        if self.active_editor:
            for ai in self.active_editor.associated_editors:
                if isinstance(ai, FigureEditor):
                    ai.rebuild_graph()

    @classmethod
    def group_by(cls, editor, items, key):
        ids = []
        for it in items:
            v = key(it)
            if not v in ids:
                ids.append(v)

        sitems = sorted(items, key=key)
        #for i, (_, analyses) in enumerate(groupby(sitems, key=key)):
        for k, analyses in groupby(sitems, key=key):
            gid = ids.index(k)
            idxs = [items.index(ai) for ai in analyses]
            editor.set_group(idxs, gid, refresh=False)

    def _group_by(self, key):

        editor = self.active_editor
        if editor:
            #items = editor.unknowns
            items = self.unknowns_pane.items
            group_analyses_by_key(editor, items, key)
            self.unknowns_pane.refresh_needed = True
            editor.rebuild(refresh_data=False)

            #===============================================================================
            # handlers
            #===============================================================================
            #     @on_trait_change('plotter_options_pane:pom:plotter_options:aux_plots:x_error')
            #     def _update_x_error(self):


    @on_trait_change('plotter_options_pane:pom:plotter_options:[+, aux_plots:+]')
    def _options_update(self, name, new):
        if name == 'initialized':
            return

        self.active_editor.rebuild(refresh_data=False)

    #         do_later(self.active_editor.rebuild, refresh_data=False)
    #         self.active_editor.rebuild()

    #        self.active_editor.dirty = True

    def _active_editor_changed(self):
        if self.active_editor:
        #             if hasattr(self.active_editor, 'plotter_options_manager'):
            if isinstance(self.active_editor, FigureEditor):
                self.plotter_options_pane.pom = self.active_editor.plotter_options_manager

        super(FigureTask, self)._active_editor_changed()

    @on_trait_change('active_editor:refresh_unknowns_table')
    def _ac_refresh_table(self):
        if self.unknowns_pane:
            self.unknowns_pane.refresh_needed = True

    #===========================================================================
    # browser protocol
    #===========================================================================
    def _dclicked_sample_changed(self, new):
        if self.unknowns_pane.items:

            #editor = IdeogramEditor(processor=self.manager)

            #for sa in self.selected_samples:
            ans = self._get_sample_analyses(self.selected_samples)
            ans = self.manager.make_analyses(ans)
            self.new_ideogram(ans, set_ans=False)

            #self.unknowns_pane.items=ans
            #print sa, ans
        else:
            ans = self._get_sample_analyses(self.selected_samples)
            self.unknowns_pane.items = ans

            #             sam = next((si
            #                         for si in self.active_editor.items
            #                             if si.sample == sa.name), None)
            #             if sam is None:
            #                 man = self.manager
            #                 ans = self._get_sample_analyses(sa)
            #                 ans = man.make_analyses(ans)

            #===============================================================================
            # defaults
            #===============================================================================

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.analysis_edit',
            left=HSplitter(
                PaneItem('pychron.browser'),
                Tabbed(
                    PaneItem('pychron.analysis_edit.unknowns'),
                    PaneItem('pychron.processing.figures.plotter_options'),
                    PaneItem('pychron.plot_editor')
                    #PaneItem('pychron.analysis_edit.controls'),
                ),
            ),
        )

#============= EOF =============================================
