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
from apptools.preferences.preference_binding import bind_preference
from traits.api import Str, Bool, Property, on_trait_change, Button, Enum, List, Instance
# ============= standard library imports ========================
from datetime import datetime, timedelta
import re
# ============= local library imports  ==========================
# from pychron.processing.tasks.browser.browser_task import NCHARS
# from pychron.database.records.isotope_record import GraphicalRecordView
from pychron.core.helpers.iterfuncs import partition
from pychron.dvc.dvc import get_review_status
from pychron.envisage.browser.base_browser_model import BaseBrowserModel, extract_mass_spectrometer_name
from pychron.envisage.browser.find_references_config import FindReferencesConfigModel, FindReferencesConfigView
from pychron.envisage.browser.record_views import ProjectRecordView
from pychron.envisage.browser.analysis_table import AnalysisTable
# from pychron.processing.tasks.browser.time_view import TimeViewModel
from pychron.envisage.browser.time_view import TimeViewModel
from pychron.envisage.browser.util import get_pad

NCHARS = 60
REG = re.compile(r'.' * NCHARS)


class BrowserModel(BaseBrowserModel):
    filter_focus = Bool(True)
    use_focus_switching = Bool(True)
    # filter_label = Property(Str, depends_on='filter_focus')

    irradiation_visible = Property(depends_on='filter_focus')
    analysis_types_visible = Property(depends_on='filter_focus')
    date_visible = Property(depends_on='filter_focus')
    mass_spectrometer_visible = Property(depends_on='filter_focus')
    identifier_visible = Property(depends_on='filter_focus')
    project_visible = Property(depends_on='filter_focus')

    filter_by_button = Button
    graphical_filter_button = Button
    find_references_button = Button
    toggle_view = Button
    toggle_focus = Button

    current_task_name = Enum('Recall', 'IsoEvo', 'Blanks', 'ICFactor', 'Ideogram', 'Spectrum')
    datasource_url = Str
    irradiation_enabled = Bool
    irradiations = List
    irradiation = Str
    irradiation_enabled = Bool
    levels = List
    level = Str
    analysis_table = Instance(AnalysisTable, ())
    time_view_model = Instance(TimeViewModel)
    update_on_level_change = True
    is_activated = False

    _top_level_filter = None

    def __init__(self, *args, **kw):
        super(BrowserModel, self).__init__(*args, **kw)
        prefid = 'pychron.browsing'
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

    def activated(self, force=False):
        if not self.is_activated or force:
            self.load_browser_options()
            if self.sample_view_active:
                self.activate_sample_browser(force)
                # self.filter_focus = True
                self.is_activated = True
            else:
                self.time_view_model.load()

            self._top_level_filter = None

    def activate_sample_browser(self, force=False):
        if not self.is_activated or force:
            self.load_projects()
            self.load_experiments()
            self._load_projects_and_irradiations()

            db = self.db
            with db.session_ctx():
                self._load_mass_spectrometers()

            self.datasource_url = db.datasource_url
            self.load_browser_selection()

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

    def refresh_samples(self):
        self.debug('refresh samples')
        self._filter_by_hook()
        # self._load_associated_labnumbers()
        # self.set_samples(self._retrieve_labnumbers())

    def retrieve_sample_analyses(self, *args, **kw):
        return self._retrieve_sample_analyses(*args, **kw)

    def load_chrono_view(self):
        self.debug('load time view')
        db = self.db
        with db.session_ctx():

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
        super(BrowserModel, self).dump()

    def select_sample(self, idx=None, name=None):
        if idx is not None:
            sams = self.samples[idx:idx + 2]
            self.selected_samples = sams

    def select_project(self, name):
        for p in self.projects:
            if p.name == name:
                self.selected_projects = [p]
                self.project_enabled = True
                break

    def select_experiment(self, exp):
        for e in self.experiments:
            if e.name == exp:
                self.selected_experiments = [e]
                self.experiment_enabled = True
                break

    # handlers
    def _irradiation_enabled_changed(self, new):
        if not new:
            self._top_level_filter = None
            print self.oprojects
            self.projects = self.oprojects
        else:
            self._load_projects_for_irradiation()

    def _project_enabled_changed(self, new):
        if not new:
            self._top_level_filter = None

            # obj = self._get_manager()
            # self.irradiations = obj.irradiations

    @on_trait_change('irradiation,level')
    def _handle_irradiation_change(self, name, new):
        # obj = self._get_manager()
        # setattr(obj, name, new)

        if not self._top_level_filter:
            self._top_level_filter = 'irradiation'

        if self._top_level_filter == 'irradiation':
            self._load_projects_for_irradiation()

        if name == 'irradiation':
            self.levels = self.db.get_level_names(new)

        # if name == 'irradiation':
        elif name == 'level':
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

            # self._load_projects_and_irradiations()

    def _find_references_button_fired(self):
        self.debug('find references button fired')
        if self.sample_view_active:
            self._find_references_hook()

    def _filter_by_button_fired(self):
        self.debug('filter by button fired low_post={}, high_post={}'.format(self.low_post, self.high_post))
        if self.sample_view_active:
            self._filter_by_hook()

            # def _toggle_focus_fired(self):
            # self.filter_focus = not self.filter_focus

    def _toggle_view_fired(self):
        self.sample_view_active = not self.sample_view_active
        if not self.sample_view_active:
            self.time_view_model.load()
        else:
            self.activate_sample_browser()

        self.dump()

    def _selected_samples_changed(self, new):
        self.analysis_table.selected = []

        ans = []
        uuids = []
        if new:
            at = self.analysis_table
            lim = at.limit

            uuids = [ai.uuid for ai in self.analysis_table.analyses]

            kw = dict(limit=lim,
                      include_invalid=not at.omit_invalid,
                      mass_spectrometers=self._recent_mass_spectrometers,
                      exclude_uuids=uuids,
                      experiments=[e.name for e in self.selected_experiments] if self.selected_experiments else None)

            lp, hp = self.low_post, self.high_post
            ans = self._retrieve_sample_analyses(new,
                                                 low_post=lp,
                                                 high_post=hp,
                                                 **kw)

            self.debug('selected samples changed. loading analyses. '
                       'low={}, high={}, limit={} n={}'.format(lp, hp, lim, len(ans)))

        self.analysis_table.set_analyses(ans, selected_identifiers={ai.identifier for ai in new})
        self.dump_browser()
        # self.filter_focus = not bool(new)

    # @on_trait_change('analysis_table:selected')
    # def _handle_analysis_selected(self, new):
    #     if self.use_focus_switching:
    #         self.filter_focus = not bool(new)

    # private
    def _find_references_hook(self):
        m = FindReferencesConfigModel()
        v = FindReferencesConfigView(model=m)
        info = v.edit_traits()
        if info.result:
            atypes = m.formatted_analysis_types
            times = sorted((ai.rundate for ai in self.analysis_table.analyses))
            refs = self.db.find_references(times, atypes, hours=m.threshold, make_records=False)
            if refs:
                self.analysis_table.add_analyses(refs)
            else:
                self.warning_dialog('No References found.\n\nAnalysis Types {}'.format(','.join(atypes)))

    def _project_date_bins(self, identifier):
        db = self.db
        hours = self.search_criteria.reference_hours_padding
        with db.session_ctx():
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

    def _get_manager(self):
        if self.use_workspace:
            obj = self.workspace.index_db
        else:
            obj = self.manager
        return obj

    def _selected_experiments_changed_hook(self, names):
        self.irradiations = []
        # get all irradiations contained within these experiments
        db = self.db
        with db.session_ctx():
            irrads = db.get_irradiations_by_experiments(names)
            if irrads:
                self.irradiations = [i.name for i in irrads]

    def _selected_projects_change_hook(self, names):

        self.selected_samples = []
        self.analysis_table.analyses = []

        if not self._top_level_filter:
            self._top_level_filter = 'project'

        if names:
            if self._top_level_filter == 'project':
                db = self.db
                with db.session_ctx():
                    irrads = db.get_irradiations(project_names=names)
                    self.irradiations = [i.name for i in irrads]

    def _retrieve_labnumbers(self):
        es = []
        ps = []
        ms = []
        if self.mass_spectrometers_enabled:
            if self.mass_spectrometer_includes:
                ms = self.mass_spectrometer_includes

        if self.experiment_enabled:
            if self.selected_experiments:
                es = [e.name for e in self.selected_experiments]
        if self.project_enabled:
            if self.selected_projects:
                rs, ps = partition([p.name for p in self.selected_projects], lambda x: x.startswith('RECENT'))
                ps, rs = list(ps), list(rs)
                if rs:
                    hpost = datetime.now()
                    lpost = hpost - timedelta(hours=self.search_criteria.recent_hours)
                    self._low_post = lpost

                    self.use_high_post = False
                    self.use_low_post = True

                    self.trait_property_changed('low_post', self._low_post)
                    for ri in rs:
                        mi = extract_mass_spectrometer_name(ri)
                        if mi not in ms:
                            ms.append(mi)
                        self._recent_mass_spectrometers.append(mi)

        ls = self.db.get_labnumbers(projects=ps, experiments=es, mass_spectrometers=ms,
                                    irradiation=self.irradiation if self.irradiation_enabled else None,
                                    level=self.level if self.irradiation_enabled else None,
                                    analysis_types=self.analysis_include_types if self.use_analysis_type_filtering else None,
                                    high_post=self.high_post if self.use_high_post else None,
                                    low_post=self.low_post if self.use_low_post else None)
        return ls

    def _identifier_change_hook(self, db, new, lns):
        if len(new) > 2:
            if self.project_enabled:
                def get_projects():
                    for li in lns:
                        try:
                            yield li.sample.project
                        except AttributeError, e:
                            print 'exception', e

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
            self.debug('load projects for irradiation= {}, level= {}'.format(self.irradiation, self.level))
            db = self.db
            with db.session_ctx():
                ps = db.get_projects(irradiation=self.irradiation,
                                     level=self.level,
                                     mass_spectrometers=ms)

                ps = self._make_project_records(ps, include_recent_first=True)
                old_selection = [p.name for p in self.selected_projects]
                self.projects = ps
                self.selected_projects = [p for p in ps if p.name in old_selection]

    def _load_projects_and_irradiations(self):
        ms = None
        if self.mass_spectrometers_enabled:
            ms = self.mass_spectrometer_includes

        db = self.db
        with db.session_ctx():
            ps = db.get_projects(mass_spectrometers=ms)
            ps = self._make_project_records(ps,
                                            ms, include_recent_first=True)
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
                self.debug('_load_projects_and_irradiations. no irradiations')

    def _load_mass_spectrometers(self):
        db = self.db
        ms = db.get_mass_spectrometers()
        if ms:
            ms = [mi.name for mi in ms]
            self.available_mass_spectrometers = ms

    def _load_analysis_types(self):
        db = self.db
        ms = [mi.name for mi in db.get_analysis_types()]
        self.analysis_types = ['Analysis Type', 'None'] + ms

    def _load_extraction_devices(self):
        db = self.db
        ms = [mi.name for mi in db.get_extraction_devices()]
        self.extraction_devices = ['Extraction Device', 'None'] + ms

    def _get_analysis_types_visible(self):
        return self._get_visible(self.use_analysis_type_filtering)

    def _get_irradiation_visible(self):
        return self._get_visible(self.irradiation_enabled)

    def _get_date_visible(self):
        return self._get_visible(self.use_low_post or self.use_high_post or self.use_named_date_range)

    def _get_mass_spectrometer_visible(self):
        return self._get_visible(self.mass_spectrometers_enabled)

    def _get_identifier_visible(self):
        return True
        # return self.filter_focus if self.use_focus_switching else True

    def _get_project_visible(self):
        return self._get_visible(self.project_enabled)

    def _get_visible(self, default):
        return True
        # if self.use_focus_switching and not self.filter_focus:
        #     ret = False  # default
        # return ret

    def _get_filter_label(self):
        ss = []
        if self.identifier:
            ss.append('Identifier={}'.format(self.identifier))

        if self.mass_spectrometers_enabled:
            ss.append('MS={}'.format(','.join(self.mass_spectrometer_includes)))

        if self.project_enabled:
            if self.selected_projects:
                s = 'Project= {}'.format(','.join([s.name for s in self.selected_projects]))
                ss.append(s)

        if self.irradiation_enabled:
            if self.irradiation:
                s = 'Irradiation= {}'.format(self.irradiation)
                ss.append(s)

        if self.use_analysis_type_filtering:
            if self.analysis_include_types:
                s = 'Types= {}'.format(self.analysis_include_types)
                ss.append(s)

        if self.use_low_post:
            # s='>={}'.format(self.low_post.strftime('%m-%d-%Y %H:%M'))
            s = '>={}'.format(self.low_post)
            ss.append(s)

        if self.use_high_post:
            s = '<={}'.format(self.high_post)
            ss.append(s)

        if self.use_named_date_range:
            ss.append(self.named_date_range)

        txt = ''
        if ss:
            txt = ' + '.join(ss)

        n = len(txt)
        if n > NCHARS:
            lines = REG.findall(txt)
            nn = NCHARS * len(lines)
            if nn < n:
                lines.append(txt[nn:])
            return '\n'.join(lines)

        return txt

    def _time_view_model_default(self):
        return TimeViewModel(db=self.db)

    # ============= EOF =============================================
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

    # print self.project_enabled, self.irradiation_enabled

    # if self.selected_experiments:
    #     ls = db.get_experiment_labnumbers([e.name for e in self.selected_experiments])
    # else:
    #     elif self.project_enabled:
    #         if not self.irradiation_enabled:
    #             ls = super(BrowserModel, self)._retrieve_labnumbers_hook(db)
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
    # return ls

    # def _graphical_filter_button_fired(self):
    #     # print 'ffffassdf'
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
    #         ans = db.get_analyses_date_range(lpost, hpost, order='asc',
    #                                          mass_spectrometers=ms)
    #         # ans = db.get_date_range_analyses(lpost, hpost,
    #         #                                  ordering='asc',
    #         #                                  spectrometer=ms)
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
