# ===============================================================================
# Copyright 2013 Jake Ross
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

from traits.api import on_trait_change, Instance, List, Event, Any, Enum, Button
from pyface.tasks.task_layout import TaskLayout, PaneItem, Tabbed, \
    HSplitter, VSplitter
from pyface.tasks.action.schema import SToolBar
# ============= standard library imports ========================
from itertools import groupby
import os
import weakref
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.envisage.tasks.actions import ToggleFullWindowAction
from pychron.file_defaults import IDEOGRAM_DEFAULTS, SPECTRUM_DEFAULTS, INVERSE_ISOCHRON_DEFAULTS, COMPOSITE_DEFAULTS, \
    SCREEN_FORMATTING_DEFAULTS, PRESENTATION_FORMATTING_DEFAULTS
from pychron.paths import paths
from pychron.processing.plotters.xy.xy_scatter import XYScatterEditor
from pychron.processing.tasks.actions.edit_actions import TagAction
from pychron.processing.tasks.actions.processing_actions import SetInterpretedAgeTBAction, BrowseInterpretedAgeTBAction
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tagging.analysis_tags import Tag
from pychron.processing.tasks.browser.util import browser_pane_item
from pychron.processing.tasks.figures.db_figure import DBFigure
from pychron.processing.tasks.figures.editors.composite_editor import CompositeEditor
from pychron.processing.tasks.figures.panes import PlotterOptionsPane, \
    FigureSelectorPane
from pychron.processing.tasks.figures.actions import SaveFigureAction, \
    NewIdeogramAction, NewSpectrumAction, \
    SavePDFFigureAction, SaveAsFigureAction, RefreshActiveEditorAction, NewIsochronAction, NewTableAction
from pychron.processing.tasks.figures.figure_editor import FigureEditor
from pychron.processing.tasks.figures.save_figure_dialog import SaveFigureDialog
from pychron.processing.tasks.recall.actions import AddIsoEvoAction
from pychron.processing.tasks.recall.recall_editor import RecallEditor

from .editors.spectrum_editor import SpectrumEditor
from .editors.isochron_editor import InverseIsochronEditor
from .editors.ideogram_editor import IdeogramEditor

# @todo: add layout editing.
# @todo: add vertical stack. link x-axes


class FigureTask(AnalysisEditTask):
    name = 'Figure'
    default_task_name = 'Ideogram'
    id = 'pychron.processing.figures'
    plotter_options_pane = Instance(PlotterOptionsPane)
    figure_selector_pane = Instance(FigureSelectorPane)

    tool_bars = [
        SToolBar(ToggleFullWindowAction()),
        SToolBar(RefreshActiveEditorAction(),
                 # AddIsoEvoAction(),
                 # TagAction()
                ),
        SToolBar(
            SavePDFFigureAction(),
            # SaveFigureAction(),
            # SaveAsFigureAction(),
            name='Figure'),
        # SToolBar(NewIdeogramAction(),
        #          NewSpectrumAction(),
        #          NewIsochronAction(),
        #          NewTableAction()),
        # SToolBar(SetInterpretedAgeTBAction(),
        #          BrowseInterpretedAgeTBAction()),
        # SToolBar(GroupSelectedAction(name='Selected'),
        # GroupbyAliquotAction(name='by Aliquot'),
        # GroupbyLabnumberAction(name='by Labnumber'),
        # GroupbySampleAction(name='by Sample'),
        # ClearGroupAction(name='Clear'))
    ]

    # auto_select_analysis = False

    figures_help = 'Double-click to open'
    figure_kind = Enum('All', 'Ideogram', 'Spectrum', 'Inv Iso')
    delete_figure_button = Button

    figures = List
    ofigures = List

    selected_figures = Any
    dclicked_figure = Event

    def activate_spectrum_editor(self):
        self._activate_editor('spectrum')

    def activate_ideogram_editor(self):
        self._activate_editor('ideogram')

    def _activate_editor(self, kind):
        func = getattr(self, 'new_{}'.format(kind))
        klass = globals()['{}Editor'.format(kind.capitalize())]
        if self.active_editor is None:
            print 'new editor'
            func()
        else:
            for editor in self.editor_area.editors:
                if isinstance(editor, klass):
                    self.activate_editor(editor)
                    break
            else:
                print 'new editor'
                func()

    # ===============================================================================
    # task protocol
    # ===============================================================================

    def prepare_destroy(self):
        for ed in self.editor_area.editors:
            if isinstance(ed, FigureEditor):
                pom = ed.plotter_options_manager
                pom.close()
        super(FigureTask, self).prepare_destroy()

    def create_dock_panes(self):
        panes = super(FigureTask, self).create_dock_panes()
        self.plotter_options_pane = PlotterOptionsPane()
        self.figure_selector_pane = FigureSelectorPane(model=self)

        return panes + [self.plotter_options_pane,
                        self.figure_selector_pane]

    # ===============================================================================
    # context menu handler
    # ===============================================================================
    def _clear_group(self):
        for i in self.unknowns_pane.items:
            i.group_id = 0
            i.graph_id = 0

        self.unknowns_pane.refresh_needed = True

    @on_trait_change('browser_model:plot_selected')
    def _handle_plot_selected(self, new):
        if new:
            self.plot_selected_grouped()
        else:
            self.plot_selected()

    def plot_selected_grouped(self):
        self.debug('plot selected grouped')
        if self.has_active_editor():
            self._clear_group()
            self._append_replace_unknowns(False, self.browser_model.analysis_table.analyses)

    def plot_selected(self):
        self.debug('plot selected')
        ac = self.has_active_editor()
        if ac:
            pane = self.unknowns_pane

            # remember original setting
            oauto_group1 = ac.auto_group
            oauto_group2 = pane.auto_group

            # turn off auto grouping
            ac.auto_group = False
            pane.auto_group = False

            self._clear_group()
            self._append_replace_unknowns(False, self.browser_model.analysis_table.analyses)

            # return to original settings
            ac.auto_group = oauto_group1
            pane.auto_group = oauto_group2

    # ===============================================================================
    # graph grouping
    # ===============================================================================
    def graph_group_selected(self):
        if self.unknowns_pane.selected:
            idxs = self._get_selected_indices()
            # all_idxs = range(len(self.unknowns_pane.items))
            # selection = list(set(all_idxs) - set(idxs))

            self.clear_grouping(refresh=False, selection_idxs=idxs)
            self.active_editor.set_graph_group(
                idxs,
                self._get_unique_graph_id())

            self.active_editor.compress_analyses()
            self.active_editor.rebuild()

    def graph_group_by_sample(self):

        ans = self.active_editor.analyses
        for i, (si, gi) in enumerate(groupby(ans, key=lambda x: x.sample)):
            idxs = [ans.index(ai) for ai in gi]
            self.active_editor.set_graph_group(idxs, i)
        # self._get_unique_graph_id()
        # self.active_editor.compress_analyses()
        self.active_editor.rebuild()

    # ===============================================================================
    # grouping
    # ===============================================================================
    def group_by_aliquot(self):
        if self.unknowns_pane and self.unknowns_pane.items:
            self.unknowns_pane.group_by_aliquot()

    def group_by_labnumber(self):
        if self.unknowns_pane and self.unknowns_pane.items:
            self.debug('group by labnumber')
            self.unknowns_pane.group_by_labnumber()

    def group_selected(self):
        if self.unknowns_pane and self.unknowns_pane.items:
            self.unknowns_pane.group_by_selected()

    def clear_grouping(self, refresh=True, selection_idxs=None):
        """
            if selected then set selected group_id to 0
            else set all to 0
        """

        if self.unknowns_pane and self.unknowns_pane.items:
            self.unknowns_pane.clear_grouping(refresh_plot=refresh,
                                              idxs=selection_idxs)

    # ===============================================================================
    # figures
    # ===============================================================================
    def _debug_add(self):
        from pychron.globals import globalv

        self.debug('debug add figure_debug: {}'.format(globalv.figure_debug))
        if globalv.figure_debug:
            if self.browser_model:
                ans = self.browser_model.analysis_table.analyses
                if ans:
                    self.unknowns_pane.items = ans

    def new_table(self, ans=None):
        if self.has_active_editor():
            if isinstance(self.active_editor, IdeogramEditor):
                from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import FusionTableEditor

                klass = FusionTableEditor
            elif isinstance(self.active_editor, SpectrumEditor):
                from pychron.processing.tasks.tables.editors.step_heat.step_heat_table_editor import StepHeatTableEditor

                klass = StepHeatTableEditor
            else:
                return

            name = self.active_editor.name.replace(self.active_editor.basename, '')
            return self._new_table(ans, name, klass)
            # # new figure editor
            # editor = klass(
            # name=name,
            # processor=self.manager)
            #
            # if ans is None:
            #         ans = self.unknowns_pane.items
            #
            #     if ans:
            #         editor.analyses = ans
            #         editor.set_name()
            #         editor.rebuild()
            #         # if set_ans:
            #         #     self.unknowns_pane.items = ans
            #
            #     self._open_editor(editor)
            #
            #     # add_associated = False
            #     # if not add_associated:
            #     #     self.debug('Not adding associated editors')
            #     # else:
            #     #     if tklass and add_table:
            #     #         # open table
            #     #         teditor = self._new_table(ans, name, tklass)
            #     #         if teditor:
            #     #             editor.associated_editors.append(weakref.ref(teditor)())
            #     #
            #     #     if add_iso:
            #     #         # open associated isochron
            #     #         ieditor = self._new_associated_isochron(ans, name)
            #     #         if ieditor:
            #     #             editor.associated_editors.append(weakref.ref(ieditor)())
            #     #             ieditor.parent_editor = editor
            #
            #     # activate figure editor
            #     # self.editor_area.activate_editor(editor)
            #     return editor

    def new_ideogram(self, ans=None, klass=None, tklass=None,
                     name='Ideo', set_ans=True,
                     add_table=True, add_iso=True):

        if klass is None:
            klass = IdeogramEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import \
                FusionTableEditor as tklass
            # from pychron.processing.tasks.tables.editors.fusion_table_editor \
        # import FusionTableEditor as tklass

        editor = self._new_figure(ans, name, klass, tklass,
                                  set_ans=set_ans,
                                  add_iso=add_iso,
                                  add_table=add_table)

        self._debug_add()
        return editor

    def new_composite(self, ans=None, klass=None,
                      tklass=None,
                      name='Comp',
                      add_table=True, add_iso=True):
        if klass is None:
            klass = CompositeEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.step_heat.step_heat_table_editor import \
                StepHeatTableEditor as tklass

        return self._new_figure(ans, name, klass, tklass,
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

        editor = self._new_figure(ans, name, klass, tklass,
                                  add_iso=add_iso,
                                  add_table=add_table)
        self._debug_add()
        return editor

    def new_inverse_isochron(self, ans=None, name='Inv. Iso.',
                             klass=None, tklass=None, plotter_kw=None):
        if klass is None:
            klass = InverseIsochronEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import \
                FusionTableEditor as tklass

        feditor = self._new_figure(ans, name, klass, tklass,
                                   add_iso=False)

        ans = self.browser_model.analysis_table.analyses
        if ans:
            self.unknowns_pane.items = ans

    def new_series(self, ans=None, name='Series',
                   klass=None, tklass=None,
                   add_iso=False,
                   add_table=False):
        if klass is None:
            from pychron.processing.tasks.figures.editors.series_editor import SeriesEditor

            klass = SeriesEditor

        if tklass is None:
            from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import \
                FusionTableEditor as tklass

        return self._new_figure(ans, name, klass, tklass,
                                add_iso=add_iso,
                                add_table=add_table)

    def new_xy_scatter(self, ans=None, name='XYScatter',
                       klass=None, tklass=None,
                       add_iso=False,
                       add_table=False):
        if klass is None:
            klass = XYScatterEditor
        return self._new_figure(ans, name, klass, tklass,
                                add_iso=add_iso,
                                add_table=add_table)

    def new_ideogram_from_file(self):
        p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/gee_sample_ages7.txt'
        p = '/Users/ross/Programming/git/dissertation/data/minnabluff/dryvalleys_comp.txt'
        p = '/Users/ross/Programming/git/dissertation/data/minnabluff/dryvalleys_comp2.txt'
        if not os.path.isfile(p):
            self.open_file_dialog(default_directory=paths.data_dir)

        self.new_ideogram(add_iso=False, add_table=False)
        self.active_editor.set_items_from_file(p)
        self.active_editor.rebuild()

    def new_spectrum_from_file(self):
        p = '/Users/ross/Sandbox/spectrum_file.txt'
        if not os.path.isfile(p):
            self.open_file_dialog(default_directory=paths.data_dir)

        self.new_spectrum(add_iso=False, add_table=False)
        self.active_editor.set_items_from_file(p)
        self.active_editor.rebuild()

    # ===============================================================================
    # actions
    # ===============================================================================
    def refresh_active_editor(self):
        if self.has_active_editor():
            self.active_editor.rebuild()

    def save_figure(self):
        if not self.has_active_editor():
            return

        if self.active_editor:
            if not isinstance(self.active_editor, RecallEditor):
                sid = self.active_editor.saved_figure_id
                if sid >= 0:
                    self._save_figure()
                else:
                    self._save_as_figure()
            else:
                self.warning_dialog('You are trying to save a figure from a Recall Editor. '
                                    'Select a Figure Editor instead.')

    def save_as_figure(self):
        self._save_as_figure()

    def set_interpreted_age(self):
        if self.active_editor:
            if not isinstance(self.active_editor, RecallEditor):
                self.active_editor.set_interpreted_age()
            else:
                self.warning_dialog('You are trying to set an interpreted age from Recall Editor. '
                                    'Select a Figure Editor instead')

    def browse_interpreted_age(self):
        app = self.application
        app.open_task('pychron.processing.interpreted_age')

    def add_text_box(self):
        ac = self.active_editor
        if ac and ac.component and hasattr(ac, 'add_text_box'):

            self.active_editor.add_text_box()

            at = self.active_editor.annotation_tool
            if at:
                at.on_trait_change(self.plot_editor_pane.set_annotation_component,
                                   'component')

                self.plot_editor_pane.set_annotation_tool(at)

    # def tb_new_ideogram(self):
    # self.new_ideogram()
    #
    # # if isinstance(self.active_editor, IdeogramEditor) and \
    # #         not self.unknowns_pane.items:
    # #     self.append_ideogram()
    #     # else:
    #     #     self.new_ideogram()
    #
    # def tb_new_spectrum(self):
    #     self.new_spectrum()
    #     # if isinstance(self.active_editor, SpectrumEditor) and \
    #     #         not self.unknowns_pane.items:
    #     #     self.append_spectrum()
    #     # else:
    #     #     self.new_spectrum()
    #
    # def tb_new_xy_scatter(self):
    #     self.new_xy_scatter()
    #
    # def tb_new_isochron(self):
    #     self.new_inverse_isochron()
    #
    # ===============================================================================
    #
    # ===============================================================================
    # ===============================================================================
    # private
    # ===============================================================================
    def _new_figure(self, ans, name, klass, tklass=None,
                    add_table=True,
                    add_iso=True,
                    set_ans=True):

        # with no_update(self):
        #     if klass == IdeogramEditor:
        #         self.browser_model.current_task_name = 'Ideogram'
        #     else:
        #         self.browser_model.current_task_name = 'Spectrum'

        # new figure editor
        editor = klass(
            name=name,
            processor=self.manager)

        if ans is None:
            ans = self.unknowns_pane.items

        if ans:
            editor.analyses = ans
            editor.set_name()
            editor.rebuild()
            # if set_ans:
            #     self.unknowns_pane.items = ans

        self._open_editor(editor)

        # add_associated = False
        # if not add_associated:
        #     self.debug('Not adding associated editors')
        # else:
        #     if tklass and add_table:
        #         # open table
        #         teditor = self._new_table(ans, name, tklass)
        #         if teditor:
        #             editor.associated_editors.append(weakref.ref(teditor)())
        #
        #     if add_iso:
        #         # open associated isochron
        #         ieditor = self._new_associated_isochron(ans, name)
        #         if ieditor:
        #             editor.associated_editors.append(weakref.ref(ieditor)())
        #             ieditor.parent_editor = editor

        # activate figure editor
        # self.editor_area.activate_editor(editor)
        return editor

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

    def _add_unknowns_hook(self, *args, **kw):
        if self.active_editor:
            # if hasattr(self.active_editor, 'auto_group'):
            # if self.active_editor.auto_group:

            if self.unknowns_pane.auto_group and self.active_editor.auto_group:
                self.group_by_labnumber()
                # for ai in self.active_editor.associated_editors:
                # if isinstance(ai, FigureEditor):
                #         ai.rebuild_graph()

    # def _get_unique_group_id(self):
    # gids = {i.group_id for i in self.unknowns_pane.items}
    #     return max(gids) + 1

    def _get_unique_graph_id(self):
        gids = {i.graph_id for i in self.unknowns_pane.items}
        return max(gids) + 1

    def _get_selected_indices(self):
        items = self.unknowns_pane.items
        return [items.index(si) for si in self.unknowns_pane.selected]

    def _new_associated_isochron(self, ans, name):
        name = '{}-isochron'.format(name)
        editor = InverseIsochronEditor(name=name,
                                       processor=self.manager)
        return self._add_editor(editor, ans)

    def _new_table(self, ans, name, klass):
        if ans is None:
            ans = self.unknowns_pane.items

        name = '{}-table'.format(name)
        editor = klass(name=name)
        return self._add_editor(editor, ans)

    def _load_project_figures(self, new):
        if new:
            db = self.manager.db
            with db.session_ctx():
                proj = [p.name for p in new]
                figs = db.get_project_figures(proj)
                self.ofigures = [self._dbfigure_factory(f) for f in figs]
                self.figures = self.ofigures
                self._figure_kind_changed()

    def _load_sample_figures(self, new):
        if new:
            lns = [p.labnumber for p in new]
            self.debug('loading sample figures for {}'.format(','.join(lns)))
            db = self.manager.db
            with db.session_ctx():

                figs = db.get_labnumber_figures(lns)

                # figs = [self._dbfigure_factory(f) for f in figs]

                def gen():
                    for f in figs:
                        fig = self._dbfigure_factory(f)
                        if fig:
                            yield fig

                figs = list(gen())

                self.ofigures = figs[:]
                self.figures = figs
                self._figure_kind_changed()

    def _dbfigure_factory(self, f):
        if f.preference:
            try:
                dbf = DBFigure(name=f.name or '',
                               project=f.project.name if f.project else '',
                               identifiers=[s.labnumber.identifier for s in f.labnumbers],
                               samples=list(set([s.labnumber.sample.name for s in f.labnumbers])),
                               kind=f.preference.kind,
                               id=f.id)
                return dbf
            except AttributeError:
                self.debug_exception()
                self.debug('failed making dbfigure {}'.format(f.name))

    def _get_sample_obj(self, s):
        return next((sr for sr in self.samples if sr.labnumber == s), None)

    def _get_project_obj(self, p):
        return next((sr for sr in self.projects if sr.name == p), None)

    def _save_figure(self):
        """

            update preferences
            update analyses
        """
        if self.active_editor:
            self.active_editor.update_figure()
            self.db_save_info()

            # db=self.manager.db
            # with db.session_ctx() as sess:
            #     fig=db.get_figure(sid, key='id')
            #     print sid, fig
            #
            #     pom=self.active_editor.plotter_options_manager
            #     blob = pom.dump_yaml()
            #     fig.preference.options=blob
            #
            #     dbans=fig.analyses
            #     uuids=[ai.uuid for ai in self.active_editor.analyses]
            #
            #     for dbai in fig.analyses:
            #         if not dbai.analysis.uuid in uuids:
            #             #remove analysis
            #             sess.delete(dbai)
            #
            #     for ai in self.active_editor.analyses:
            #         if not next((dbai for dbai in dbans if dbai.analysis.uuid==ai.uuid), None):
            #             #add analysis
            #             ai=db.get_analysis_uuid(ai.uuid)
            #             db.add_figure_analysis(fig, ai)

    def _save_as_figure(self):
        """
            add a new figure to the database
        """
        db = self.manager.db
        if not isinstance(self.active_editor, FigureEditor):
            return

        with db.session_ctx():
            #use dialog to ask user for figure name and associated project
            dlg = SaveFigureDialog(projects=self.projects,
                                   samples=self.samples)

            # if self.selected_projects:
            #     dlg.selected_project = self.selected_projects[0]
            #
            projects = list(set([ai.project for ai in self.active_editor.analyses]))
            if projects:
                proj = self._get_project_obj(projects[0])
                if proj:
                    dlg.selected_project = proj

            identifiers = list(set([ai.labnumber for ai in self.active_editor.analyses]))
            # print samples
            ss = [self._get_sample_obj(si) for si in identifiers]
            # # print ss
            ss = filter(lambda x: not x is None, ss)
            # # print ss
            dlg.selected_samples = ss

            while 1:
                info = dlg.edit_traits(kind='livemodal')
                if not info.result:
                    return
                if dlg.name:
                    break
                else:
                    if not self.confirmation_dialog('Need to set the name of a "figure" to save. Continue?'):
                        return

            project = None
            if dlg.selected_project:
                project = dlg.selected_project.name

            identifiers = [si.labnumber for si in dlg.selected_samples]
            fid = self.active_editor.save_figure(dlg.name, project, identifiers)
            self._load_sample_figures(dlg.selected_samples)

            idx = next((i for i, o in enumerate(self.ofigures) if o.id == fid), None)

            if idx is not None:
                self.active_editor.saved_figure_id = idx

    def _delete_figures(self, figs):
        db = self.manager.db
        with db.session_ctx() as sess:
            for fi in figs:
                dbfig = db.get_figure(fi.id, key='id')

                sess.delete(dbfig.preference)
                for si in dbfig.labnumbers:
                    sess.delete(si)

                for ai in dbfig.analyses:
                    sess.delete(ai)

                sess.delete(dbfig)

    # ===============================================================================
    # handlers
    # ===============================================================================
    # def _selected_projects_changed(self, old, new):
    #     # self._load_project_figures(new)
    #     super(FigureTask, self)._selected_projects_changed(new)

    @on_trait_change('browser_model:selected_samples')
    def _selected_samples_changed(self, new):
        self._load_sample_figures(new)
        # super(FigureTask, self)._selected_samples_changed(new)

    def _delete_figure_button_fired(self):
        if self.selected_figures:

            if self.confirmation_dialog('Are you sure you want to delete the selected figures?'):
                self._delete_figures(self.selected_figures)
                if self.selected_samples:
                    self._load_sample_figures(self.selected_samples)
                else:
                    self._load_project_figures(self.selected_projects)

    def _figure_kind_changed(self):
        self.selected_figures = []
        if self.figure_kind:
            if self.figure_kind == 'All':
                self.figures = self.ofigures
            else:
                kind = self.figure_kind[:4].lower()
                self.figures = filter(lambda x: x.kind == kind, self.ofigures)

    # def _dclicked_sample_changed(self, new):
    def _dclicked_sample_hook(self):
        if not self.has_active_editor():
            return

        editor = self.active_editor
        if isinstance(editor, FigureEditor):
            editor.saved_figure_id = -1
            editor.clear_aux_plot_limits()
            editor.enable_aux_plots()

        # super(FigureTask, self)._dclicked_sample_changed()
        super(FigureTask, self)._dclicked_sample_hook()

    def _dclicked_figure_changed(self, new):
        if not new:
            return

        sf = self.selected_figures
        if sf:  # and isinstance(self.active_editor, FigureEditor):
            db = self.manager.db
            with db.session_ctx():
                sf = sf[0]
                db_fig = db.get_figure(sf.id, key='id')

                blob = db_fig.preference.options

                kind = db_fig.preference.kind
                open_editor_needed = True
                editor = self.active_editor
                if editor:
                    open_editor_needed = editor.basename != kind

                if open_editor_needed:
                    # open new editor of this kind
                    if kind == 'spec':
                        if editor:
                            editor.close()
                        self.new_spectrum()
                    elif kind == 'ideo':
                        if editor:
                            editor.close()
                        self.new_ideogram()

                if editor:
                    editor.enable_aux_plots()
                    editor.saved_figure_id = int(sf.id)
                    editor.plotter_options_manager.deinitialize()
                    editor.set_items([a.analysis for a in db_fig.analyses])
                    for ai, dbai in zip(editor.analyses, db_fig.analyses):
                        ai.group_id = int(dbai.group or 0)
                        ai.graph_id = int(dbai.graph or 0)

                    editor.plotter_options_manager.load_yaml(blob)
                    editor.rebuild()

    @on_trait_change('plotter_options_pane:pom:plotter_options:[+, refresh_plot_needed, aux_plots:+]')
    def _options_update(self, obj, name, old, new):
        if name == 'initialized' or not obj.initialized:
            return

        # print obj, name
        if self.has_active_editor():
            if name == 'refresh_plot_needed':
                # if self.plotter_options_pane.pom.plotter_options.auto_refresh or name == 'refresh_plot_needed':
                # print 'plotter options rebuild'
                if not isinstance(self.active_editor, RecallEditor):
                    self.active_editor.rebuild()
                    self.active_editor.dump_tool()

    def _set_current_task(self):
        with no_update(self):
            if isinstance(self.active_editor, IdeogramEditor):
                self.browser_model.current_task_name = 'Ideogram'
            elif isinstance(self.active_editor, SpectrumEditor):
                self.browser_model.current_task_name = 'Spectrum'
            else:
                super(FigureTask, self)._set_current_task()

    def _active_editor_changed(self, new):
        editor = self.active_editor
        if editor:
            if isinstance(editor, (FigureEditor, XYScatterEditor)):
                self.plotter_options_pane.pom = pom = editor.plotter_options_manager
                colors = pom.plotter_options.get_group_colors()
                if colors:
                    self.unknowns_pane.adapter.colors = colors

            # self._set_current_task()

        super(FigureTask, self)._active_editor_changed(new)

    @on_trait_change('plotter_options_pane:pom:plotter_options:groups:color')
    def _handle_colors(self):
        pom = self.plotter_options_pane.pom
        colors = pom.plotter_options.get_group_colors()
        self.unknowns_pane.adapter.colors = colors
        self.unknowns_pane.refresh_needed = True

    @on_trait_change('active_editor:refresh_unknowns_table')
    def _ac_refresh_table(self):
        if self.unknowns_pane:
            self.unknowns_pane.refresh_needed = True

    @on_trait_change('active_editor:tag')
    def _handle_graph_tag(self):
        self.set_tag()

    @on_trait_change('active_editor:save_db_figure')
    def _handle_save_db_figure(self):
        self._save_as_figure()

    @on_trait_change('active_editor:invalid')
    def _handle_invalid(self):
        self.set_tag(Tag(name='invalid'))

    # ===========================================================================
    # browser protocol
    # ===========================================================================

    # ===============================================================================
    # defaults
    # ===============================================================================

    def _default_layout_default(self):
        a = Tabbed(browser_pane_item(),
                   PaneItem('pychron.processing.figures.plotter_options'))
        b = PaneItem('pychron.processing.unknowns')
        left = HSplitter(a, b)

        # HSplitter(VSplitter(
        #                       Tabbed(browser_pane_item(),
        #                              PaneItem('pychron.processing.figures.plotter_options'),
        #                              PaneItem('pychron.plot_editor'))),
        #                              PaneItem('pychron.processing.unknowns'))

        return TaskLayout(id='pychron.processing',
                          left=left)

# return TaskLayout(
#     id='pychron.processing',
# left=HSplitter(
#     browser_pane_item(),
#     Tabbed(
#         # PaneItem('pychron.processing.figures.saved_figures'),
#         PaneItem('pychron.processing.unknowns'),
#         PaneItem('pychron.processing.figures.plotter_options'),
#         PaneItem('pychron.plot_editor'))))
# ============= EOF =============================================
#@classmethod
# def group_by(cls, editor, items, key):
#     ids = []
#     for it in items:
#         v = key(it)
#         if not v in ids:
#             ids.append(v)
#
#     sitems = sorted(items, key=key)
#     for k, analyses in groupby(sitems, key=key):
#         gid = ids.index(k)
#         idxs = [items.index(ai) for ai in analyses]
#         editor.set_group(idxs, gid, refresh=False)
# def _append_figure(self, klass):
#     """
#         if selected_samples append all analyses
#         else append selected analyses
#
#     """
#     return
#
#     if isinstance(self.active_editor, klass):
#         sa = self.analysis_table.selected
#         if sa:
#             ts = self.manager.make_analyses(sa)
#         else:
#             ts = [ai for si in self.selected_sample
#                   for ai in self._get_sample_analyses(si)]
#
#         ans = self.manager.make_analyses(ts)
#         if ans:
#             pans = self.active_editor.analyses
#             uuids = [p.uuid for p in pans]
#             fans = [ai for ai in ans if ai.uuid not in uuids]
#
#             pans.extend(fans)
#             self.active_editor.trait_set(unknowns=pans)
#
#         gid = 0
#         for _, gans in groupby(self.active_editor.unknowns, key=lambda x: x.sample):
#             for ai in gans:
#                 ai.group_id = gid
#             gid += 1
#
#         self.active_editor.rebuild(compress_groups=False)