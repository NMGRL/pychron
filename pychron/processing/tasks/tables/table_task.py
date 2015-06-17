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
from itertools import groupby

from traits.api import Instance
from pyface.tasks.action.schema import SToolBar, SGroup




# from pyface.action.action import Action
# from pyface.tasks.action.task_action import TaskAction
# from pyface.tasks.task_layout import TaskLayout, PaneItem
# from pyface.timer.do_later import do_later
# from pyface.tasks.action.schema import SToolBar
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.pipeline.editors.base_adapter import TableSeparator
from pychron.pipeline.editors.fusion.fusion_table_editor import FusionTableEditor
from pychron.pipeline.editors.step_heat.step_heat_table_editor import StepHeatTableEditor
from pychron.processing.tasks.tables.table_actions import ToggleStatusAction, \
    SummaryTableAction, AppendSummaryTableAction, MakePDFTableAction, \
    AppendTableAction, MakeXLSTableAction, MakeCSVTableAction
# from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.tables.panes import TableEditorPane
#from pychron.processing.tasks.browser.browser_task import BrowserTask
# from pychron.pipeline.editors.fusion import FusionTableEditor
from pychron.processing.tasks.tables.table_task_editor import TableTaskEditor
from pychron.pipeline.editors.summary_table_editor import SummaryTableEditor

from traits.api import Str, List
from pyface.timer.do_later import do_later
from pychron.processing.analyses.analysis_group import AnalysisGroup
from traits.has_traits import on_trait_change


class Summary(AnalysisGroup):
    sample = Str
    material = Str
    #     age = Float
    #     age_error = Float
    irradiation = Str
    age_kind = Str


class StepHeatingSummary(Summary):
    age_kind = Str('Plateau')
    age_kinds = List(['Plateau', 'Isochron', 'Integrated'])


class FusionSummary(Summary):
    age_kind = Str('Weighted Mean')
    age_kinds = List(['Weighted Mean', ])


class TableTask(BaseBrowserTask):
    name = 'Tables'
    editor = Instance(TableTaskEditor, ())

    def _tool_bars_default(self):
        xls = True
        try:
            import xlwt
        except ImportError:
            xls = False

        pdf = True
        try:
            from reportlab import Version
        except ImportError:
            pdf = False

        tb1 = SToolBar(
            SGroup(
                ToggleStatusAction(),
                SummaryTableAction(),
                AppendSummaryTableAction()
            ),
            SGroup(
                AppendTableAction()
            ),
            image_size=(16, 16)
        )

        actions = []
        if pdf:
            actions.append(MakePDFTableAction())
        if xls:
            actions.append(MakeXLSTableAction())

        actions.append(MakeCSVTableAction())

        tb2 = SToolBar(*actions,
                       image_size=(16, 16))
        #                     orientation='vertical'
        #                     )

        return [tb1, tb2]


    # def activated(self):
        #editor = FusionTableEditor()
        #self._open_editor(editor)
        self.load_projects()
        #self.selected_project = self.projects[1]

        # editor = StepHeatTableEditor()
        # self._open_editor(editor)


        # def _dclicked_sample_changed(self, new):
        #     self._append_table()
        #         man = self.manager
        #         ans = [ai for ai in self.analyses
        # #                 if not ai.step
        #                 ]  # [:5]
        # #         self.manager.make
        #         ans = man.make_analyses(ans)
        #         aa = [r for ai in ans
        #                 for r in (ai, TableBlank(analysis=(ai)))]
        #
        #         self.active_editor.oitems = aa
        #         self.active_editor.items = aa
        #         self.active_editor.refresh_blanks()

        #self.active_editor.name = self.selected_samples[0].name

    # ===============================================================================
    # task actions
    # ===============================================================================
    # ===========================================================================
    # output actions
    # ===========================================================================
    def make_pdf_table(self):
        ae = self.active_editor
        ae.use_alternating_background = self.editor.use_alternating_background
        ae.notes_template = self.editor.notes_template

        title = self.editor.make_title()

        p = ae.make_pdf_table(title)
        self.view_pdf(p)

    def make_xls_table(self):
        ae = self.active_editor
        ae.use_alternating_background = self.editor.use_alternating_background
        ae.notes_template = self.editor.notes_template

        title = self.editor.make_title()

        p = ae.make_xls_table(title)
        self.view_xls(p)

    def make_csv_table(self):
        ae = self.active_editor
        ae.use_alternating_background = self.editor.use_alternating_background
        ae.notes_template = self.editor.notes_template

        title = self.editor.make_title()

        p = ae.make_csv_table(title)
        self.view_csv(p)

    # ===========================================================================
    #
    # ===========================================================================
    def toggle_status(self):
        ae = self.active_editor
        if ae and ae.selected:
            for s in ae.selected:
                s.temp_status = int(not s.temp_status)

    def append_summary_table(self):
        if isinstance(self.active_editor, SummaryTableEditor):
            #             do_later(self._append_summary_table)
            self._append_summary_table()

    def append_table(self):
        if isinstance(self.active_editor, FusionTableEditor) or \
                isinstance(self.active_editor, StepHeatTableEditor):
            self._append_table()

    def open_summary_table(self):
        do_later(self._open_summary_table)

    def _append_table(self):
        find = lambda x: next((si for si in self.active_editor.items
                               if si.sample == x), None)

        ss = [sa for sa in self.selected_samples if not find(sa.name)]
        man = self.manager
        ans = self._retrieve_sample_analyses(ss)
        ans = man.make_analyses(ans)

        items = self.active_editor.items
        if items:
            items.extend((TableSeparator(),))

        for ln, ais in groupby(ans, key=lambda x: x.labnumber):
            #print ln, ais
            items.extend(list(ais))
            items.extend((TableSeparator(),))

        items.pop(-1)


        #for sa in self.selected_samples:
        #    sam = next((si
        #                for si in self.active_editor.items
        #                if si.sample == sa.name), None)
        #
        #    if sam is None:
        #        man = self.manager
        #        ans = self._get_sample_analyses((sa,))
        #        ans = man.make_analyses(ans)
        #
        #        aa = ans
        #
        #        if self.active_editor.items:
        #            aa.insert(0, TableSeparator())
        #
        #        self.active_editor.items.extend(aa)

    def _append_summary_table(self):
        ss = self.active_editor.items
        items = self._make_summary_table(ss)
        self.active_editor.items.extend(items)

    def _open_summary_table(self):
        items = self._make_summary_table()
        uab = self.editor.use_alternating_background
        editor = SummaryTableEditor(items=items,
                                    name='Summary',
                                    use_alternating_background=uab)
        self._open_editor(editor)

    def _make_summary_table(self, pitems=None):
        def factory(s):
            sam = s.name
            mat = ''
            if s.material:
                mat = s.material

            ans = self._retrieve_sample_analyses(s)
            #             ans = [ai for ai in ans if ai.step == ''][:5]
            #             ans = [ai for ai in ans][:5]
            #            ans = self.manager.make_analyses(ans[:4])
            ans = self.manager.make_analyses(ans)

            ref = ans[0]
            irrad_str = ref.irradiation_label

            klass = StepHeatingSummary if ref.step else FusionSummary
            ss = klass(
                sample=sam,
                material=mat,
                irradiation=irrad_str,
                analyses=ans
            )
            return ss

        if pitems is None:
            pitems = []

        def test(si):
            return next((ss for ss in pitems if ss.sample == si.name), None)

        items = [factory(si)
                 for si in self.selected_samples
                 if not test(si)]

        #         ans = [ai for si in items
        #                     for ai in si.analyses]

        #         self.manager.load_analyses(ans)
        return items


    def create_dock_panes(self):
        return [
            self._create_browser_pane(),
            TableEditorPane(model=self.editor)
        ]


    # ===============================================================================
    # handlers
    # ===============================================================================
    @on_trait_change('editor:age_kind')
    def _edit_handler(self, obj, name, old, new):
        ae = self.active_editor
        if isinstance(ae, SummaryTableEditor):
            if ae.selected:
                for si in ae.selected:
                    si.age_kind = new

                ae.refresh_needed = True

    @on_trait_change('active_editor:selected')
    def _update_selected(self, new):
        if new:
            ref = new[0]
            if hasattr(ref, 'age_kinds'):
                self.editor.age_kinds = ref.age_kinds


# ============= EOF =============================================
