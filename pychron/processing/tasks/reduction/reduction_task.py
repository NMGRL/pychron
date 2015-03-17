# ===============================================================================
# Copyright 2015 Jake Ross
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
from pyface.tasks.task_layout import TaskLayout, HSplitter, Tabbed, PaneItem
from traits.api import Int, Any, on_trait_change
# ============= standard library imports ========================
from datetime import timedelta
# ============= local library imports  ==========================
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.processing.analyses.analysis import Analysis
from pychron.processing.tasks.analysis_edit.adapters import ReferencesAdapter
from pychron.processing.tasks.analysis_edit.interpolation_task import InterpolationTask
from pychron.processing.tasks.analysis_edit.panes import ReferencesPane
from pychron.processing.tasks.browser.browser_task import DEFAULT_AT
from pychron.processing.tasks.browser.util import browser_pane_item
from pychron.processing.tasks.recall.recall_editor import RecallEditor
from pychron.processing.tasks.reduction.group_entry import ReductionAnalysisGroupEntry


class ReductionTask(InterpolationTask):
    name = 'Reduction'

    references_pane = Any
    references_adapter = ReferencesAdapter
    references_pane_klass = ReferencesPane
    # default_reference_analysis_type = 'air'

    # tool_bars = [SToolBar(FindAssociatedAction(), ),
    # SToolBar(DatabaseSaveAction(),
    # BinAnalysesAction())]

    analysis_group_edit_klass = ReductionAnalysisGroupEntry

    days_pad = Int(0)
    hours_pad = Int(18)

    ic_factor_editor_count = 1
    blank_editor_count = 1

    def new_blank(self):
        from pychron.processing.tasks.reduction.blanks_editor import BlanksEditor

        editor = BlanksEditor(name='Blanks {:03d}'.format(self.blank_editor_count),
                              processor=self.manager,
                              task=self,
                              default_reference_analysis_type='blank_unknown')

        self._open_editor(editor)
        self.blank_editor_count += 1

    def new_ic_factor(self):
        from pychron.processing.tasks.reduction.intercalibration_factor_editor import \
            IntercalibrationFactorEditor

        editor = IntercalibrationFactorEditor(name='ICFactor {:03d}'.format(self.ic_factor_editor_count),
                                              processor=self.manager)
        self._open_editor(editor)
        self.ic_factor_editor_count += 1

    def find_associated_analyses(self):
        if self.has_active_editor():
            self.active_editor.find_references()

    def bin_analyses(self):
        self.debug('binning analyses')
        if self.active_editor:
            self.active_editor.bin_analyses()

    def create_dock_panes(self):
        panes = super(InterpolationTask, self).create_dock_panes()
        self._create_references_pane()
        return panes + [self.references_pane]

    # private
    def _get_analyses_to_group(self):
        sitems = super(InterpolationTask, self)._get_analyses_to_group()
        if self.references_pane:
            items = self.references_pane.selected

        if not items:
            if self.references_pane:
                items = self.references_pane.items

        if not items:
            items = self.analysis_table.selected
            if sitems:
                if items == sitems[0][0]:
                    items = []

        analysis_type = self.default_reference_analysis_type
        if sitems:
            return sitems[0], (items, analysis_type)
        elif items:
            return (items, analysis_type),

    def _make_analysis_group_hook(self, *args, **kw):
        pass

    def _set_tag_hook(self):
        if self.references_pane:
            self.references_pane.refresh_needed = True

    def _get_analyses_to_tag(self):
        ritems = None
        if self.references_pane:
            ritems = [i for i in self.references_pane.items
                      if i.is_temp_omitted()]
            self.debug('Temp omitted analyses {}'.format(len(ritems)))
            if not ritems:
                ritems = self.references_pane.selected

        items = super(InterpolationTask, self)._get_analyses_to_tag()
        if ritems:
            if items:
                items.extend(ritems)
            else:
                items = ritems

        return items

    def _create_references_pane(self):
        self.references_pane = self.references_pane_klass(adapter_klass=self.references_adapter)
        self.references_pane.load()

    def _load_references(self, analyses, atype=None):
        if not hasattr(analyses, '__iter__'):
            analyses = (analyses, )

        ds = [ai.rundate for ai in analyses]
        dt = timedelta(days=self.days_pad, hours=self.hours_pad)

        sd = min(ds) - dt
        ed = max(ds) + dt

        self.start_date = sd.date()
        self.end_date = ed.date()
        self.start_time = sd.time()
        self.end_time = ed.time()

        at = atype or self.analysis_type

        if self.analysis_type == DEFAULT_AT:
            self.analysis_type = at = self.active_editor.default_reference_analysis_type

        ref = analyses[-1]
        exd = ref.extract_device
        ms = ref.mass_spectrometer

        self.trait_set(extraction_device=exd or 'Extraction Device',
                       mass_spectrometer=ms or 'Mass Spectrometer', trait_change_notify=False)

        db = self.manager.db
        with db.session_ctx():
            ans = db.get_analyses_date_range(sd, ed,
                                             analysis_type=at,
                                             mass_spectrometers=ms,
                                             extract_device=exd)
            ans = [self._record_view_factory(ai) for ai in ans]
            # self.danalysis_table.set_analyses(ans)
            return ans

    def _set_analysis_type(self, new, progress=None):
        records = self.unknowns_pane.items
        if records:
            ans = self._load_references(records, new)
            ans = self.manager.make_analyses(ans, progress=progress)
            self.references_pane.items = ans

    # handlers
    @on_trait_change('references_pane:[items, update_needed, dclicked]')
    def _update_references_runs(self, obj, name, old, new):
        if name == 'dclicked':
            if new:
                if isinstance(new.item, (IsotopeRecordView, Analysis)):
                    self._recall_item(new.item)
        elif not obj._no_update:
            if self.active_editor:
                self.active_editor.references = self.references_pane.items

    @on_trait_change('references_pane:previous_selection')
    def _update_rp_previous_selection(self, obj, name, old, new):
        self._set_previous_selection(obj, new)

    @on_trait_change('references_pane:[append_button, replace_button]')
    def _append_references(self, obj, name, old, new):

        is_append = name == 'append_button'
        if self.active_editor:
            if not isinstance(self.active_editor, RecallEditor):
                refs = None
                if is_append:
                    refs = self.active_editor.references

                s = self._get_selected_analyses(unks=refs)
                if s:
                    if is_append:
                        refs = self.active_editor.references
                        refs.extend(s)
                    else:
                        self.active_editor.references = s

    @on_trait_change('active_editor:references')
    def _update_references(self):
        if self.references_pane:
            items = self.active_editor.references
            if self.references_pane.auto_sort:
                items = self.references_pane.sort_items(items)

            self.references_pane.items = items

    @on_trait_change('active_editor:tool:[analysis_type, refresh_references]')
    def _handle_analysis_type(self, obj, name, old, new):
        if name == 'analysis_type':
            if new:
                self._set_analysis_type(new)
        elif name == 'refresh_references':
            if obj.analysis_type:
                self._set_analysis_type(self.analysis_type)

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.processing.reduction',
            left=HSplitter(
                browser_pane_item(),
                Tabbed(PaneItem('pychron.processing.unknowns'),
                       PaneItem('pychron.processing.references'),
                       PaneItem('pychron.processing.controls'))))
        # ============= EOF =============================================