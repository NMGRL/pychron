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
#===============================================================================

#============= enthought library imports =======================
from datetime import timedelta

from pyface.tasks.task_layout import TaskLayout, PaneItem, Tabbed, HSplitter
from pyface.tasks.action.schema import SToolBar


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.globals import globalv
from pychron.processing.tasks.actions.processing_actions import ConfigureRecallAction
from pychron.processing.tasks.browser.util import browser_pane_item
from pychron.processing.tasks.recall.actions import AddIsoEvoAction, AddDiffAction, EditDataAction, RatioEditorAction, \
    SummaryLabnumberAction, CalculationViewAction, SummaryProjectAction, ContextViewAction
from pychron.processing.tasks.recall.context_editor import ContextEditor
from pychron.processing.tasks.recall.diff_editor import DiffEditor
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.analysis_edit.panes import ControlsPane
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from pychron.processing.tasks.recall.recall_editor import RecallEditor
from pychron.processing.utils.grouping import group_analyses_by_key


class RecallTask(AnalysisEditTask):
    name = 'Recall'
    id = 'pychron.recall'

    tool_bars = [
        SToolBar(AddIsoEvoAction(),
                 AddDiffAction(),
                 EditDataAction(),
                 ConfigureRecallAction(),
                 CalculationViewAction(),
                 RatioEditorAction(),
                 SummaryProjectAction(),
                 SummaryLabnumberAction(),
                 ContextViewAction(),
                 image_size=(16, 16))]
    auto_select_analysis = False
    _append_replace_analyses_enabled = False

    def open_ratio_editor(self):
        if self.has_active_editor():
            from pychron.processing.ratios.ratio_editor import RatioEditor

            rec = self.active_editor.model
            self.manager.load_raw_data(rec)
            editor = RatioEditor(analysis=rec)
            try:
                editor.setup_graph()
                self._open_editor(editor)
            except BaseException, e:
                self.warning_dialog('Invalid analysis for ratio editing. {}'.format(e))

    def open_calculation_view(self):
        if self.has_active_editor():
            from pychron.processing.analyses.view.calculation_view import CalculationView

            cv = CalculationView()
            cv.load_view(self.active_editor.model)
            cv.edit_traits()

    def open_existing_context_editor(self):
        an=self.active_editor.model.record_id
        name='Context {}'.format(an)
        for e in self.editor_area.editors:
            if e.name==name:
                self.activate_editor(e)
                return True

    def new_context_editor(self):
        if self.has_active_editor(RecallEditor):
            if self.open_existing_context_editor():
                return

            db = self.manager.db
            with db.session_ctx():

                an=self.active_editor.model
                a=an.analysis_timestamp
                pad=timedelta(hours=1)
                lp=a-pad
                hp=a+pad

                ans = db.get_analyses_date_range(lp, hp, mass_spectrometers=an.mass_spectrometer)
                ans = self.manager.make_analyses(ans)
                ans = sorted(ans, key=lambda x: x.timestamp)
                editor = ContextEditor(analyses=ans,
                                       name='Context {}'.format(an.record_id),
                                       root_analysis=an)
                self._open_editor(editor)

    def new_summary_project_editor(self):
        from pychron.processing.tasks.recall.summary_project_editor import SummaryProjectEditor

        db = self.manager.db
        with db.session_ctx():
            ans = self._get_selected_analyses(selection=self.selected_samples, make_records=False)
            ans = self.manager.make_analyses(ans, calculate_age=True)
            group_analyses_by_key(ans, lambda x: x.labnumber)
            name = ','.join([p.name for p in self.selected_projects])
            editor = SummaryProjectEditor(name='{} Sum.'.format(name),
                                          analyses=ans)
            editor.load()
            self._open_editor(editor)

    def new_summary_labnumber_editor(self):
        from pychron.processing.tasks.recall.summary_labnumber_editor import SummaryLabnumberEditor

        db = self.manager.db
        with db.session_ctx():
            for si in self.selected_samples:
                ans = self._get_selected_analyses(selection=[si], make_records=False)
                ans = self.manager.make_analyses(ans, calculate_age=True)
                editor = SummaryLabnumberEditor(name='{} ({})Sum.'.format(si.identifier,
                                                                          si.name),
                                                analyses=ans)
                editor.load()
                self._open_editor(editor)

    # def append_unknown_analyses(self, ans):
    #
    #     for i, ai in enumerate(ans):
    #         if not (i == 0 and self.active_editor):
    #             self.new_editor()
    #         self._set_selected_analysis(ai)
    #
    # def replace_unkonwn_analyses(self, ans):
    #     for ei in self.editor_area.editors:
    #         ei.close()
    #
    #     self.append_unknown_analyses(ans)
    #
    # def new_editor(self):
    #     editor = RecallEditor()
    #     self._open_editor(editor)

    def edit_data(self):
        if not self.has_active_editor():
            return

        editor = self.active_editor
        if hasattr(editor, 'edit_view') and editor.edit_view:
            editor.edit_view.show()
        else:
            from pychron.processing.tasks.recall.edit_analysis_view import AnalysisEditView

            e = AnalysisEditView(editor)

            # e.load_isotopes()
            # info = e.edit_traits()
            # info = timethis(e.edit_traits)
            info = self.application.open_view(e)
            e.control = info.control
            editor.edit_view = e

    def add_diff(self):
        if not self.has_active_editor():
            return

        left = None
        if self.active_editor:
            left = self.active_editor.model

        if left:
            editor = DiffEditor()
            editor.set_diff(left)
            self.editor_area.add_editor(editor)

    def create_dock_panes(self):
        self.controls_pane = ControlsPane()
        self.plot_editor_pane = PlotEditorPane()
        panes = [
            self.controls_pane,
            self.plot_editor_pane,
            self._create_browser_pane()]

        return panes

    def activated(self):
        super(RecallTask, self).activated()

        if globalv.recall_debug:
            try:
                a=self.analysis_table.analyses[3]
                self.recall([a])
                # self.new_context_editor()
            except IndexError:
                pass

    def _dclicked_sample_changed(self):
        pass

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.recall',
            left=HSplitter(Tabbed(
                browser_pane_item()),
                           PaneItem('pychron.processing.controls')))
        #============= EOF =============================================
        # def activated(self, load=False):
        # super(RecallTask, self).activated()
        # self.recall([DummyRecord('f4d301bd-a217-42a2-b4c9-c1696089acb2')])

        #     self.load_projects()
        #     # if load:
        #         # editor = RecallEditor()
        #         # self._open_editor(editor)
        #
        #         #db = self.manager.db
        #         #db.selector.limit = 100
        #         #db.selector.load_recent()
        #
        #     super(RecallTask, self).activated()
        # def _set_selected_analysis(self, an):
        #     if an and isinstance(self.active_editor, RecallEditor):
        #         if hasattr(an, '__iter__'):
        #             an=an[0]
        #
        #         an = self.manager.make_analysis(an, calculate_age=True)
        #         self.active_editor.analysis_view = an.analysis_view
        #         self.controls_pane.tool = an.analysis_view.selection_tool
        #         self.active_editor.model = an
        # def _active_editor_changed(self):
        #     if self.active_editor:
        #         if hasattr(self.active_editor, 'analysis_view'):
        #             self.controls_pane.tool = self.active_editor.analysis_view.selection_tool
        #         else:
        #             self.controls_pane.tool = self.active_editor.tool

        # def add_iso_evo(self, name=None, rec=None):
        #     if rec is None:
        #         if self.active_editor is not None:
        #             rec = self.active_editor.model
        #             name = self.active_editor.name
        #
        #     if rec is None:
        #         return
        #
        #     from pychron.processing.tasks.isotope_evolution.isotope_evolution_editor import IsotopeEvolutionEditor
        #     name='IsoEvo {}'.format(name)
        #     editor=self.get_editor(name)
        #     if editor:
        #         self.activate_editor(editor)
        #     else:
        #         ieditor = IsotopeEvolutionEditor(name=name,processor=self.manager)
        #         ieditor.set_items([rec])
        #         self.editor_area.add_editor(ieditor)