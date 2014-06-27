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
from apptools.preferences.preference_binding import bind_preference
import apptools.sweet_pickle as pickle
from traits.api import List, Str, Bool, Any, String, \
    on_trait_change, Date, Int, Time, Instance, Button, DelegatesTo
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.database.records.isotope_record import GraphicalRecordView
from pychron.envisage.browser.record_views import LabnumberRecordView
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.paths import paths
from pychron.processing.tasks.browser.analysis_table import AnalysisTable
from pychron.processing.tasks.browser.graphical_filter_selector import GraphicalFilterSelector
from pychron.processing.tasks.browser.panes import BrowserPane

'''
add toolbar action to open another editor tab


'''

"""
@todo: how to fit cocktail/air blanks. make special project called references.
added sample to air, cocktail. added samples to references project
"""

DEFAULT_SPEC = 'Spectrometer'
DEFAULT_AT = 'Analysis Type'
DEFAULT_ED = 'Extraction Device'


class BaseBrowserTask(BaseEditorTask, BrowserMixin):
    analysis_table = Instance(AnalysisTable)
    # danalysis_table = Instance(AnalysisTable)

    analysis_filter = String(enter_set=True, auto_set=False)

    irradiations = DelegatesTo('manager')
    irradiation = DelegatesTo('manager')
    levels = DelegatesTo('manager')
    level = DelegatesTo('manager')

    auto_select_analysis = Bool(False)

    mass_spectrometer = Str(DEFAULT_SPEC)
    mass_spectrometers = List
    analysis_type = Str(DEFAULT_AT)
    analysis_types = List
    extraction_device = Str(DEFAULT_ED)
    extraction_devices = List
    start_date = Date
    start_time = Time

    end_date = Date
    end_time = Time
    days_pad = Int(0)
    hours_pad = Int(18)

    datasource_url = String
    # clear_selection_button = Button

    browser_pane = Any
    advanced_query = Button

    graphical_filter_button = Button
    graphical_filtering_max_days = Int

    _activated = False

    def dump_browser_options(self):
        d = {'include_monitors': self.include_monitors,
             'include_unknowns': self.include_unknowns}
        p = os.path.join(paths.hidden_dir, 'browser_options')
        with open(p, 'w') as fp:
            pickle.dump(d, fp)

    def load_browser_options(self):
        d = {}
        p = os.path.join(paths.hidden_dir, 'browser_options')
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    d = pickle.load(fp)
                except Exception:
                    pass
        if d:
            self.trait_set(**d)

    def prepare_destroy(self):
        self.dump_browser_selection()
        self.dump_browser_options()
        self._activated = False

    def activated(self):

        self.load_browser_date_bounds()
        self.load_projects()

        db = self.manager.db
        with db.session_ctx():
            self._load_mass_spectrometers()
            self._load_analysis_types()
            self._load_extraction_devices()

        self.datasource_url = db.datasource_url

        bind_preference(self.search_criteria, 'recent_hours', 'pychron.processing.recent_hours')
        bind_preference(self, 'graphical_filtering_max_days', 'pychron.processing.graphical_filtering_max_days')
        self.load_browser_selection()
        self.load_browser_options()
        self._activated = True

    def _get_selected_analyses(self, unks=None):
        s = self.analysis_table.selected
        if not s:
            if self.selected_samples:
                iv = not self.analysis_table.omit_invalid
                uuids = [x.uuid for x in unks] if unks else None
                s = [ai for ai in self._retrieve_sample_analyses(self.selected_samples,
                                                                 exclude_uuids=uuids,
                                                                 include_invalid=iv,
                                                                 low_post=self.start_date,
                                                                 high_post=self.end_date)]
        return s

    def _load_mass_spectrometers(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_mass_spectrometers()]
        self.mass_spectrometers = ['Spectrometer', 'None'] + ms

    def _load_analysis_types(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_analysis_types()]
        self.analysis_types = ['Analysis Type', 'None'] + ms

    def _load_extraction_devices(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_extraction_devices()]
        self.extraction_devices = ['Extraction Device', 'None'] + ms

    def _create_browser_pane(self, **kw):
        self.browser_pane = BrowserPane(model=self, **kw)
        self.analysis_table.tabular_adapter = self.browser_pane.analysis_tabular_adapter
        self.sample_tabular_adapter = self.browser_pane.sample_tabular_adapter
        return self.browser_pane

    def _ok_query(self):
        ms = self.mass_spectrometer not in (DEFAULT_SPEC, 'None')
        at = self.analysis_type not in (DEFAULT_AT, 'None')
        return ms and at

    def _ok_ed(self):
        return self.extraction_device not in (DEFAULT_ED, 'None')

    def _set_selected_analysis(self, new):
        pass

    def _load_graphical_record_views(self, ans):
        n = len(ans)
        prog = None
        if n > 10:
            prog = self.manager.open_progress(n)

        for i, ai in enumerate(ans):
            ir = GraphicalRecordView(ai)
            if prog:
                prog.change_message('Loading {}-{}. {}'.format(i, n, ir.record_id))
            yield ir

    def _graphical_filter_button_fired(self):
        self.debug('doing graphical filter')
        from pychron.processing.tasks.browser.graphical_filter import GraphicalFilterModel, GraphicalFilterView

        sams = self.selected_samples
        if not sams:
            sams = self.samples

        db = self.manager.db
        with db.session_ctx():
            lns = [si.identifier for si in sams]
            lpost, hpost = db.get_min_max_analysis_timestamp(lns)
            ms = db.get_analysis_mass_spectrometers(lns)

            # if date range > X days make user fine tune range
            if (hpost - lpost).total_seconds() > 3600 * 24 * max(1, self.graphical_filtering_max_days) or len(ms) > 1:
                d = GraphicalFilterSelector(lpost=lpost, hpost=hpost,
                                            available_mass_spectrometers=ms,
                                            mass_spectrometers=ms)
                info = d.edit_traits(kind='livemodal')
                if info.result:
                    lpost, hpost, ms = d.lpost, d.hpost, d.mass_spectrometers
                    if not ms:
                        self.warning_dialog('Please select at least one Mass Spectrometer')
                        return
                else:
                    return

            associated = db.get_date_range_analyses(lpost, hpost, ordering='asc', spectrometer=ms)
            ans = list(self._load_graphical_record_views(associated))

        gm = GraphicalFilterModel(analyses=ans,
                                  projects=[p.name for p in self.selected_projects])
        gm.setup()
        gv = GraphicalFilterView(model=gm)
        info = gv.edit_traits(kind='livemodal')
        if info.result:
            ans = gm.get_selection()
            self.analysis_table.analyses = ans
            self._graphical_filter_hook(ans, gm.is_append)

    def _graphical_filter_hook(self, ans):
        pass

    def _level_changed(self):
        self._find_by_irradiation_fired()

    def __analysis_include_types_changed(self, new):
        if new:
            if self.selected_projects:
                self._filter_by_button_fired()
            else:
                self._find_by_irradiation_fired()
        else:
            self.samples = []

    def _find_by_irradiation_fired(self):
        if not (self.level and self._activated):
            return
        if not self.analysis_include_types:
            self.information_dialog('Select analysis types to include')
            return

        sam = []
        man = self.manager
        db = man.db
        with db.session_ctx():
            level = man.get_level(self.level)
            if level:
                refs, unks = man.group_level(level)
                xs = []
                if 'monitors' in self.analysis_include_types:
                    # if self.include_monitors:
                    xs.extend(refs)
                if 'unknown' in self.analysis_include_types:
                    # if self.include_unknowns:
                    xs.extend(unks)
                if xs:
                    lns = [x.identifier for x in xs]
                    sam = [LabnumberRecordView(li)
                           for li in db.get_labnumbers(lns, low_post=self.low_post,
                                                       high_post=self.high_post)
                           if li.sample]
        self.set_samples(sam, [])

    def _advanced_query_fired(self):

        app = self.window.application
        win, task, is_open = app.get_open_task('pychron.advanced_query')
        task.set_append_replace_enabled(True)
        if is_open:
            win.activate()
        else:
            win.open()

    @on_trait_change('analysis_table:selected')
    def _selected_analysis_changed(self, new):
        self._set_selected_analysis(new)

    @on_trait_change('analysis_table:omit_invalid')
    def _omit_invalid_changed(self):
        self._selected_samples_changed(self.selected_samples)

    def _dclicked_sample_changed(self):
        if self.active_editor:
            ans = self.analysis_table.analyses
            self.active_editor.set_items(ans)

    def _selected_samples_changed(self, new):
        if new:
            at = self.analysis_table
            # lp, hp, lim = at.low_post, at.high_post, at.limit
            lp, hp, lim = self.low_post, self.high_post, at.limit
            if self._recent_low_post:
                lp = self._recent_low_post
                hp = None

            # lp = self.low_post if self.use_low_post else None
            # hp = self.high_post if self.use_high_post else None
            # lim = at.limit
            ans = self._retrieve_sample_analyses(self.selected_samples,
                                                 low_post=lp,
                                                 high_post=hp,
                                                 limit=lim,
                                                 include_invalid=not at.omit_invalid,
                                                 mass_spectrometers=self._recent_mass_spectrometers)
            self.debug('selected samples changed. loading analyses. '
                       'low={}, high={}, limit={}'.format(lp, hp, lim))
            self.analysis_table.set_analyses(ans)

    def _analysis_table_default(self):
        at = AnalysisTable(db=self.manager.db)
        return at

# ============= EOF =============================================

