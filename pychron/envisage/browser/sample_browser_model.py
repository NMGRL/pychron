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
import re

from apptools.preferences.preference_binding import bind_preference
from traits.api import Button, Instance

from pychron.dvc.func import get_review_status
from pychron.envisage.browser.analysis_table import AnalysisTable
from pychron.envisage.browser.browser_model import BrowserModel
from pychron.envisage.browser.find_references_config import FindReferencesConfigModel, FindReferencesConfigView
from pychron.envisage.browser.time_view import TimeViewModel
from pychron.envisage.browser.util import get_pad

NCHARS = 60
REG = re.compile(r'.' * NCHARS)


class SampleBrowserModel(BrowserModel):
    graphical_filter_button = Button
    find_references_button = Button
    toggle_view = Button

    add_analysis_group_button = Button
    analysis_table = Instance(AnalysisTable)
    time_view_model = Instance(TimeViewModel)

    def __init__(self, *args, **kw):
        super(SampleBrowserModel, self).__init__(*args, **kw)
        prefid = 'pychron.browser'
        bind_preference(self.search_criteria, 'recent_hours',
                        '{}.recent_hours'.format(prefid))
        bind_preference(self.search_criteria, 'reference_hours_padding',
                        '{}.reference_hours_padding'.format(prefid))

        # self._preference_binder('pychron.browsing',
        # ('recent_hours','graphical_filtering_max_days',
        # 'reference_hours_padding'),
        # obj=self.search_criteria)

    # def drop_factory(self, item):
    #     print 'dropadfs', item
    #     return item
    def dump_browser(self):
        super(SampleBrowserModel, self).dump_browser()
        self.analysis_table.dump()

    def activated(self, force=False):
        self.analysis_table.load()

        if not self.is_activated or force:
            self.load_browser_options()
            if self.sample_view_active:
                self.activate_browser(force)
                # self.filter_focus = True
                self.is_activated = True
            else:
                self.time_view_model.load()

            self._top_level_filter = None

    def load_review_status(self):
        at = self.analysis_table
        records = self.get_analysis_records()
        if records:
            for ri in records:
                get_review_status(ri)
            at.refresh_needed = True

    def get_analysis_records(self):
        records = self.analysis_table.selected
        if not records:
            records = self.analysis_table.analyses

        return records

    def get_selection(self, low_post, high_post, unks=None, selection=None, make_records=True):
        ret = None
        if selection is None:
            if self.analysis_table.selected:
                ret = self.analysis_table.selected
            elif self.time_view_model.selected:
                ret = self.time_view_model.selected
            else:
                selection = self.selected_samples

        if selection:
            iv = not self.analysis_table.omit_invalid
            uuids = [x.uuid for x in unks] if unks else None
            ret = [ai for ai in self.retrieve_sample_analyses(selection,
                                                              exclude_uuids=uuids,
                                                              include_invalid=iv,
                                                              low_post=low_post,
                                                              high_post=high_post,
                                                              make_records=make_records)]
        return ret

    def retrieve_sample_analyses(self, *args, **kw):
        return self._retrieve_sample_analyses(*args, **kw)

    def load_chrono_view(self):
        self.debug('load time view')
        db = self.db

        ss = [si.labnumber for si in self.selected_samples]
        bt = self.search_criteria.reference_hours_padding
        if not bt:
            self.information_dialog('Set "References Window" in Preferences defaulting to 2hrs')
            bt = 2

        # ss  = ['bu-FD-O']
        ts = db.get_analysis_date_ranges(ss, bt)
        if any((vi.name.startswith('RECENT ') for vi in self.selected_projects)):
            ts = ts[-1:]

        ms = db.get_labnumber_mass_spectrometers(ss)
        n = len(ts)
        if n > 1:
            if not self.confirmation_dialog('The date range you selected is to large. It will be '
                                            'broken into {} subranges.\nDo you want to Continue?'.format(n)):
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

        self.analysis_table.set_analyses(xx)

    def dump(self):
        self.time_view_model.dump_filter()
        self.analysis_table.dump()
        super(SampleBrowserModel, self).dump()

    def add_analysis_set(self):
        self.analysis_table.add_analysis_set()

    # handlers
    def _add_analysis_group_button_fired(self):
        ans = self.analysis_table.get_selected_analyses()
        if ans:
            from pychron.envisage.browser.add_analysis_group_view import AddAnalysisGroupView
            a = AddAnalysisGroupView(projects=[p.name for p in self.projects])
            if self.selected_projects:
                a.project = self.selected_projects[0].name

            info = a.edit_traits(kind='livemodal')
            if info.result:
                self.db.add_analysis_group(a.name, a.project, ans)

    def _analysis_set_changed(self, new):
        if self.analysis_table.suppress_load_analysis_set:
            return

        self.debug('analysis set changed={}'.format(new))
        ans = self.analysis_table.get_analysis_set(new)
        ans = self.db.get_analyses_uuid([a[0] for a in ans])
        xx = self._make_records(ans)
        self.analysis_table.set_analyses(xx)

    def _find_references_button_fired(self):
        self.debug('find references button fired')
        if self.sample_view_active:
            self._find_references_hook()

    def _toggle_view_fired(self):
        self.sample_view_active = not self.sample_view_active
        if not self.sample_view_active:
            self.time_view_model.load()
        else:
            self.activate_browser()

        self.dump()

    def _selected_samples_changed_hook(self, new):
        self.analysis_table.selected = []

        ans = []
        if new:
            at = self.analysis_table
            lim = at.limit

            uuids = [ai.uuid for ai in self.analysis_table.analyses]

            kw = dict(limit=lim,
                      include_invalid=not at.omit_invalid,
                      mass_spectrometers=self._recent_mass_spectrometers,
                      exclude_uuids=uuids,
                      # repositories=[e.name for e in self.selected_repositories] if self.selected_repositories else None
                      )

            lp, hp = self.low_post, self.high_post
            ans = self._retrieve_sample_analyses(new,
                                                 low_post=lp,
                                                 high_post=hp,
                                                 **kw)

            self.debug('selected samples changed. loading analyses. '
                       'low={}, high={}, limit={} n={}'.format(lp, hp, lim, len(ans)))

        self.analysis_table.set_analyses(ans, selected_identifiers={ai.identifier for ai in new})

    # private
    def _find_references_hook(self):
        ans = self.analysis_table.analyses
        ms = list({a.mass_spectrometer for a in ans})

        m = FindReferencesConfigModel(mass_spectrometers=ms[:],
                                      available_mass_spectrometers=ms)
        v = FindReferencesConfigView(model=m)
        info = v.edit_traits()
        if info.result:
            if not m.mass_spectrometers:
                self.warning_dialog('No Mass Spectrometer selected. Cannot find references. Select one or more Mass '
                                    'Spectrometers from the "Configure Find References" window')
                return

            atypes = m.formatted_analysis_types
            refs = self.db.find_references(ans, atypes,
                                           mass_spectrometer=m.mass_spectrometers,
                                           hours=m.threshold, make_records=False)
            if refs:
                self.analysis_table.add_analyses(refs)
            else:
                atypes=','.join(atypes)
                ms = ','.join(m.mass_spectrometers)
                self.warning_dialog('No References found.\n\n'
                                    'Analysis Types: {}\n'
                                    'Mass Spectrometers: {}'.format(atypes,ms))

    def _project_date_bins(self, identifier):
        db = self.db
        hours = self.search_criteria.reference_hours_padding
        for pp in self.selected_projects:
            bins = db.get_project_date_bins(identifier, pp.name, hours)
            print bins
            if bins:
                for li, hi in bins:
                    yield li, hi

    def _get_analysis_series(self, lp, hp, ms):
        self.use_low_post = True
        self._set_low_post(lp)
        self.use_high_post = True
        self._set_high_post(hp)
        ans = self._retrieve_analyses(low_post=lp,
                                      high_post=hp,
                                      order='desc',
                                      mass_spectrometers=ms)
        return ans

    def _selected_projects_change_hook(self, names):

        self.selected_samples = []
        self.analysis_table.analyses = []

        if not self._top_level_filter:
            self._top_level_filter = 'project'

        if names:
            if self._top_level_filter == 'project':
                db = self.db
                irrads = db.get_irradiations(project_names=names)
                self.irradiations = [i.name for i in irrads]

    def _time_view_model_default(self):
        return TimeViewModel(db=self.db)

    def _analysis_table_default(self):
        at = AnalysisTable()
        at.load()
        at.on_trait_change(self._analysis_set_changed, 'analysis_set')
        bind_preference(at, 'max_history', 'pychron.browser.max_history')
        return at

# ============= EOF =============================================
