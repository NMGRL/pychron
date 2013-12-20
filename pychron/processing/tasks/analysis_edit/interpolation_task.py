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
from datetime import timedelta
from traits.api import on_trait_change
from traits.api import Any
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.analysis_edit.panes import ReferencesPane
from pychron.processing.tasks.analysis_edit.adapters import ReferencesAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.browser.browser_task import DEFAULT_AT


class InterpolationTask(AnalysisEditTask):
    references_pane = Any
    references_adapter = ReferencesAdapter
    references_pane_klass = ReferencesPane
    default_reference_analysis_type = 'air'

    def create_dock_panes(self):
        panes = super(InterpolationTask, self).create_dock_panes()
        self._create_references_pane()
        return panes + [self.references_pane]

    def _create_references_pane(self):
        self.references_pane = self.references_pane_klass(adapter_klass=self.references_adapter)
        self.references_pane.load()

    @on_trait_change('references_pane:[items, update_needed]')
    def _update_references_runs(self, obj, name, old, new):
        if not obj._no_update:
            if self.active_editor:
                self.active_editor.references = self.references_pane.items

    @on_trait_change('references_pane:previous_selection')
    def _update_rp_previous_selection(self, obj, name, old, new):
        self._set_previous_selection(obj, new)

    @on_trait_change('references_pane:[append_button, replace_button]')
    def _append_references(self, obj, name, old, new):

        is_append = name == 'append_button'
        if self.active_editor:
            refs = None
            if is_append:
                refs = self.active_editor.references

            s = self._get_selected_analyses(refs)
            if s:
                if is_append:
                    refs = self.active_editor.references
                    refs.extend(s)
                else:
                    self.active_editor.references = s

    @on_trait_change('active_editor:references')
    def _update_references(self):
        if self.references_pane:
            self.references_pane.items = self.active_editor.references

    #def _handle_key_pressed(self, c):
    #    s = self.data_selector.selector.selected
    #    if c == 'r':
    #        self.references_pane.items.extend(s)
    #    elif c == 'R':
    #        self.references_pane.items = s

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
            self.analysis_type = at = self.default_reference_analysis_type

        ref = analyses[-1]
        exd = ref.extract_device
        ms = ref.mass_spectrometer

        self.trait_set(extraction_device=exd or 'Extraction Device',
                       mass_spectrometer=ms or 'Mass Spectrometer', trait_change_notify=False)

        db = self.manager.db
        with db.session_ctx():
            ans = db.get_analyses_data_range(sd, ed,
                                             analysis_type=at,
                                             mass_spectrometer=ms,
                                             extract_device=exd)
            ans = [self._record_view_factory(ai) for ai in ans]
            self.danalysis_table.set_analyses(ans)
            return ans

#============= EOF =============================================
