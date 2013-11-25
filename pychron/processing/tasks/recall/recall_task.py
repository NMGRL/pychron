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
from pyface.tasks.task_layout import TaskLayout, PaneItem, Tabbed, HSplitter
from pyface.tasks.action.schema import SToolBar

from pychron.processing.tasks.recall.actions import AddIsoEvoAction, AddDiffAction
from pychron.processing.tasks.recall.diff_editor import DiffEditor
from pychron.processing.tasks.recall.recall_editor import RecallEditor
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.analysis_edit.panes import ControlsPane
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane

#============= standard library imports ========================
#============= local library imports  ==========================



class RecallTask(AnalysisEditTask):
    name = 'Recall'

    tool_bars = [
        SToolBar(AddIsoEvoAction(),
                 AddDiffAction(),
                 image_size=(16, 16))]

    def activated(self, load=False):
        self.load_projects()
        if load:
            editor = RecallEditor()
            self._open_editor(editor)

            db = self.manager.db
            db.selector.limit = 100
            db.selector.load_recent()

            super(RecallTask, self).activated()

    def new_editor(self):
        editor = RecallEditor()
        self._open_editor(editor)

    def _set_selected_analysis(self, an):
        if an and isinstance(self.active_editor, RecallEditor):
        #             l, a, s = strip_runid(s)
        #             an = self.manager.db.get_unique_analysis(l, a, s)
        #    print 'asdfasfdasdfasdf'
            an = self.manager.make_analysis(an,
                                            calculate_age=True)
            #             an.load_isotopes(refit=False)
            #self.active_editor.analysis_summary = an.analysis_summary
            self.active_editor.analysis_view = an.analysis_view
            self.controls_pane.tool = an.analysis_view.selection_tool
            self.active_editor.model = an

#    def create_dock_panes(self):
#        return [self._create_browser_pane(multi_select=False)]

    def _dclicked_sample_changed(self):
        pass

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.recall',
            left=HSplitter(Tabbed(
                PaneItem('pychron.browser'),
                PaneItem('pychron.search.query'),
            ),
                           PaneItem('pychron.analysis_edit.controls')
            ))

    def create_dock_panes(self):
        self.controls_pane = ControlsPane()
        self.plot_editor_pane = PlotEditorPane()
        panes = [
            self.controls_pane,
            self.plot_editor_pane,
            self._create_browser_pane()
        ]
        ps = self._create_db_panes()
        if ps:
            panes.extend(ps)
        return panes

    #def recall(self, records):
    #
    #    ans = self.manager.make_analyses(records, calculate_age=True)
    #
    #    def func(rec):
    #    #             rec.load_isotopes()
    #        rec.calculate_age()
    #        reditor = RecallEditor(analysis_view=rec.analysis_view)
    #        self.editor_area.add_editor(reditor)
    #
    #    #             self.add_iso_evo(reditor.name, rec)
    #
    #    if ans:
    #        for ri in ans:
    #            func(ri)
    #            #             self.manager._load_analyses(ans, func=func)
    #
    #        ed = self.editor_area.editors[-1]
    #        self.editor_area.activate_editor(ed)

    def add_iso_evo(self, name=None, rec=None):
        if rec is None:
            if self.active_editor is not None:
                rec = self.active_editor.model
                name = self.active_editor.name

        if rec is None:
            return

        from pychron.processing.tasks.isotope_evolution.isotope_evolution_editor import IsotopeEvolutionEditor

        ieditor = IsotopeEvolutionEditor(
            name='IsoEvo {}'.format(name),
            processor=self.manager)

        ieditor.unknowns = [rec]
        self.editor_area.add_editor(ieditor)

    def add_diff(self):
        left = None
        if self.active_editor:
            left = self.active_editor.model

        if left:
            editor = DiffEditor()
            editor.set_diff(left)
            self.editor_area.add_editor(editor)

#============= EOF =============================================
