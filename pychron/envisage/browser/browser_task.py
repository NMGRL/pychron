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

from traits.api import Any, on_trait_change, Date, Time, Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.strtools import to_bool
from pychron.envisage.tasks.editor_task import BaseEditorTask
# from pychron.processing.selection.data_selector import DataSelector
# from pychron.processing.tasks.browser.panes import BrowserPane
from pychron.processing.tasks.recall.recall_editor import RecallEditor

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


# NCHARS = 60
# REG = re.compile(r'.' * NCHARS)


class BaseBrowserTask(BaseEditorTask):
    # filter_focus = Bool(True)
    # use_focus_switching = Bool(True)
    # filter_label = Property(Str, depends_on='filter_focus')
    #
    # irradiation_visible = Property(depends_on='filter_focus')
    # analysis_types_visible = Property(depends_on='filter_focus')
    # date_visible = Property(depends_on='filter_focus')
    # mass_spectrometer_visible = Property(depends_on='filter_focus')
    # identifier_visible = Property(depends_on='filter_focus')
    # project_visible = Property(depends_on='filter_focus')
    default_task_name = 'Recall'
    browser_model = Instance('pychron.envisage.browser.browser_model.BrowserModel')
    dvc = Instance('pychron.dvc.dvc.DVC')
    # analysis_filter = String(enter_set=True, auto_set=False)

    # irradiations = List  # Property #DelegatesTo('manager')
    # irradiation = Str  # Property # DelegatesTo('manager')
    # irradiation_enabled = Bool
    # levels = List  # Property #DelegatesTo('manager')
    # level = Str  # Property #DelegatesTo('manager')

    # auto_select_analysis = Bool(False)

    start_date = Date
    start_time = Time

    end_date = Date
    end_time = Time

    # datasource_url = String

    browser_pane = Any

    # data_selector = Instance(DataSelector)

    # filter_by_button = Button
    # graphical_filter_button = Button
    # toggle_view = Button
    # toggle_focus = Button

    _activated = False
    # update_on_level_change = True

    initialize_workspace = True
    _top_level_filter = None
    _append_replace_analyses_enabled = True

    def __init__(self, *args, **kw):
        super(BaseBrowserTask, self).__init__(*args, **kw)

    def prepare_destroy(self):
        if self.browser_model:
            self.browser_model.dump_browser()
            self._activated = False

            self._destroy_browser_model()

    def activate_workspace(self):
        if self.initialize_workspace:
            workspace = self.application.get_service('pychron.workspace.workspace_manager.WorkspaceManager')
            if workspace:
                self.browser_model.use_workspace = workspace.active
                self.workspace = workspace

    def activated(self):

        # model = self._get_browser_model()
        # self.browser_model = model
        if not self.browser_model.is_activated:
            self._setup_browser_model()

        with no_update(self):
            self.browser_model.current_task_name = self.default_task_name

        # self._top_level_filter = None
        self.activate_workspace()

        self.browser_model.activated()

        if to_bool(self.application.preferences.get('pychron.dvc.enabled')):
            self.dvc = self.application.get_service('pychron.dvc.dvc.DVC')
        # if self.browser_model.sample_view_active:
        self._activate_sample_browser()
        # else:

        # self._activate_query_browser()

    def recall(self, records, open_copy=False):
        """
            if analysis is already open activate the editor
            otherwise open a new editor

            if open_copy is True, allow multiple instances of the same analysis
        """
        self.debug('recalling records {}'.format(records))

        if not isinstance(records, (list, tuple)):
            records = [records]
        elif isinstance(records, tuple):
            records = list(records)

        if not open_copy:
            records = self._open_existing_recall_editors(records)
            if records:
                # ans = None
                # if self.browser_model.use_workspace:
                #     ans = self.workspace.make_analyses(records)
                # elif self.dvc:
                ans = self.dvc.make_analyses(records)
                if ans:
                    self._open_recall_editors(ans)
                else:
                    self.warning('failed making records')

    # private
    def _get_editor_by_uuid(self, uuid):
        return next((editor for editor in self.editor_area.editors
                     if isinstance(editor, RecallEditor) and
                     editor.model and editor.model.uuid == uuid), None)

    def _open_existing_recall_editors(self, records):
        editor = None
        # check if record already is open
        for r in records:
            editor = self._get_editor_by_uuid(r.uuid)
            if editor:
                records.remove(r)

        # activate editor if open
        if editor:
            self.activate_editor(editor)
        return records

    def _setup_browser_model(self):
        model = self.browser_model
        model.pattributes += ('irradiation_enabled', 'use_focus_switching')

    def _destroy_browser_model(self):
        pass

    def _activate_sample_browser(self):
        # if not self._activated:
        # pass
        # self.load_projects()

        # db = self.manager.db
        # with db.session_ctx():
        #     self._load_mass_spectrometers()
        #
        # self.datasource_url = db.datasource_url
        # self._preference_binder('pychron.browsing',
        #                         ('recent_hours','graphical_filtering_max_days',
        #                          'reference_hours_padding'),
        #                         obj=self.search_criteria)
        #
        # self.load_browser_selection()
        self.browser_model.activate_sample_browser()
        # self.browser_pane.name = 'Browser/Sample'
        self._activated = True

    def _get_selected_analyses(self, **kw):
        """
        """
        ret = self.browser_model.get_selection(low_post=self.start_date, high_post=self.end_date, **kw)
        return ret

    def _get_browser_model(self):
        model = self.application.get_service('pychron.processing.tasks.browser.browser_model.BrowserModel')
        self.debug('Browser model model={}, id={}'.format(model, id(model)))
        return model

    # def _create_browser_pane(self, **kw):
    # model = self._get_browser_model()
    # self.browser_pane = BrowserPane(model=model, **kw)
    #
    #     # self.analysis_table.tabular_adapter = self.browser_pane.analysis_tabular_adapter
    #     # self.labnumber_tabular_adapter = self.browser_pane.labnumber_tabular_adapter
    #     model.labnumber_tabular_adapter = self.browser_pane.labnumber_tabular_adapter
    #     return self.browser_pane

    def _ok_ed(self):
        return self.extraction_device not in (DEFAULT_ED, 'None')

    def _set_selected_analysis(self, new):
        pass

    def _selector_dclick(self, item):
        pass

    def _graphical_filter_hook(self, ans, is_append):
        pass

    def _recall_item(self, item, open_copy=False):
        self.recall(item, open_copy=open_copy)

    def _open_recall_editors(self, ans):
        existing = [e.basename for e in self.get_recall_editors()]
        if ans:
            for rec in ans:
                av = rec.analysis_view
                mv = av.main_view
                # mv.isotope_adapter = self.isotope_adapter
                # mv.intermediate_adapter = self.intermediate_adapter
                # mv.show_intermediate = self.recall_configurer.show_intermediate

                # self.recall_configurer.set_fonts(av)

                editor = RecallEditor(model=rec)
                # editor.set_items(rec)
                if existing and editor.basename in existing:
                    editor.instance_id = existing.count(editor.basename)

                try:
                    self.editor_area.add_editor(editor)
                except AttributeError:
                    pass
        else:
            self.warning('could not load records')

    def get_recall_editors(self):
        es = self.editor_area.editors
        return [e for e in es if isinstance(e, RecallEditor)]

    @on_trait_change('browser_model:[analysis_table:context_menu_event, time_view_model:context_menu_event]')
    def _handle_analysis_table_context_menu(self, new):
        if new:
            sel = self.browser_model.analysis_table.selected

            action, modifiers = new
            # if action in ('append', 'replace'):
            #     self._append_replace_unknowns(action == 'append')
            if action == 'open':
                if sel:
                    open_copy = False
                    if modifiers:
                        open_copy = modifiers.get('open_copy')

                    for it in sel:
                        self._recall_item(it, open_copy=open_copy)
            elif action == 'find_refs':
                if sel:
                    self._find_refs(sel[-1])

    @on_trait_change('browser_model:[analysis_table:dclicked]')
    def _handle_dclicked(self, new):
        self._recall_item(new.item)

    # @on_trait_change('analysis_table:selected')
    # def _selected_analysis_changed(self, new):
    #     print 'asdf', new
    #     self._set_selected_analysis(new)

    @on_trait_change('browser_model:dclicked_sample')
    def _dclicked_sample_changed(self):
        self._dclicked_sample_hook()

        if self.active_editor:
            ans = self.browser_model.analysis_table.analyses
            self.active_editor.set_items(ans)

    def _dclicked_sample_hook(self):
        pass

    # ============= EOF =============================================
    # def load_irradiation(self):
    # if self.use_workspace:
    #         obj = self.workspace.index_db
    #     else:
    #         obj = self.manager
    #
    #     self.irradiations = irs = obj.irradiations
    #     if irs:
    #         self.irradiation = irs[0]
    #         self.levels = ls = obj.levels
    #         if ls:
    #             self.level = ls[0]
    # def _get_analysis_series(self, lp, hp, ms):
    #     self.use_low_post = True
    #     self._set_low_post(lp)
    #     self.use_high_post = True
    #     self._set_high_post(hp)
    #
    #     ans = self._retrieve_analyses(low_post=lp,
    #                                   high_post=hp,
    #                                   mass_spectrometers=ms)
    #     return ans

    # def _get_manager(self):
    #     if self.use_workspace:
    #         obj = self.workspace.index_db
    #     else:
    #         obj = self.manager
    #     return obj

    # def _load_projects_for_irradiation(self):
    #     ms = None
    #     if self.use_mass_spectrometers:
    #         ms = self.mass_spectrometer_includes
    #
    #     if self.irradiation:
    #         db = self.db
    #         with db.session_ctx():
    #             ps = db.get_projects(irradiation=self.irradiation,
    #                                  level=self.level,
    #                                  mass_spectrometers=ms)
    #
    #             ps = self._make_project_records(ps, include_recent_first=True)
    #             self.projects = ps

    # def _load_projects_and_irradiations(self):
    #     ms = None
    #     if self.use_mass_spectrometers:
    #         ms = self.mass_spectrometer_includes
    #
    #     db = self.db
    #     with db.session_ctx():
    #         ps = db.get_projects(mass_spectrometers=ms)
    #         ps = self._make_project_records(ps,
    #                                         ms, include_recent_first=True)
    #         self.projects = ps
    #         sp = []
    #         for si in self.selected_projects:
    #             cp = next((p for p in ps if p.name == si), None)
    #             if cp:
    #                 sp.append(cp)
    #
    #         self.selected_projects = sp
    #         irs = db.get_irradiations(mass_spectrometers=ms)
    #         self.irradiations = [i.name for i in irs]

    # def _activate_query_browser(self):
    #     psel = self.data_selector
    #     selector = self.data_selector.selector
    #     selector.queries = []
    #
    #     if self.project_enabled and self.selected_projects:
    #         for i, si in enumerate(self.selected_projects):
    #             selector.add_query('Project', '=', si.name, chain_rule='Or' if i > 0 else '')
    #
    #     if self.use_analysis_type_filtering and self.analysis_include_types:
    #         for at in self.analysis_include_types:
    #             selector.add_query('Analysis Type', '=', at, chain_rule='Or')
    #
    #     if self.use_low_post:
    #         selector.add_query('Run Date/Time', '>', self.low_post.strftime('%m/%d/%Y %H:%M:%S'))
    #     if self.use_high_post:
    #         selector.add_query('Run Date/Time', '<', self.high_post.strftime('%m/%d/%Y %H:%M:%S'))
    #
    #     if not selector.queries:
    #         if not psel.active:
    #             selector.load_recent()
    #     else:
    #         selector.execute_query()
    #
    #     psel.active = True
    #     self.browser_pane.name = 'Browser/Query'
    # @on_trait_change('analysis_table:omit_invalid')
    # def _omit_invalid_changed(self):
    # self._selected_samples_changed(self.selected_samples)

    # def _selected_projects_change_hook(self, names):
    #     if not self._top_level_filter:
    #         self._top_level_filter = 'project'
    #     if names:
    #         if self._top_level_filter == 'project':
    #             db = self.db
    #             with db.session_ctx():
    #                 irrads = db.get_irradiations(project_names=names)
    #                 self.irradiations = [i.name for i in irrads]

    # def _retrieve_labnumbers_hook(self, db):
    #     low_post = self.low_post
    #     high_post = self.high_post
    #     ms = None
    #     if self.use_mass_spectrometers:
    #         ms = self.mass_spectrometer_includes
    #
    #     def get_labnumbers(ids=None):
    #         return db.get_labnumbers(identifiers=ids,
    #                                  low_post=low_post,
    #                                  high_post=high_post,
    #                                  mass_spectrometers=ms,
    #                                  filter_non_run=self.filter_non_run_samples)
    #
    #     def atypes_func(obj, func):
    #         func = getattr(man, func)
    #         refs, unks = func(obj)
    #         nls = []
    #         if 'monitors' in atypes:
    #             nls.extend(refs)
    #         if 'unknown' in atypes:
    #             nls.extend(unks)
    #         return nls
    #
    #     man = self.manager
    #     ls = []
    #     atypes = self.analysis_include_types if self.use_analysis_type_filtering else None
    #
    #     if self.project_enabled:
    #         if not self.irradiation_enabled:
    #             ls = super(BaseBrowserTask, self)._retrieve_labnumbers_hook(db)
    #         else:
    #             if self.selected_projects and self.irradiation_enabled and self.irradiation:
    #                 ls = db.get_project_irradiation_labnumbers([si.name for si in self.selected_projects],
    #                                                            self.irradiation,
    #                                                            self.level,
    #                                                            low_post=low_post,
    #                                                            high_post=high_post,
    #                                                            mass_spectrometers=ms,
    #                                                            filter_non_run=self.filter_non_run_samples,
    #                                                            analysis_types=atypes)
    #                 if atypes:
    #                     ls = atypes_func(ls)
    #
    #     elif self.irradiation_enabled and self.irradiation:
    #         if not self.level:
    #             ls = db.get_irradiation_labnumbers(self.irradiation, self.level,
    #                                                low_post=low_post,
    #                                                high_post=high_post,
    #                                                mass_spectrometers=ms,
    #                                                filter_non_run=self.filter_non_run_samples,
    #                                                analysis_types=atypes)
    #         else:
    #             # level = man.get_level(self.level)
    #             level = db.get_irradiation_level(self.irradiation,
    #                                              self.level)
    #             if level:
    #                 if atypes:
    #                     xs = atypes_func(level, 'group_level')
    #                 else:
    #                     xs = [p.labnumber for p in level.positions]
    #
    #                 if xs:
    #                     lns = [x.identifier for x in xs]
    #                     ls = get_labnumbers(ids=lns)
    #
    #     elif low_post or high_post:
    #         ls = get_labnumbers()
    #         ans = db.get_analyses_date_range(low_post, high_post, mass_spectrometers=ms)
    #         ans = self._make_records(ans)
    #         self.analysis_table.set_analyses(ans)
    #
    #     return ls
    #
    # def _identifier_change_hook(self, db, new, lns):
    #     if len(new) > 2:
    #         if self.project_enabled:
    #             def get_projects():
    #                 for li in lns:
    #                     try:
    #                         yield li.sample.project
    #                     except AttributeError, e:
        # print 'exception', e
    #
    #             ps = sorted(list(set(get_projects())))
    #             ps = [ProjectRecordView(p) for p in ps]
    #             self.projects = ps
    #             self.selected_projects = []
    #
    #         if self.irradiation_enabled:
    #             def get_irradiations():
    #                 for li in lns:
    #                     try:
    #                         yield li.irradiation_position.level.irradiation.name
    #                     except AttributeError:
    #                         pass
    #
    #             irrads = sorted(list(set(get_irradiations())))
    #             self.irradiations = irrads
    #             if irrads:
    #                 self.irradiation = irrads[0]

    # handlers
    # def _filter_by_button_fired(self):
    #     self.debug('filter by button fired low_post={}, high_post={}'.format(self.low_post, self.high_post))
    #     if self.sample_view_active:
    #         self._filter_by_hook()
    #     else:
    #         self.data_selector.execute_query()

    # def _toggle_focus_fired(self):
    #     self.filter_focus = not self.filter_focus
    #
    # def _toggle_view_fired(self):
    #     self.sample_view_active = not self.sample_view_active
    #     if not self.sample_view_active:
    #         self._activate_query_browser()
    #     else:
    #         self._activate_sample_browser()
    #
    #     self.dump()

    # def _graphical_filter_button_fired(self):
    #     print 'ffffassdf'
    #     self.debug('doing graphical filter')
    #     from pychron.processing.tasks.browser.graphical_filter import GraphicalFilterModel, GraphicalFilterView
    #
    #     sams = self.selected_samples
    #     if not sams:
    #         sams = self.samples
    #
    #     db = self.db
    #     with db.session_ctx():
    #         if sams:
    #             lns = [si.identifier for si in sams]
    #             lpost, hpost = db.get_min_max_analysis_timestamp(lns)
    #             ams = ms = db.get_analysis_mass_spectrometers(lns)
    #             force = False
    #         else:
    #             force = True
    #             lpost = datetime.now() - timedelta(hours=self.search_criteria.recent_hours)
    #             hpost = datetime.now()
    #             ams = [mi.name for mi in db.get_mass_spectrometers()]
    #             ms = ams[:1]
    #
    #         # if date range > X days make user fine tune range
    #         tdays = 3600 * 24 * max(1, self.search_criteria.graphical_filtering_max_days)
    #
    #         if force or (hpost - lpost).total_seconds() > tdays or len(ms) > 1:
    #             d = GraphicalFilterSelector(lpost=lpost, hpost=hpost,
    #                                         available_mass_spectrometers=ams,
    #                                         mass_spectrometers=ms)
    #             info = d.edit_traits(kind='livemodal')
    #             if info.result:
    #                 lpost, hpost, ms = d.lpost, d.hpost, d.mass_spectrometers
    #                 if not ms:
    #                     self.warning_dialog('Please select at least one Mass Spectrometer')
    #                     return
    #             else:
    #                 return
    #
    #         ans = db.get_date_range_analyses(lpost, hpost, ordering='asc', spectrometer=ms)
    #
    #         def func(xi, prog, i, n):
    #             if prog:
    #                 prog.change_message('Loading {}-{}. {}'.format(i, n, xi.record_id))
    #             return GraphicalRecordView(xi)
    #
    #         ans = progress_loader(ans, func)
    #         if not ans:
    #             return
    #
    #     gm = GraphicalFilterModel(analyses=ans,
    #                               projects=[p.name for p in self.selected_projects])
    #     gm.setup()
    #     gv = GraphicalFilterView(model=gm)
    #     info = gv.edit_traits(kind='livemodal')
    #     if info.result:
    #         ans = gm.get_selection()
    #         self.analysis_table.analyses = ans
    #         self._graphical_filter_hook(ans, gm.is_append)

    # def _use_mass_spectrometer_changed(self, new):
    #     if new:
    #         self.refresh_samples()
    #         self._load_projects_and_irradiations()
    #
    # def _mass_spectrometer_includes_changed(self):
    #     if self.mass_spectrometer_includes:
    #         if self.identifier:
    #             self._identifier_changed(self.identifier)
    #             return
    #
    #         self.refresh_samples()
    #
    #     self._load_projects_and_irradiations()

    # def _irradiation_enabled_changed(self, new):
    #     if not new:
    #         self._top_level_filter = None
    #         self.projects = self.oprojects
    #     else:
    #         self._load_projects_for_irradiation()
    #
    # def _project_enabled_changed(self, new):
    #     if not new:
    #         self._top_level_filter = None
    #         obj = self._get_manager()
    #         self.irradiations = obj.irradiations
    #
    # @on_trait_change('irradiation,level')
    # def _handle_irradiation_change(self, name, new):
    #     obj = self._get_manager()
    #     setattr(obj, name, new)
    #
    #     if not self._top_level_filter:
    #         self._top_level_filter = 'irradiation'
    #
    #     if self._top_level_filter == 'irradiation':
    #         self._load_projects_for_irradiation()
    #
    #     if name == 'irradiation':
    #         self.levels = obj.levels
    #     elif name == 'level':
    #         self.set_samples(self._retrieve_labnumbers())
    #
    # def _use_analysis_type_filtering_changed(self):
    #     self.refresh_samples()
    #
    # def _level_changed(self):
    #     if self.update_on_level_change:
    #         self.refresh_samples()
    #
    # def __analysis_include_types_changed(self, new):
    #     if new:
    #         if self.selected_projects:
    #             self._filter_by_button_fired()
    #         else:
    #             self.refresh_samples()
    #     else:
    #         self.samples = []

    # def _project_date_bins(self, identifier):
    #     db = self.db
    #     hours = self.search_criteria.reference_hours_padding
    #     with db.session_ctx():
    #         for pp in self.selected_projects:
    #             bins = db.get_project_date_bins(identifier, pp.name, hours)
    #             print bins
    #             if bins:
    #                 for li, hi in bins:
    #                     yield li, hi

    # def _selected_samples_changed(self, new):
    #     if new:
    #         at = self.analysis_table
    #         lim = at.limit
    #         kw = dict(limit=lim,
    #                   include_invalid=not at.omit_invalid,
    #                   mass_spectrometers=self._recent_mass_spectrometers)
    #
    #         ss = self.selected_samples
    #         xx = ss[:]
    #         # if not any(['RECENT' in p for p in self.selected_projects]):
    #         # sp=self.selected_projects
    #         # if not hasattr(sp, '__iter__'):
    #         #     sp = (sp, )
    #
    #         if not any(['RECENT' in p.name for p in self.selected_projects]):
    #             reftypes = ('blank_unknown',)
    #             if any((si.analysis_type in reftypes
    #                     for si in ss)):
    #                 with self.db.session_ctx():
    #                     ans = []
    #                     for si in ss:
    #                         if si.analysis_type in reftypes:
    #                             xx.remove(si)
    #                             dates = list(self._project_date_bins(si.identifier))
    #                             print dates
    #                             progress = open_progress(len(dates))
    #                             for lp, hp in dates:
    #
    #                                 progress.change_message('Loading Date Range '
    #                                                         '{} to {}'.format(lp.strftime('%m-%d-%Y %H:%M:%S'),
    #                                                                           hp.strftime('%m-%d-%Y %H:%M:%S')))
    #                                 ais = self._retrieve_sample_analyses([si],
    #                                                                      make_records=False,
    #                                                                      low_post=lp,
    #                                                                      high_post=hp, **kw)
    #                                 ans.extend(ais)
    #                             progress.close()
    #
    #                     ans = self._make_records(ans)
    #                 # print len(ans), len(set([si.record_id for si in ans]))
    #         if xx:
    #             lp, hp = self.low_post, self.high_post
    #             ans = self._retrieve_sample_analyses(xx,
    #                                                  low_post=lp,
    #                                                  high_post=hp,
    #                                                  **kw)
    #             self.debug('selected samples changed. loading analyses. '
    #                        'low={}, high={}, limit={}'.format(lp, hp, lim))
    #
    #         self.analysis_table.set_analyses(ans)
    #         self.dump_browser()
    #
    #     self.filter_focus = not bool(new)

    # @on_trait_change('data_selector:database_selector:dclicked')
    # def _handle_selector_dclick(self, new):
    #     self._selector_dclick(new.item)

    # def _analysis_table_default(self):
    #     at = AnalysisTable(db=self.manager.db,
    #                        append_replace_enabled=self._append_replace_analyses_enabled)
    #     return at

    # def _data_selector_default(self):
    #     return DataSelector(database_selector=self.manager.db.selector)

    # def refresh_samples(self):
    # self.debug('refresh samples')
    # self.set_samples(self._retrieve_labnumbers())

    # def load_time_view(self):
    #     self.debug('load time view')
    #     db = self.db
    #     with db.session_ctx():
    #         ss = [si.labnumber for si in self.selected_samples]
    #         bt = self.search_criteria.reference_hours_padding
    #         if not bt:
    #             self.information_dialog('Set "References Window" in Preferences defaulting to 2hrs')
    #             bt = 2
    #
    #         ts = db.get_analysis_date_ranges(ss, bt * 3600)
    #         ms = db.get_labnumber_mass_spectrometers(ss)
    #         n = len(ts)
    #         if n > 1:
    #             if not self.confirmation_dialog('The date range you selected is to large. It will be '
    #                                             'broken into {} subranges.\nDo you want to Continue?'.format(n)):
    #                 return
    #
    #             xx = []
    #             for lp, hp in ts:
    #                 pad = get_pad(lp, hp)
    #                 if not pad:
    #                     break
    #                 ans = self._get_analysis_series(pad.low_post, pad.high_post, ms)
    #                 xx.extend(ans)
    #         else:
    #             lp, hp = db.get_min_max_analysis_timestamp(ss)
    #             pad = get_pad(lp, hp)
    #             if not pad:
    #                 return
    #             xx = self._get_analysis_series(pad.low_post, pad.high_post, ms)
    #
    #         self.analysis_table.set_analyses(xx)
