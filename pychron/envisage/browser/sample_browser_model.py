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

from datetime import datetime, timedelta
from operator import attrgetter

import sqlalchemy.orm.exc

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import Str

from pychron.envisage.browser.analysis_browser_model import AnalysisBrowserModel
from pychron.envisage.browser.find_references_config import (
    FindReferencesConfigModel,
    FindReferencesConfigView,
)
from pychron.envisage.browser.util import get_pad
from pychron.envisage.browser.view import SampleBrowserView


class SampleBrowserModel(AnalysisBrowserModel):
    # time_view_model = Instance(TimeViewModel)
    monitor_sample_name = Str

    def __init__(self, *args, **kw):
        super(SampleBrowserModel, self).__init__(*args, **kw)
        prefid = "pychron.browser"
        bind_preference(
            self.search_criteria,
            "reference_hours_padding",
            "{}.reference_hours_padding".format(prefid),
        )

        bind_preference(self, "monitor_sample_name", "pychron.entry.monitor_name")

    def reattach(self):
        self.debug("reattach")

        try:
            ans = sorted(self.table.oanalyses, key=attrgetter("uuid"))
            uuids = [ai.uuid for ai in ans]
            nans = self.db.get_analyses_uuid(uuids)

            for ni, ai in zip(nans, ans):
                ai.dbrecord = ni

            if self.selected_projects:
                self._load_associated_groups(self.selected_projects)
        except sqlalchemy.orm.exc.DetachedInstanceError:
            self.warning_dialog(
                "There is an issue with pychron's connection to the database. "
                "Please restart pychron and try again"
            )
            self.application.stop()

    def dump_browser(self):
        super(SampleBrowserModel, self).dump_browser()
        self.table.dump()

    def activated(self, force=False):
        self.reattach()
        self.table.load()

        if not self.is_activated or force:
            self.load_browser_options()
            if self.sample_view_active:
                self.activate_browser(force)
                # self.filter_focus = True
                self.is_activated = True
            # else:
            #     self.time_view_model.load()

            self._top_level_filter = None

    def load_review_status(self):
        self.table.load_review_status()

    def get_analysis_records(self):
        # if not self.sample_view_active:
        #     return self.time_view_model.get_analysis_records()
        # else:
        #     return self.table.get_analysis_records()
        return self.table.get_analysis_records()

    def get_selection(
        self, low_post, high_post, unks=None, selection=None, make_records=True
    ):
        ret = None
        if selection is None:
            if self.table.selected:
                ret = self.table.selected
            # elif self.time_view_model.selected:
            #     ret = self.time_view_model.selected
            else:
                selection = self.selected_samples

        if selection:
            iv = not self.table.omit_invalid
            uuids = [x.uuid for x in unks] if unks else None
            ret = [
                ai
                for ai in self._retrieve_analyses(
                    samples=selection,
                    exclude_uuids=uuids,
                    include_invalid=iv,
                    low_post=low_post,
                    high_post=high_post,
                    make_records=make_records,
                )
            ]
        return ret

    def load_chrono_view(self):
        self.debug("load time view")
        db = self.db

        ss = [si.labnumber for si in self.selected_samples]
        bt = self.search_criteria.reference_hours_padding
        if not bt:
            self.information_dialog(
                'Set "References Window" in Preferences.\n\nDefaulting to 2hrs'
            )
            bt = 2

        # ss  = ['bu-FD-O']
        ts = db.get_analysis_date_ranges(ss, bt)
        # if any((vi.name.startswith('RECENT ') for vi in self.selected_projects)):
        #     ts = ts[-1:]

        if self.mass_spectrometers_enabled:
            ms = self.mass_spectrometer_includes
        else:
            ms = db.get_labnumber_mass_spectrometers(ss)

        n = len(ts)
        if n > 1:
            if not self.confirmation_dialog(
                "The date range you selected is to large. It will be "
                "broken into {} subranges.\nDo you want to Continue?".format(n)
            ):
                return

            xx = []
            for lp, hp in ts:
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

        self.table.set_analyses(xx)

    def delete_analysis_group(self):
        self.debug("delete analysis groups")
        n = len(self.selected_analysis_groups)
        for i, g in enumerate(self.selected_analysis_groups):
            self.debug("deleting analysis group. {}".format(g))
            self.db.delete_analysis_group(g, commit=i == n - 1)
            self.analysis_groups.remove(g)

    def add_analysis_group(self, ans):
        from pychron.envisage.browser.add_analysis_group_view import (
            AddAnalysisGroupView,
        )

        # a = AddAnalysisGroupView(projects={'{:05n}:{}'.format(i, p.name): p for i, p in enumerate(self.projects)})
        projects = self.db.get_projects(order="asc")
        projects = self._make_project_records(projects, include_recent=False)
        agv = AddAnalysisGroupView(
            db=self.db,
            projects={p: "{:05n}:{}".format(i, p.name) for i, p in enumerate(projects)},
        )

        project, pp = tuple({(a.project, a.principal_investigator) for a in ans})[0]
        try:
            project = next(
                (
                    p
                    for p in projects
                    if p.name == project and p.principal_investigator == pp
                )
            )
            agv.project = project
        except StopIteration:
            pass

        info = agv.edit_traits(kind="livemodal")
        if info.result:
            if agv.save(ans, self.db):
                self.load_associated_groups(projects)

    def set_tags(self, tagname):
        items = self.get_analysis_records()
        if items:
            self.dvc.tag_items(tagname, items)
        return items

    # handlers
    # def _toggle_view_fired(self):
    #     self.debug('toggle view fired')
    #     self.sample_view_active = not self.sample_view_active
    #     if not self.sample_view_active:
    #         self.time_view_model.load()
    #     else:
    #         self.activate_browser()
    #
    #     self.dump()

    def _selected_samples_changed_hook(self, new):
        self.table.selected = []

        ans = []
        if new:
            at = self.table
            lim = at.limit

            uuids = [ai.uuid for ai in self.table.analyses]

            kw = dict(
                limit=lim, include_invalid=not at.omit_invalid, exclude_uuids=uuids
            )

            lp = self.low_post  # if self.use_low_post else None
            hp = self.high_post  # if self.use_high_post else None

            ls = None
            if self.load_enabled and self.selected_loads:
                ls = [l.name for l in self.selected_loads]

            ans = self._retrieve_analyses(
                samples=new, loads=ls, low_post=lp, high_post=hp, **kw
            )

            self.debug(
                "selected samples changed. loading analyses. "
                "low={}, high={}, limit={} n={}".format(lp, hp, lim, len(ans))
            )

        self.table.set_analyses(ans, selected_identifiers={ai.identifier for ai in new})

    # private
    def _load_recent(self):
        from pychron.envisage.browser.recent_view import RecentView

        if not self.available_mass_spectrometers:
            self._load_mass_spectrometers()

        v = RecentView(
            available_mass_spectrometers=self.available_mass_spectrometers,
            use_mass_spectrometers=len(self.available_analysis_types) > 1,
        )
        v.load()
        info = v.edit_traits()
        if info.result:
            v.dump()
            now = datetime.now()
            lp = now - timedelta(hours=v.nhours)
            ls = self.db.get_labnumbers(
                mass_spectrometers=(
                    v.mass_spectrometers if v.use_mass_spectrometers else None
                ),
                analysis_types=v.analysis_types,
                high_post=now,
                low_post=lp,
                filter_non_run=self.filter_non_run_samples,
            )
            if ls:
                sams = self._load_sample_record_views(ls)

                self.samples = sams
                self.osamples = sams

                xx = self._get_analysis_series(
                    lp, now, v.mass_spectrometers, analysis_types=v.analysis_types
                )
                self.table.set_analyses(xx)
            else:
                self.samples = []
                self.osamples = []
                self.table.clear()

    def _find_references_hook(self):
        ans = self.table.analyses
        ms = list({a.mass_spectrometer.lower() for a in ans if a.mass_spectrometer})
        es = list({a.extract_device.lower() for a in ans if a.extract_device})
        irs = list(
            {"{},{}".format(a.irradiation, a.irradiation_level.upper()) for a in ans}
        )

        samples = []
        for il in irs:
            i, l = il.split(",")
            ns = self.dvc.distinct_sample_names(i, l)
            samples.extend(ns)

        m = FindReferencesConfigModel(
            mass_spectrometers=ms[:],
            available_mass_spectrometers=ms,
            extract_devices=es[:],
            available_extract_devices=es,
            monitor_samples=list(set(samples)),
            available_irradiations=irs,
        )

        v = FindReferencesConfigView(model=m)
        info = v.edit_traits()
        if info.result:
            if not m.mass_spectrometers:
                self.warning_dialog(
                    "No Mass Spectrometer selected. Cannot find references. Select one or more Mass "
                    'Spectrometers from the "Configure Find References" window'
                )
                return
            if m.replace:
                self.table.clear()

            atypes = m.formatted_analysis_types
            if atypes:
                refs = self.db.find_references(
                    ans,
                    atypes,
                    extract_devices=m.extract_devices,
                    mass_spectrometers=m.mass_spectrometers,
                    hours=m.threshold,
                    make_records=False,
                )
                if refs:
                    self.table.add_analyses(refs)
                else:
                    atypes = ",".join(atypes)
                    ms = ",".join(m.mass_spectrometers)
                    self.warning_dialog(
                        "No References found.\n\n"
                        "Analysis Types: {}\n"
                        "Mass Spectrometers: {}".format(atypes, ms)
                    )

            for irstr in m.irradiations:
                i, l = irstr.split(",")
                r = self.db.get_flux_monitor_analyses(i, l, m.monitor_sample)
                if r:
                    self.table.add_analyses(r)

                if atypes:
                    refs = self.db.find_references(
                        r,
                        atypes,
                        extract_devices=m.extract_devices,
                        mass_spectrometers=m.mass_spectrometers,
                        hours=m.threshold,
                        make_records=False,
                    )
                    if refs:
                        self.table.add_analyses(refs)

    def _project_date_bins(self, identifier):
        db = self.db
        hours = self.search_criteria.reference_hours_padding
        for pp in self.selected_projects:
            bins = db.get_project_date_bins(identifier, pp.name, hours)
            print(bins)
            if bins:
                for li, hi in bins:
                    yield li, hi

    def _get_analysis_series(self, lp, hp, ms, analysis_types=None):
        self.use_low_post = True
        self._set_low_post(lp)
        self.use_high_post = True
        self._set_high_post(hp)
        ans = self._retrieve_analyses(
            low_post=lp,
            high_post=hp,
            order="desc",
            mass_spectrometers=ms,
            analysis_types=analysis_types,
        )
        return ans

    def _selected_projects_change_hook(self, names):
        self.selected_samples = []
        self.table.clear_non_frozen()
        #
        if not self._top_level_filter:
            self._top_level_filter = "project"

        if names:
            irrads = []
            if self._top_level_filter == "project":
                irrads = self.db.get_irradiations(project_names=names)
        else:
            irrads = self.db.get_irradiations()

        self.irradiations = [i.name for i in irrads]

    # def _time_view_model_default(self):
    #     return TimeViewModel(db=self.db)

    def _browser_view_default(self):
        return SampleBrowserView(model=self)


# ============= EOF =============================================
