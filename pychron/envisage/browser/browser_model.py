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
# ============= standard library imports ========================
# ============= local library imports  ==========================
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
from traits.api import String, Bool, Property, on_trait_change, Button, List, Str, Enum

from pychron.core.ui.preference_binding import bind_preference
from pychron.envisage.browser.base_browser_model import BaseBrowserModel
from pychron.envisage.browser.record_views import ProjectRecordView


class BrowserModel(BaseBrowserModel):
    filter_focus = Bool(True)
    use_focus_switching = Bool(True)
    fuzzy_search_entry = String
    execute_fuzzy_search = Button
    fuzzy_search_type = Enum("Sample", "Analysis", "Project")

    irradiation_visible = Property(depends_on="filter_focus")
    analysis_types_visible = Property(depends_on="filter_focus")
    date_visible = Property(depends_on="filter_focus")
    mass_spectrometer_visible = Property(depends_on="filter_focus")
    identifier_visible = Property(depends_on="filter_focus")
    project_visible = Property(depends_on="filter_focus")
    principal_investigator_visible = Property(depends_on="filter_focus")

    filter_by_button = Button
    toggle_focus = Button
    load_view_button = Button
    refresh_selectors_button = Button

    datasource_url = Str
    irradiation_enabled = Bool
    irradiations = List
    irradiation = Str
    levels = List
    level = Str

    update_on_level_change = True
    is_activated = False

    _top_level_filter = None

    def __init__(self, *args, **kw):
        super(BrowserModel, self).__init__(*args, **kw)

        prefid = "pychron.browser"
        bind_preference(
            self, "load_selection_enabled", "{}.load_selection_enabled".format(prefid)
        )
        bind_preference(
            self, "auto_load_database", "{}.auto_load_database".format(prefid)
        )
        bind_preference(self, "use_quick_recall", "{}.use_quick_recall".format(prefid))

    def activated(self, force=False):
        self.reattach()

        self.activate_browser(force)

    def activate_browser(self, force=False):
        db = self.db
        self.datasource_url = db.datasource_url
        self.debug(
            "activate browser autoload={} "
            "load_selection_enabled={}".format(
                self.auto_load_database, self.load_selection_enabled
            )
        )

        if not self.is_activated or force:
            if self.auto_load_database:
                self.load_selectors()

            if self.load_selection_enabled:
                self.load_browser_selection()

            self.is_activated = True

    def load_selectors(self):
        self._suppress_load_labnumbers = True
        self.load_principal_investigators()
        self.load_projects()
        self.load_repositories()
        self.load_loads()
        self._suppress_load_labnumbers = False

        self._load_projects_and_irradiations()
        self._load_mass_spectrometers()

    def refresh_samples(self):
        self.debug("refresh samples")
        self._filter_by_hook()

    def select_sample(self, idx=None, name=None):
        if idx is not None:
            sams = self.samples[idx : idx + 2]
            self.selected_samples = sams

    def select_project(self, name):
        for p in self.projects:
            if p.name == name:
                self.selected_projects = [p]
                self.project_enabled = True
                break

    # def select_repository(self, exp):
    #     for e in self.repositories:
    #         if e.name == exp:
    #             self.selected_repositories = [e]
    #             self.repository_enabled = True
    #             break

    # handlers
    def _execute_fuzzy_search_fired(self):
        self.debug("execute fuzzy search")
        if self.fuzzy_search_entry:
            if len(self.fuzzy_search_entry) < 2:
                self.warning_dialog(
                    'At least two (2) characters are required for "Search"'
                )
                return

            db = self.db
            with db.session_ctx():
                ss = []
                ps = []
                if self.fuzzy_search_type == "Project":
                    ps = db.get_fuzzy_projects(self.fuzzy_search_entry)
                elif self.fuzzy_search_type == "Sample":
                    ss, ps = db.get_fuzzy_labnumbers(
                        self.fuzzy_search_entry,
                        filter_non_run=self.filter_non_run_samples,
                    )
                elif self.fuzzy_search_type == "Analysis":
                    ans = db.get_fuzzy_analysis(self.fuzzy_search_entry)
                    self.table.set_analyses(ans)

                sams = self._load_sample_record_views(ss)
                self.samples = sams
                self.osamples = sams

                ad = self._make_project_records(ps, include_recent=False)
                self.projects = ad
                self.oprojects = ad

                # ans = None
                # if "-" in self.fuzzy_search_entry:
                #     ans = db.get_fuzzy_analysis(self.fuzzy_search_entry)
                #
                # if ans:
                #     self.table.set_analyses(ans)
                # else:
                #     ps1 = db.get_fuzzy_projects(self.fuzzy_search_entry)
                #
                #     ss, ps2 = db.get_fuzzy_labnumbers(
                #         self.fuzzy_search_entry,
                #         filter_non_run=self.filter_non_run_samples,
                #     )
                #
                #     # ss2, ps3 = db.get_fuzzy_samples(self.fuzzy_search_entry, include_projects=True)
                #     # if ss:
                #     #     ss.extend(ss2)
                #     # else:
                #     #     ss = ss2
                #
                #     sams = self._load_sample_record_views(ss)
                #
                #     ps = set(ps1 + ps2)
                #     self.osamples = sams
                #     self.samples = sams
                #
                #     ad = self._make_project_records(ps, include_recent=False)
                #     self.projects = ad
                #     self.oprojects = ad

        # self._fuzzy_search_entry_changed(self.fuzzy_search_entry)

    # def _fuzzy_search_entry_changed(self, new):

    def _irradiation_enabled_changed(self, new):
        if not new:
            self._top_level_filter = None
            self.projects = self.oprojects
        else:
            self._load_projects_for_irradiation()

    def _project_enabled_changed(self, new):
        if not new:
            self._top_level_filter = None
            self.selected_projects = []

    @on_trait_change("irradiation,level")
    def _handle_irradiation_change(self, name, new):
        # obj = self._get_manager()
        # setattr(obj, name, new)

        if not self._top_level_filter:
            self._top_level_filter = "irradiation"

        if self._top_level_filter == "irradiation":
            self._load_projects_for_irradiation()

        if name == "irradiation":
            self.levels = self.db.get_level_names(new)

        # if name == 'irradiation':
        elif name == "level":
            self._load_associated_labnumbers()

    def _use_analysis_type_filtering_changed(self):
        self.refresh_samples()

    def __analysis_include_types_changed(self, new):
        if new:
            if self.selected_projects:
                self._filter_by_button_fired()
            else:
                self.refresh_samples()
        else:
            self.samples = []

    def _use_mass_spectrometer_changed(self, new):
        if new:
            self.refresh_samples()
            self._load_projects_and_irradiations()

    def _mass_spectrometer_includes_changed(self):
        if self.mass_spectrometer_includes:
            if self.identifier:
                self._identifier_changed(self.identifier)
                return

            self.refresh_samples()

    def _filter_by_button_fired(self):
        self.debug(
            "filter by button fired low_post={}, high_post={}".format(
                self.low_post, self.high_post
            )
        )
        if self.sample_view_active:
            self._filter_by_hook()

            # def _toggle_focus_fired(self):
            # self.filter_focus = not self.filter_focus

    def _load_view_button_fired(self):
        lm = self.application.get_service(
            "pychron.loading.loading_manager.LoadingManager"
        )
        if lm:
            selection = lm.get_selection()
            if selection:
                print("load view", selection)
                # lm.trait_set(db=self.db,
                #              show_group_positions=True)
                #
                # from pychron.envisage.view_util import open_view
                # lvsm = LoadViewSelectionModel(manager=lm)
                # lvc = LoadViewController(model=lvsm)
                # info = open_view(lvc)
                # if info.result:
                #     print lvsm.selections

    def _selected_samples_changed(self, new):
        self._selected_samples_changed_hook(new)
        self.dump_browser()

    def _refresh_selectors_button_fired(self):
        self.debug("refresh selectors fired")
        if self.sample_view_active:
            self.load_selectors()

    # private
    def _selected_samples_changed_hook(self, new):
        pass

    # def _get_manager(self):
    #     if self.use_workspace:
    #         obj = self.workspace.index_db
    #     else:
    #         obj = self.manager
    #     return obj

    # def _selected_repositories_changed_hook(self, names):
    #     self.irradiations = []
    #     # get all irradiations contained within these experiments
    #     irrads = self.db.get_irradiations_by_repositories(names)
    #     if irrads:
    #         self.irradiations = [i.name for i in irrads]

    # def _selected_projects_change_hook(self, names):
    #
    #     self.selected_samples = []
    #     self.table.analyses = []
    #
    #     if not self._top_level_filter:
    #         self._top_level_filter = 'project'
    #
    #     if names:
    #         if self._top_level_filter == 'project':
    #             db = self.db
    #             with db.session_ctx():
    #                 irrads = db.get_irradiations(project_names=names)
    #                 self.irradiations = [i.name for i in irrads]

    def _retrieve_labnumbers(self):
        es = []
        ps = []
        ms = []
        ls = []
        if self.load_enabled and self.selected_loads:
            ls = [s.name for s in self.selected_loads]

        if self.mass_spectrometers_enabled:
            if self.mass_spectrometer_includes:
                ms = self.mass_spectrometer_includes

        principal_investigators = None
        if (
            self.principal_investigator_enabled
            and self.selected_principal_investigators
        ):
            principal_investigators = [
                p.name for p in self.selected_principal_investigators
            ]

        if self.project_enabled:
            if self.selected_projects:
                ps = [p.unique_id for p in self.selected_projects]

        at = self.analysis_include_types if self.use_analysis_type_filtering else None

        hp = self.high_post
        lp = self.low_post

        ats = []
        samples = None
        if at:
            for a in at:
                if a == "monitors":
                    if not self.monitor_sample_name:
                        self.warning_dialog(
                            "Please Set Monitor name in preferences. Defaulting to FC-2"
                        )
                        self.monitor_sample_name = "FC-2"

                    samples = [
                        self.monitor_sample_name,
                    ]
                else:
                    ats.append(a)

        lns = self.db.get_labnumbers(
            principal_investigators=principal_investigators,
            project_ids=ps,
            # repositories=es,
            samples=samples,
            mass_spectrometers=ms,
            irradiation=self.irradiation if self.irradiation_enabled else None,
            level=self.level if self.irradiation_enabled else None,
            analysis_types=ats,
            high_post=hp,
            low_post=lp,
            loads=ls,
            filter_non_run=self.filter_non_run_samples,
        )
        return lns

    def _identifier_change_hook(self, db, new, lns):
        if len(new) > 2:
            if self.project_enabled:

                def get_projects():
                    for li in lns:
                        try:
                            yield li.sample.project
                        except AttributeError as e:
                            print("exception", e)

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

                irrads = sorted(list(set(get_irradiations())))
                self.irradiations = irrads
                if irrads:
                    self.irradiation = irrads[0]

    def _load_projects_for_irradiation(self):
        ms = None
        if self.mass_spectrometers_enabled:
            ms = self.mass_spectrometer_includes

        if self.irradiation:
            self.debug(
                "load projects for irradiation= {}, level= {}".format(
                    self.irradiation, self.level
                )
            )

            ps = self.db.get_projects(
                irradiation=self.irradiation, level=self.level, mass_spectrometers=ms
            )

            ps = self._make_project_records(ps, include_recent_first=True)
            old_selection = [p.name for p in self.selected_projects]
            self.projects = ps
            self.selected_projects = [p for p in ps if p.name in old_selection]

    def _load_projects_and_irradiations(self):
        self.debug("load_projects_and_irradiations")
        ms = None
        if self.mass_spectrometers_enabled:
            ms = self.mass_spectrometer_includes

        db = self.db
        ps = db.get_projects(mass_spectrometers=ms)
        ps = self._make_project_records(ps, ms, include_recent_first=True)
        self.projects = ps
        sp = []
        if self.selected_projects:
            for si in self.selected_projects:
                cp = next((p for p in ps if p.name == si), None)
                if cp:
                    sp.append(cp)

        self.selected_projects = sp
        irs = db.get_irradiations(mass_spectrometers=ms)
        if irs:
            self.irradiations = [i.name for i in irs]
        else:
            self.debug("_load_projects_and_irradiations. no irradiations")

    def _load_mass_spectrometers(self):
        db = self.db
        ms = db.get_mass_spectrometers()
        if ms:
            ms = [mi.name for mi in ms]
            self.available_mass_spectrometers = ms

    def _load_analysis_types(self):
        db = self.db
        ms = [mi.name for mi in db.get_analysis_types()]
        self.analysis_types = ["Analysis Type", "None"] + ms

    def _load_extraction_devices(self):
        ms = self.db.get_extraction_device_names()
        self.extraction_devices = ["Extraction Device", "None"] + ms

    def _get_analysis_types_visible(self):
        return self._get_visible(self.use_analysis_type_filtering)

    def _get_irradiation_visible(self):
        return self._get_visible(self.irradiation_enabled)

    def _get_date_visible(self):
        return self._get_visible(
            self.use_low_post or self.use_high_post or self.use_named_date_range
        )

    def _get_mass_spectrometer_visible(self):
        return self._get_visible(self.mass_spectrometers_enabled)

    def _get_identifier_visible(self):
        return True
        # return self.filter_focus if self.use_focus_switching else True

    def _get_project_visible(self):
        return self._get_visible(self.project_enabled)

    def _get_principal_investigator_visible(self):
        return self._get_visible(self.principal_investigator_enabled)

    def _get_visible(self, default):
        return True


# ============= EOF =============================================
