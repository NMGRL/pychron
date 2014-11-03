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
from traits.api import List, Str, Bool, Any, Enum, Button, \
    Int, Property, cached_property, DelegatesTo, Date, Instance, HasTraits
import apptools.sweet_pickle as pickle
# ============= standard library imports ========================
from datetime import timedelta, datetime
import os
import re
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.codetools.inspection import caller
from pychron.core.progress import progress_loader
from pychron.database.orms.isotope.gen import gen_ProjectTable
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.envisage.browser.date_selector import DateSelector
from pychron.envisage.browser.record_views import ProjectRecordView, LabnumberRecordView, AnalysisGroupRecordView
from pychron.envisage.browser.table_configurer import SampleTableConfigurer
from pychron.paths import paths


def filter_func(new, attr=None, comp=None):
    comp_keys = {'=': '__eq__',
                 '<': '__lt__',
                 '>': '__gt__',
                 '<=': '__le__',
                 '>=': '__ge__',
                 'not =': '__ne__'}
    if comp:
        if comp in comp_keys:
            comp_key = comp_keys[comp]
        else:
            comp_key = comp

    def func(x):
        if attr:
            x = getattr(x, attr.lower())

        if comp is None:
            return x.lower().startswith(new.lower())
        else:
            return getattr(x, comp_key)(str(new))

    return func


class SearchCriteria(HasTraits):
    recent_hours = Int


def extract_mass_spectrometer_name(name):
    if 'RECENT' in name:
        args = name.split(' ')
        ms = ' '.join(args[1:]).lower()
        return ms


class BrowserMixin(ColumnSorterMixin):
    projects = List
    oprojects = List
    project_enabled = Bool(True)

    samples = List
    osamples = List

    analysis_groups = List

    identifier = Str

    sample_filter = Str

    date_configure_button = Button

    selected_projects = Any
    selected_samples = Any
    selected_analysis_groups = Any

    dclicked_sample = Any
    dclicked_analysis_group = Any

    auto_select_analysis = Bool(False)

    sample_filter_values = Property(List, depends_on='osamples, sample_filter_parameter')
    sample_filter_parameter = Str('name')
    sample_filter_comparator = Enum('=', 'not =')
    sample_filter_parameters = Property(List, depends_on='sample_tabular_adapter.columns')
    configure_sample_table = Button
    clear_sample_table = Button
    clear_selection_button = Button

    find_by_irradiation = Button

    filter_non_run_samples = DelegatesTo('table_configurer')

    sample_tabular_adapter = Any
    table_configurer = Instance(SampleTableConfigurer)

    search_criteria = Instance(SearchCriteria, ())

    use_mass_spectrometers = Bool
    mass_spectrometer_includes = List
    available_mass_spectrometers = List

    named_date_range = Enum('this month', 'this week', 'yesterday')
    low_post = Property(Date, depends_on='_low_post')
    high_post = Property(Date, depends_on='_high_post')
    use_low_post = Bool
    use_high_post = Bool
    use_named_date_range = Bool
    _low_post = Date
    _high_post = Date
    _recent_low_post = None
    _recent_mass_spectrometers = None
    _previous_recent_name = ''

    use_analysis_type_filtering = Bool
    analysis_include_types = Property(List)
    _analysis_include_types = List(['Unknown'])
    available_analysis_types = List(['Unknown', 'Blank', 'Air', 'Cocktail', 'Monitors'])

    sample_view_active = Bool(True)

    use_workspace = False
    workspace = None
    db = Property

    def _get_db(self):
        if self.use_workspace:
            return self.workspace.index_db
        else:
            return self.manager.db

    def dump_browser(self):
        self.dump_browser_selection()
        self.dump_browser_options()

    # persistence
    def _browser_options_hook(self, d):
        pass

    def dump_browser_options(self):
        d = {
            # 'include_monitors': self.include_monitors,
            # 'include_unknowns': self.include_unknowns,
            'project_enabled': self.project_enabled,
            'sample_view_active': self.sample_view_active}
        self._browser_options_hook(d)

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

    def load_browser_date_bounds(self):
        obj = self._get_browser_persistence()
        if obj:
            for attr in ('use_low_post', 'use_high_post',
                         'use_named_date_range', 'named_date_range',
                         'low_post', 'high_post', ):
                sd = obj.get(attr)
                if sd:
                    setattr(self, attr, sd)

    def load_browser_selection(self):
        # self.debug('$$$$$$$$$$$$$$$$$$$$$ Loading browser selection')
        obj = self._get_browser_persistence()
        if obj:
            self._load_browser_selection(obj)

    def dump_browser_selection(self):
        # self.debug('$$$$$$$$$$$$$$$$$$$$$ Dumping browser selection')

        ps = []
        if self.selected_projects:
            ps = [p.name for p in self.selected_projects]

        ss = []
        if self.selected_samples:
            ss = [p.identifier for p in self.selected_samples]

        obj = dict(projects=ps,
                   samples=ss,
                   use_low_post=self.use_low_post,
                   use_high_post=self.use_high_post,
                   use_named_date_range=self.use_named_date_range,
                   named_date_range=self.named_date_range,
                   low_post=self.low_post,
                   high_post=self.high_post)

        p = os.path.join(paths.hidden_dir, 'browser_selection')
        try:
            with open(p, 'wb') as fp:
                pickle.dump(obj, fp)
        except (pickle.PickleError, EOFError, OSError), e:
            #self.debug('Failed dumping previous browser selection. {}'.format(e))
            return

    def set_projects(self, ps, sel=None):
        if sel is None:
            sel = []

        self.oprojects = ps
        self.projects = ps
        self.trait_set(selected_projects=sel)

    def set_samples(self, s, sel=None):
        if sel is None:
            sel = []

        self.samples = s
        self.osamples = s
        self.trait_set(selected_samples=sel)

    def _make_project_records(self, ps, ms=None, include_recent_first=True):
        db = self.db
        with db.session_ctx():
            if not ms:
                ms = db.get_mass_spectrometers()
                ms = [mi.name for mi in ms]

            recents = [ProjectRecordView('RECENT {}'.format(mi.upper())) for mi in ms]
            pss = [ProjectRecordView(p) for p in ps]

            # move references project to after Recent
            p = next((p for p in pss if p.name.lower() == 'references'), None)
            if p is not None:
                rp = pss.pop(pss.index(p))
                pss.insert(0, rp)

            if include_recent_first:
                return recents + pss
            else:
                return pss + recents

    def load_projects(self):
        db = self.db
        with db.session_ctx():
            ps = db.get_projects(order=gen_ProjectTable.name.asc())
            ad = self._make_project_records(ps)
            self.projects = ad
            self.oprojects = ad

    def get_analysis_groups(self, names):
        if not isinstance(names[0], (str, unicode)):
            names = [ni.name for ni in names]

        db = self.db

        with db.session_ctx():
            gs = db.get_analysis_groups(projects=names)
            grps = [AnalysisGroupRecordView(gi) for gi in gs]
        return grps

    # private
    # column sort mixin interface
    def _sample_name_sort_key(self, v):
        v = v.name
        args = re.split('\D', v)
        if args:
            v = [ai for ai in args if ai]

        return v

    # database querying
    def _load_associated_groups(self, names):
        """
            names: list of project names
        """
        grps = self.get_analysis_groups(names)
        self.analysis_groups = grps

    def _load_associated_samples(self, names):
        """
            names: list of project names
        """
        db = self.db
        sams = []
        with db.session_ctx():
            self._recent_mass_spectrometers = []
            warned = False

            for name in names:
                # load associated samples
                if name.startswith('RECENT'):
                    if not self.search_criteria.recent_hours:
                        if not warned:
                            self.warning_dialog('Set "Recent Hours" in Preferences.\n'
                                                '"Recent Hours" is located in the "Processing" category')
                            warned = True
                    else:
                        sams.extend(self._retrieve_recent_samples(name))
                else:
                    sams.extend(self._retrieve_samples())

        self.samples = sams
        self.osamples = sams

    def _retrieve_recent_samples(self, recent_name):
        ms = extract_mass_spectrometer_name(recent_name)

        db = self.db
        with db.session_ctx():
            hpost = datetime.now()

            #use users low_post if set
            if not self.use_low_post and not self.use_named_date_range:
                lpost = hpost - timedelta(hours=self.search_criteria.recent_hours)
                self.use_low_post = True
                self._low_post = lpost.date()
                self._recent_low_post = lpost

            self._recent_mass_spectrometers.append(ms)

            if not self.use_named_date_range:
                self.use_high_post = True
                self._high_post = hpost.date()

            sams = self._retrieve_samples()

        return sams

    def _populate_samples(self, lns=None):
        db = self.db

        with db.session_ctx():
            if not lns:
                lns = [db.get_labnumber(self.identifier)]

            n = len(lns)
            self.debug('_populate_samples n={}'.format(n))

            def func(li, prog, i, n):
                if prog:
                    prog.change_message('Loading Labnumber {}'.format(li.identifier))
                return LabnumberRecordView(li)

            sams = progress_loader(lns, func)

        sel = sams[:1] if n == 1 and sams else []
        self.set_samples(sams, sel)

    def _retrieve_samples_hook(self, db):
        projects = self.selected_projects

        if self.use_mass_spectrometers:
            mass_spectrometers = self.mass_spectrometer_includes
        else:
            mass_spectrometers = [extract_mass_spectrometer_name(p.name) for p in projects]
            mass_spectrometers = [ms for ms in mass_spectrometers if ms]

        projects = [p.name for p in projects if not p.name.startswith('RECENT')]
        atypes = self.analysis_include_types if self.use_analysis_type_filtering else None

        lp, hp = self.low_post, self.high_post
        if atypes and projects:
            tlp, thp = db.get_min_max_analysis_timestamp(projects=projects, delta=1)
            if not lp:
                lp=tlp
            if not hp:
                hp=thp

        ls = db.get_project_labnumbers(projects,
                                       self.filter_non_run_samples,
                                       lp, hp,
                                       #self.low_post,
                                       #self.high_post,
                                       analysis_types=atypes,
                                       mass_spectrometers=mass_spectrometers)
        return ls

    @caller
    def _retrieve_samples(self):
        db = self.db
        # dont query if analysis_types enabled but not analysis type specified
        if self.use_analysis_type_filtering and not self.analysis_include_types:
            self.warning_dialog('Specify Analysis Types or disable Analysis Type Filtering')
            return []

        with db.session_ctx():
            ls = self._retrieve_samples_hook(db)
            self.debug('_retrieve_samples n={}'.format(len(ls)))

            def func(li, prog, i, n):
                if prog:
                    prog.change_message('Loading Labnumber {}'.format(li.identifier))
                return LabnumberRecordView(li)

            sams = progress_loader(ls, func)
        return sams

    def _retrieve_analyses(self, samples=None, limit=500,
                           low_post=None,
                           high_post=None,
                           exclude_uuids=None,
                           include_invalid=False,
                           mass_spectrometers=None,
                           make_records=True):
        db = self.db
        with db.session_ctx():
            if samples:
                lns = [si.labnumber for si in samples]
                self.debug('retrieving identifiers={}'.format(','.join(lns)))
                if low_post is None:
                    lps = [si.low_post for si in samples if si.low_post is not None]
                    low_post = min(lps) if lps else None

                ans, tc = db.get_labnumber_analyses(lns,
                                                    low_post=low_post,
                                                    high_post=high_post,
                                                    limit=limit,
                                                    exclude_uuids=exclude_uuids,
                                                    include_invalid=include_invalid,
                                                    mass_spectrometers=mass_spectrometers)
                self.debug('retrieved analyses n={}'.format(tc))
            else:
                ans = db.get_analyses_date_range(low_post, high_post,
                                                 mass_spectrometers=mass_spectrometers,
                                                 limit=limit)

            if make_records:
                return self._make_records(ans)
            else:
                return ans

    def _retrieve_sample_analyses(self, samples,
                                  **kw):
        return self._retrieve_analyses(samples=samples, **kw)

    def _make_records(self, ans):
        def func(xi, prog, i, n):
            if prog:
                prog.change_message('Loading {}'.format(xi.record_id))
            return IsotopeRecordView(xi)

        return progress_loader(ans, func, threshold=25)

    def _get_sample_filter_parameter(self):
        p = self.sample_filter_parameter
        if p == 'Sample':
            p = 'name'

        return p.lower()

    # persistence private
    def _get_browser_persistence(self):
        p = os.path.join(paths.hidden_dir, 'browser_selection')
        if os.path.isfile(p):
            try:
                with open(p, 'rb') as fp:
                    return pickle.load(fp)
            except (pickle.PickleError, EOFError, OSError), e:
                # self.debug('Failed loaded previous browser selection. {}'.format(e))
                pass

    def _load_browser_selection(self, selection):
        def load(attr, values):
            def get(n):
                return next((p for p in values if p.id == n), None)

            try:
                sel = selection[attr]
            except KeyError:
                return

            vs = [get(pp) for pp in sel]
            vs = [pp for pp in vs if pp is not None]
            setattr(self, 'selected_{}'.format(attr), vs)

        load('projects', self.projects)
        load('samples', self.samples)

    # handlers
    def _identifier_changed(self, new):
        db = self.db
        if new:
            if len(new) > 2:
                with db.session_ctx():
                    lns = self._get_identifiers(db, new)
                    # lns = db.get_labnumbers_startswith(new)
                    if lns:
                        self._identifier_change_hook(db, new, lns)
                        self._populate_samples(lns)
                    else:
                        self.set_samples([])
                        self.projects = self.oprojects[:]
        else:
            self.projects = self.oprojects[:]
            self.set_samples([])

    def _get_identifiers(self, db, new):
        ms = None
        if self.use_mass_spectrometers:
            ms = self.mass_spectrometer_includes

        return db.get_labnumbers_startswith(new, mass_spectrometers=ms)

    def _identifier_change_hook(self, db, new, lns):
        pass

    def _selected_projects_changed(self, old, new):
        if new and self.project_enabled:
            self._recent_low_post = None
            self._recent_mass_spectrometers = None
            if old:
                if any(['RECENT' in x.name for x in old]) and not any(['RECENT' in x.name for x in new]):
                    self.use_high_post = False
                    self.use_low_post = False

            names = [ni.name for ni in new]
            self.debug('selected projects={}'.format(names))
            self._load_associated_samples(names)
            self._load_associated_groups(names)

            self._selected_projects_change_hook(names)
            self.dump_browser_selection()

    def _selected_projects_change_hook(self, names):
        pass

    def _clear_sample_table_fired(self):
        self.samples = []
        self.osamples = []

    def _configure_sample_table_fired(self):
        self.table_configurer.edit_traits()

    def _sample_tabular_adapter_changed(self):
        self.table_configurer.adapter = self.sample_tabular_adapter
        self.table_configurer.load()

    def _clear_selection_button_fired(self):
        self.selected_projects = []
        self.selected_samples = []
        self.samples = []
        self.osamples = []

    def _use_named_date_range_changed(self, new):
        if new:
            self.use_low_post, self.use_high_post = False, False

    def _date_configure_button_fired(self):
        ds = DateSelector(model=self)
        info = ds.edit_traits()
        if info.result:
            self._filter_by_hook()

    def _filter_by_hook(self):
        s = self._retrieve_samples()
        self.set_samples(s, [])

        # @on_trait_change('level')
        # def _find_by_irradiation(self):
        #     if not (self.level and self._activated):
        #         return

        # man = self.manager
        # db = man.db
        # with db.session_ctx():
        #     level = man.get_level(self.level)
        #     if level:
        #
        #         refs, unks = man.group_level(level)
        #         xs = []
        #         if 'Monitors' in self.analysis_include_types:
        #         # if self.include_monitors:
        #             xs.extend(refs)
        #         if 'Unknowns' in self.analysis_include_types:
        #         # if self.include_unknowns:
        #             xs.extend(unks)
        #
        #         lns = [x.identifier for x in xs]
        #         self.samples = [LabnumberRecordView(li)
        #                         for li in db.get_labnumbers(lns)
        #                         if li.sample]

        # def _sample_filter_parameter_changed(self, new):
        #     if new:
        #         vs = []
        #         p = self._get_sample_filter_parameter()

        # for si in self.osamples:
        #     v = getattr(si, p)
        #     if not v in vs:
        #         vs.append(v)
        #
        # self.sample_filter_values = vs

    # def _project_filter_changed(self, new):
    #     self.projects = filter(filter_func(new, 'name'), self.oprojects)

    def _sample_filter_changed(self, new):
        name = self._get_sample_filter_parameter()
        self.samples = filter(filter_func(new, name), self.osamples)

    # proprty get/set
    def _set_low_post(self, v):
        self._low_post = v

    # def _validate_low_post(self, v):
    # v = v.replace('/', '-')
    # if v.count('-') < 3:
    # map(int, v.split('-'))

    def _set_high_post(self, v):
        self._high_post = v

    # def _validate_high_post(self,v):
    #     v=v.replace('/','-')
    #     if v.count('-')<3:
    #         map(int, v.split('-'))

    def _get_high_post(self):
        hp = None

        tdy = datetime.today()
        if self.use_named_date_range:
            if self.named_date_range in ('this month', 'today', 'this week'):
                hp = tdy
            elif self.named_date_range == 'yesterday':
                hp = tdy - timedelta(days=1)
        elif self.use_high_post:
            hp = self._high_post
            if not hp:
                hp = tdy
        return hp

    def _get_low_post(self):
        lp = None
        tdy = datetime.today()
        if self.use_named_date_range:
            if self.named_date_range == 'this month':
                lp = tdy - timedelta(days=tdy.day,
                                     seconds=tdy.second,
                                     hours=tdy.hour,
                                     minutes=tdy.minute)
            elif self.named_date_range == 'this week':
                days = datetime.today().weekday()
                lp = tdy - timedelta(days=days)

        elif self.use_low_post:
            lp = self._low_post
            if not lp:
                lp = tdy

        return lp

    @cached_property
    def _get_sample_filter_parameters(self):
        if self.sample_tabular_adapter:
            return dict([(ci[1], ci[0]) for ci in self.sample_tabular_adapter.columns])
        else:
            return {}

    @cached_property
    def _get_sample_filter_values(self):
        p = self._get_sample_filter_parameter()
        return list(set([getattr(si, p) for si in self.osamples]))

    def _get_analysis_include_types(self):
        if self.use_analysis_type_filtering:
            ats = self._analysis_include_types
            return map(str.lower, ats)

    #factories
    # def _record_view_factory(self, ai, progress=None, **kw):
    #
    # iso = IsotopeRecordView(**kw)
    #     iso.create(ai)
    #     if progress:
    #         progress.change_message('Loading {}'.format(iso.record_id))
    #
    #     return iso



    # defaults
    def _table_configurer_default(self):
        return SampleTableConfigurer()

#============= EOF =============================================
