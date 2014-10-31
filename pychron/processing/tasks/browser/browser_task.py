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
from datetime import datetime, timedelta

from apptools.preferences.preference_binding import bind_preference
from traits.api import List, Str, Bool, Any, String, \
    on_trait_change, Date, Int, Time, Instance, Button

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.database.records.isotope_record import GraphicalRecordView
from pychron.envisage.browser.record_views import ProjectRecordView
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.processing.selection.data_selector import DataSelector
from pychron.processing.tasks.browser.analysis_table import AnalysisTable
from pychron.processing.tasks.browser.graphical_filter_selector import GraphicalFilterSelector
from pychron.processing.tasks.browser.panes import BrowserPane
from pychron.processing.tasks.browser.util import get_pad

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


def unique_list(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x.name in seen or seen_add(x.name))]


class BaseBrowserTask(BaseEditorTask, BrowserMixin):
    analysis_table = Instance(AnalysisTable)
    # danalysis_table = Instance(AnalysisTable)

    analysis_filter = String(enter_set=True, auto_set=False)

    irradiations = List  # Property #DelegatesTo('manager')
    irradiation = Str  # Property # DelegatesTo('manager')
    irradiation_enabled = Bool
    levels = List  # Property #DelegatesTo('manager')
    level = Str  # Property #DelegatesTo('manager')

    auto_select_analysis = Bool(False)

    # use_mass_spectrometers = Bool
    # mass_spectrometer_includes = List
    # available_mass_spectrometers = List
    # mass_spectrometer = Str(DEFAULT_SPEC)
    # mass_spectrometers = List

    # analysis_type = Str(DEFAULT_AT)
    # analysis_types = List
    # extraction_device = Str(DEFAULT_ED)
    # extraction_devices = List
    start_date = Date
    start_time = Time

    end_date = Date
    end_time = Time

    datasource_url = String
    # clear_selection_button = Button

    browser_pane = Any
    # advanced_query = Button

    data_selector = Instance(DataSelector)

    filter_by_button = Button
    graphical_filter_button = Button
    graphical_filtering_max_days = Int
    toggle_view = Button

    _activated = False
    update_on_level_change = True

    initialize_workspace = True
    _top_level_filter = None
    _append_replace_analyses_enabled = True

    bin_tol_hrs = Int

    def _identifier_change_hook(self, db, new, lns):
        if len(new) > 2:
            if self.project_enabled:
                def get_projects():
                    for li in lns:
                        try:
                            yield li.sample.project
                        except AttributeError, e:
                            print e

                ps = sorted(list(set(get_projects())))
                ps = [ProjectRecordView(p) for p in ps]
                self.projects = ps
                self.selected_projects = []

            if self.irradiation_enabled:
                def get_irradiations():
                    for li in lns:
                        try:
                            yield li.irradiation_position.level.irradiation.name
                        except AttributeError:
                            pass
                irrads =sorted(list(set(get_irradiations())))
                self.irradiations = irrads
                if irrads:
                    self.irradiation=irrads[0]

    def refresh_samples(self):
        self.debug('refresh samples')
        self.set_samples(self._retrieve_samples())

    def load_time_view(self):
        self.debug('load time view')
        db = self.db
        with db.session_ctx():
            ss = [si.labnumber for si in self.selected_samples]
            bt = self.bin_tol_hrs
            if not bt:
                self.information_dialog('Set "Analysis Series Binning" in Preferences defaulting to 2hrs')
                bt = 2

            ts = db.get_analysis_timestamps(ss, binned=bt * 3600)
            ms = db.get_labnumber_mass_spectrometers(ss)
            n = len(ts)
            if n > 1:
                if not self.confirmation_dialog('The date range you selected is to large. It will be '
                                                'broken into {} subranges.\nDo you want to Continue?'.format(n)):
                    return

                xx = []
                for ti in ts:
                    lp, hp = ti[0], ti[-1]
                    pad = get_pad(lp, hp)
                    if not pad:
                        break
                    ans = self._get_analysis_series(pad.low_post, pad.high_post, ms)
                    xx.extend(ans)
            else:
                lp, hp = db.get_min_max_analysis_timestamp(ss)
                pad = get_pad(lp, hp)
                if not pad:
                    return
                xx = self._get_analysis_series(pad.low_post, pad.high_post, ms)

            self.analysis_table.set_analyses(xx)

    def prepare_destroy(self):
        self.dump_browser()
        self._activated = False

    def activate_workspace(self):
        if self.initialize_workspace:
            workspace = self.application.get_service('pychron.workspace.workspace_manager.WorkspaceManager')
            if workspace:
                self.use_workspace = workspace.active
                self.workspace = workspace

    def load_irradiation(self):
        if self.use_workspace:
            obj = self.workspace.index_db
        else:
            obj = self.manager

        self.irradiations = irs = obj.irradiations
        if irs:
            self.irradiation = irs[0]
            self.levels = ls = obj.levels
            if ls:
                self.level = ls[0]

    def activated(self):
        self._top_level_filter = None
        self.activate_workspace()

        self.load_browser_options()
        if self.sample_view_active:
            self._activate_sample_browser()
        else:
            self._activate_query_browser()

    def _get_analysis_series(self, lp, hp, ms):
        self.use_low_post = True
        self._set_low_post(lp)
        self.use_high_post = True
        self._set_high_post(hp)

        ans = self._retrieve_analyses(low_post=lp,
                                      high_post=hp,
                                      mass_spectrometers=ms)
        return ans

    def _get_manager(self):
        if self.use_workspace:
            obj = self.workspace.index_db
        else:
            obj = self.manager
        return obj

    def _load_projects_for_irradiation(self):
        if self.irradiation:
            db = self.db
            with db.session_ctx():
                ps = db.get_projects(irradiation=self.irradiation,
                                     level=self.level)
                ps = self._make_project_records(ps, include_recent_first=False)
                self.projects = ps

    def _load_projects_and_irradiations(self):
        if self.use_mass_spectrometers:
            ms = self.mass_spectrometer_includes
            if ms:
                db = self.db
                with db.session_ctx():
                    ps = db.get_projects(mass_spectrometers=ms)
                    ps = self._make_project_records(ps, include_recent_first=False)
                    self.projects = ps

                    irs = db.get_irradiations(mass_spectrometers=ms)
                    self.irradiations = [i.name for i in irs]

    def _activate_query_browser(self):
        psel = self.data_selector
        selector = self.data_selector.selector
        selector.queries = []

        if self.project_enabled and self.selected_projects:
            for i, si in enumerate(self.selected_projects):
                selector.add_query('Project', '=', si.name, chain_rule='Or' if i > 0 else '')

        if self.use_analysis_type_filtering and self.analysis_include_types:
            for at in self.analysis_include_types:
                selector.add_query('Analysis Type', '=', at, chain_rule='Or')

        if self.use_low_post:
            selector.add_query('Run Date/Time', '>', self.low_post)
        if self.use_high_post:
            selector.add_query('Run Date/Time', '<', self.high_post)

        if not selector.queries:
            if not psel.active:
                selector.load_recent()
        else:
            selector.execute_query()

        psel.active = True
        self.browser_pane.name = 'Browser/Query'

    def _activate_sample_browser(self):
        if not self._activated:
            self.load_browser_date_bounds()
            self.load_projects()

            db = self.manager.db
            with db.session_ctx():
                self._load_mass_spectrometers()
            # self._load_analysis_types()
            #     self._load_extraction_devices()

            self.datasource_url = db.datasource_url

            pid = 'pychron.browsing'
            bind_preference(self.search_criteria, 'recent_hours', '{}.recent_hours'.format(pid))
            bind_preference(self, 'graphical_filtering_max_days', '{}.graphical_filtering_max_days'.format(pid))
            bind_preference(self, 'bin_tol_hrs', '{}.bin_tol_hrs'.format(pid))
            self.load_browser_selection()

        self.browser_pane.name = 'Browser/Sample'
        self._activated = True

    def _get_selected_analyses(self, unks=None, selection=None, make_records=True):
        """
        """
        if selection is None:
            if self.analysis_table.selected:
                ret = self.analysis_table.selected
            elif self.data_selector.selector.selected:
                ret = self.data_selector.selector.selected
            else:
                selection = self.selected_samples

        if selection:
            iv = not self.analysis_table.omit_invalid
            uuids = [x.uuid for x in unks] if unks else None
            ret = [ai for ai in self._retrieve_sample_analyses(selection,
                                                               exclude_uuids=uuids,
                                                               include_invalid=iv,
                                                               low_post=self.start_date,
                                                               high_post=self.end_date,
                                                               make_records=make_records)]
        return ret

    def _load_mass_spectrometers(self):
        db = self.db
        ms = [mi.name for mi in db.get_mass_spectrometers()]
        self.available_mass_spectrometers = ms
        # self.mass_spectrometers = ['Spectrometer', 'None'] + ms

    def _load_analysis_types(self):
        db = self.db
        ms = [mi.name for mi in db.get_analysis_types()]
        self.analysis_types = ['Analysis Type', 'None'] + ms

    def _load_extraction_devices(self):
        db = self.db
        ms = [mi.name for mi in db.get_extraction_devices()]
        self.extraction_devices = ['Extraction Device', 'None'] + ms

    def _create_browser_pane(self, **kw):
        self.browser_pane = BrowserPane(model=self, **kw)
        self.analysis_table.tabular_adapter = self.browser_pane.analysis_tabular_adapter
        self.sample_tabular_adapter = self.browser_pane.sample_tabular_adapter
        return self.browser_pane

    # def _ok_query(self):
    # ms = self.mass_spectrometer not in (DEFAULT_SPEC, 'None')
    #     at = self.analysis_type not in (DEFAULT_AT, 'None')
    #     return ms and at

    def _ok_ed(self):
        return self.extraction_device not in (DEFAULT_ED, 'None')

    def _set_selected_analysis(self, new):
        pass

    def _selector_dclick(self, item):
        pass

    def _graphical_filter_hook(self, ans, is_append):
        pass

    def _browser_options_hook(self, d):
        d['irradiation_enabled'] = self.irradiation_enabled

    def _selected_projects_change_hook(self, names):
        if not self._top_level_filter:
            self._top_level_filter = 'project'
        if names:
            if self._top_level_filter == 'project':
                db = self.db
                with db.session_ctx():
                    irrads = db.get_irradiations(project_names=names)
                    self.irradiations = [i.name for i in irrads]

    def _retrieve_samples_hook(self, db):
        low_post = self.low_post
        high_post = self.high_post
        ms = None
        if self.use_mass_spectrometers:
            ms = self.mass_spectrometer_includes

        def get_labnumbers(ids=None):
            return db.get_labnumbers(identifiers=ids,
                                     low_post=low_post,
                                     high_post=high_post,
                                     mass_spectrometers=ms,
                                     filter_non_run=self.filter_non_run_samples)

        def atypes_func(obj, func):
            func = getattr(man, func)
            refs, unks = func(obj)
            nls = []
            if 'monitors' in atypes:
                nls.extend(refs)
            if 'unknown' in atypes:
                nls.extend(unks)
            return nls

        man = self.manager
        ls = []
        atypes = self.analysis_include_types if self.use_analysis_type_filtering else None

        if self.project_enabled:
            if not self.irradiation_enabled:
                ls = super(BaseBrowserTask, self)._retrieve_samples_hook(db)
            else:
                if self.selected_projects and self.irradiation_enabled and self.irradiation:
                    ls = db.get_project_irradiation_labnumbers([si.name for si in self.selected_projects],
                                                               self.irradiation,
                                                               self.level,
                                                               low_post=low_post,
                                                               high_post=high_post,
                                                               mass_spectrometers=ms,
                                                               filter_non_run=self.filter_non_run_samples,
                                                               analysis_types=atypes)
                    if atypes:
                        ls = atypes_func(ls)

        elif self.irradiation_enabled and self.irradiation:
            if not self.level:
                ls = db.get_irradiation_labnumbers(self.irradiation, self.level,
                                                   low_post=low_post,
                                                   high_post=high_post,
                                                   mass_spectrometers=ms,
                                                   filter_non_run=self.filter_non_run_samples,
                                                   analysis_types=atypes)
            else:
                # level = man.get_level(self.level)
                level = db.get_irradiation_level(self.irradiation,
                                                 self.level)
                if level:
                    if atypes:
                        xs = atypes_func(level, 'group_level')
                    else:
                        xs = [p.labnumber for p in level.positions]

                    if xs:
                        lns = [x.identifier for x in xs]
                        ls = get_labnumbers(ids=lns)

        elif low_post or high_post:
            ls = get_labnumbers()
            ans = db.get_analyses_date_range(low_post, high_post, mass_spectrometers=ms)
            ans = self._make_records(ans)
            self.analysis_table.set_analyses(ans)

        return ls

    # handlers
    def _filter_by_button_fired(self):
        self.debug('filter by button fired low_post={}, high_post={}'.format(self.low_post, self.high_post))
        if self.sample_view_active:
            self._filter_by_hook()
        else:
            self.data_selector.execute_query()

    def _toggle_view_fired(self):
        self.sample_view_active = not self.sample_view_active
        if not self.sample_view_active:
            self._activate_query_browser()
        else:
            self._activate_sample_browser()

        self.dump_browser_options()

    def _graphical_filter_button_fired(self):
        self.debug('doing graphical filter')
        from pychron.processing.tasks.browser.graphical_filter import GraphicalFilterModel, GraphicalFilterView

        sams = self.selected_samples
        if not sams:
            sams = self.samples

        db = self.db
        with db.session_ctx():
            if sams:
                lns = [si.identifier for si in sams]
                lpost, hpost = db.get_min_max_analysis_timestamp(lns)
                ams = ms = db.get_analysis_mass_spectrometers(lns)
                force = False
            else:
                force = True
                lpost = datetime.now() - timedelta(hours=self.search_criteria.recent_hours)
                hpost = datetime.now()
                ams = [mi.name for mi in db.get_mass_spectrometers()]
                ms = ams[:1]

            # if date range > X days make user fine tune range
            tdays = 3600 * 24 * max(1, self.graphical_filtering_max_days)

            if force or (hpost - lpost).total_seconds() > tdays or len(ms) > 1:
                d = GraphicalFilterSelector(lpost=lpost, hpost=hpost,
                                            available_mass_spectrometers=ams,
                                            mass_spectrometers=ms)
                info = d.edit_traits(kind='livemodal')
                if info.result:
                    lpost, hpost, ms = d.lpost, d.hpost, d.mass_spectrometers
                    if not ms:
                        self.warning_dialog('Please select at least one Mass Spectrometer')
                        return
                else:
                    return

            ans = db.get_date_range_analyses(lpost, hpost, ordering='asc', spectrometer=ms)

            def func(xi, prog, i, n):
                if prog:
                    prog.change_message('Loading {}-{}. {}'.format(i, n, xi.record_id))
                return GraphicalRecordView(xi)

            ans = progress_loader(ans, func)
            if not ans:
                return

        gm = GraphicalFilterModel(analyses=ans,
                                  projects=[p.name for p in self.selected_projects])
        gm.setup()
        gv = GraphicalFilterView(model=gm)
        info = gv.edit_traits(kind='livemodal')
        if info.result:
            ans = gm.get_selection()
            self.analysis_table.analyses = ans
            self._graphical_filter_hook(ans, gm.is_append)

    def _use_mass_spectrometer_changed(self):
        self.refresh_samples()

    def _mass_spectrometer_includes_changed(self):
        if self.mass_spectrometer_includes:
            if self.identifier:
                self._identifier_changed(self.identifier)
            else:
                self.refresh_samples()
                self._load_projects_and_irradiations()

    def _irradiation_enabled_changed(self, new):
        if not new:
            self._top_level_filter = None
            self.projects = self.oprojects
        else:
            self._load_projects_for_irradiation()

    def _project_enabled_changed(self, new):
        if not new:
            self._top_level_filter = None
            obj = self._get_manager()
            self.irradiations = obj.irradiations

    @on_trait_change('irradiation,level')
    def _handle_irradiation_change(self, name, new):
        obj = self._get_manager()
        setattr(obj, name, new)

        if not self._top_level_filter:
            self._top_level_filter = 'irradiation'

        if self._top_level_filter == 'irradiation':
            self._load_projects_for_irradiation()

        if name == 'irradiation':
            self.levels = obj.levels
        elif name == 'level':
            self.set_samples(self._retrieve_samples())

    def _use_analysis_type_filtering_changed(self):
        self.refresh_samples()

    def _level_changed(self):
        if self.update_on_level_change:
            self.refresh_samples()

    def __analysis_include_types_changed(self, new):
        if new:
            if self.selected_projects:
                self._filter_by_button_fired()
            else:
                self.refresh_samples()
        else:
            self.samples = []

            # def _find_by_irradiation_fired(self):
            # if not (self.level and self._activated):
            # return
            # self.refresh_samples()

            # atypes=self.analysis_include_types
            # if self.use_analysis_type_filtering and not atypes:
            # self.information_dialog('Select analysis types to include')
            # return
            # if not atypes:
            # atypes =('monitors','unknown')
            #
            # sam = []
            # man = self.manager
            # db = self.db
            # with db.session_ctx():
            # level = man.get_level(self.level)
            #     if level:
            #         refs, unks = man.group_level(level)
            #         xs = []
            #         if 'monitors' in atypes:
            #             xs.extend(refs)
            #         if 'unknown' in atypes:
            #             xs.extend(unks)
            #         if xs:
            #             lns = [x.identifier for x in xs]
            #             sam = [LabnumberRecordView(li)
            #                    for li in db.get_labnumbers(lns, low_post=self.low_post,
            #                                                high_post=self.high_post)
            #                    if li.sample]

            # sam=self._retrieve_samples()
            # self.set_samples(sam)

    # def _advanced_query_fired(self):
    # app = self.window.application
    # win, task, is_open = app.get_open_task('pychron.advanced_query')
    # task.set_append_replace_enabled(True)
    # if is_open:
    # win.activate()
    # else:
    # win.open()

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
            # if self._recent_low_post:
            # lp = self._recent_low_post
            # hp = None

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
            self.dump_browser()

    @on_trait_change('data_selector.database_selector.dclicked')
    def _handle_selector_dclick(self, new):
        self._selector_dclick(new.item)

    def _analysis_table_default(self):
        at = AnalysisTable(db=self.db,
                           append_replace_enabled=self._append_replace_analyses_enabled)
        return at

    def _data_selector_default(self):
        return DataSelector(database_selector=self.manager.db.selector)

# ============= EOF =============================================

