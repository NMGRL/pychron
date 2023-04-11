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

import os
import re
from datetime import timedelta, datetime

import six.moves.cPickle as pickle

# ============= enthought library imports =======================
from traits.api import (
    List,
    Str,
    Bool,
    Any,
    Enum,
    Button,
    Int,
    Property,
    cached_property,
    DelegatesTo,
    Date,
    Instance,
    HasTraits,
    Event,
    Float,
)
from traits.trait_types import BaseStr
from traitsui.tabular_adapter import TabularAdapter

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.progress import progress_loader
from pychron.core.ui.table_configurer import SampleTableConfigurer
from pychron.envisage.browser import progress_bind_records
from pychron.envisage.browser.adapters import LabnumberAdapter
from pychron.envisage.browser.record_views import (
    ProjectRecordView,
    LabnumberRecordView,
    PrincipalInvestigatorRecordView,
    LoadRecordView,
)
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceLoggable
from pychron.pychron_constants import DVC_PROTOCOL


class IdentifierStr(BaseStr):
    def validate(self, obj, name, value):
        if len(value) > 2:
            return value
        else:
            self.error(obj, name, value)


def filter_func(new, attr=None, comp=None):
    comp_keys = {
        "=": "__eq__",
        "<": "__lt__",
        ">": "__gt__",
        "<=": "__le__",
        ">=": "__ge__",
        "not =": "__ne__",
    }
    if comp:
        if comp in comp_keys:
            comp_key = comp_keys[comp]
        else:
            comp_key = comp

    def func(x):
        if attr:
            x = getattr(x, attr.lower())

        if comp is None:
            if isinstance(x, (float, int)):
                try:
                    return x == float(new)
                except ValueError:
                    pass
            else:
                return str(x).lower().startswith(new.lower())
        else:
            v = float(new) if isinstance(x, (float, int)) else str(new)

            return getattr(x, comp_key)(v)

    return func


class SearchCriteria(HasTraits):
    reference_hours_padding = Float
    graphical_filtering_max_days = Int


def extract_mass_spectrometer_name(name):
    if "RECENT" in name:
        args = name.split(" ")
        ms = " ".join(args[1:]).lower()
        return ms


class BaseBrowserModel(PersistenceLoggable, ColumnSorterMixin):
    dvc = Instance("pychron.dvc.dvc.DVC")
    plot_selected = Event
    use_quick_recall = Bool(True)

    selected_principal_investigators = Any
    principal_investigators = List
    principal_investigator_names = List

    projects = List
    oprojects = List
    repositories = List
    orepositories = List
    samples = List
    osamples = List

    selected_loads = Any
    loads = List

    include_recent = True
    project_enabled = Bool(True)
    repository_enabled = Bool(True)
    principal_investigator_enabled = Bool(True)
    load_enabled = Bool(True)

    analysis_groups = List

    identifier = IdentifierStr(enter_set=True, auto_set=False)

    sample_filter = Str

    date_configure_button = Button

    selected_projects = Any
    # selected_repositories = Any
    selected_samples = List
    selected_analysis_groups = Any

    dclicked_sample = Any
    dclicked_analysis_group = Any

    auto_select_analysis = Bool(False)

    sample_filter_values = Property(
        List, depends_on="osamples, sample_filter_parameter"
    )
    sample_filter_parameter = Str("name")
    sample_filter_comparator = Enum(
        "fuzzy",
        "startswith",
        "=",
        "not =",
    )
    sample_filter_parameters = Property(
        List, depends_on="labnumber_tabular_adapter.columns"
    )
    clear_sample_table = Button
    clear_selection_button = Button

    find_by_irradiation = Button

    filter_non_run_samples = DelegatesTo("table_configurer")

    labnumber_tabular_adapter = Instance(TabularAdapter)
    table_configurer = Instance(SampleTableConfigurer)

    search_criteria = Instance(SearchCriteria, ())

    mass_spectrometers_enabled = Bool
    mass_spectrometer_includes = List
    available_mass_spectrometers = List

    auto_load_database = Bool(True)
    load_selection_enabled = Bool(True)

    named_date_range = Enum("this month", "this week", "yesterday")
    low_post = Property(
        Date,
        depends_on="date_enabled, _low_post, use_low_post, use_named_date_range, "
        "named_date_range",
    )
    high_post = Property(
        Date,
        depends_on="date_enabled, _high_post, use_high_post, use_named_date_range, "
        "named_date_range",
    )

    use_low_post = Bool
    use_high_post = Bool
    use_named_date_range = Bool
    date_enabled = Bool
    _low_post = Date
    _high_post = Date
    _recent_low_post = None
    _recent_mass_spectrometers = None
    _previous_recent_name = ""

    use_analysis_type_filtering = Bool
    analysis_include_types = Property(List)
    _analysis_include_types = List(["Unknown"])
    available_analysis_types = List(["Unknown", "Blank", "Air", "Cocktail", "Monitors"])

    sample_view_active = Bool(True)

    # use_workspace = False
    # workspace = None
    # manager = Any

    db = Property

    use_fuzzy = True
    pattributes = (
        "project_enabled",
        "repository_enabled",
        "principal_investigator_enabled",
        "load_enabled",
        "date_enabled",
        "sample_view_active",
        "use_low_post",
        "use_high_post",
        "use_named_date_range",
        "named_date_range",
        "low_post",
        "high_post",
    )

    persistence_name = "browser_options"
    selection_persistence_name = "browser_selection"

    _suppress_post_update = False
    _suppress_load_labnumbers = False

    def reattach(self):
        pass

    def activate_browser(self, force=False):
        pass

    def make_records(self, ans):
        return self._make_records(ans)

    def dump_browser(self):
        self.debug("dump browser")
        self.dump()
        self.dump_browser_selection()

    def load_browser_options(self):
        self.load(verbose=False)

    def load_browser_selection(self):
        obj = self._get_browser_persistence()
        if obj:
            self.debug("$$$$$$$$$$$$$$$$$$$$$ Loading browser selection")
            self._load_browser_selection(obj)

    def dump_browser_selection(self):
        self.debug("$$$$$$$$$$$$$$$$$$$$$ Dumping browser selection")

        ps = []
        if self.selected_projects:
            ps = [p.name for p in self.selected_projects]

        ss = []
        if self.selected_samples:
            ss = [p.identifier for p in self.selected_samples]

        # es = []
        # if self.selected_repositories:
        #     es = [e.name for e in self.selected_repositories]

        pis = []
        if self.selected_principal_investigators:
            pis = [p.name for p in self.selected_principal_investigators]

        ls = []
        if self.selected_loads:
            ls = [l.name for l in self.selected_loads]

        obj = dict(
            projects=ps,
            samples=ss,
            loads=ls,
            # repositories=es,
            principal_investigators=pis,
            use_low_post=self.use_low_post,
            use_high_post=self.use_high_post,
            use_named_date_range=self.use_named_date_range,
            named_date_range=self.named_date_range,
            low_post=self.low_post,
            high_post=self.high_post,
            date_enabled=self.date_enabled,
        )

        try:
            with open(self.selection_persistence_path, "wb") as wfile:
                pickle.dump(obj, wfile)
        except (pickle.PickleError, EOFError, OSError) as e:
            # self.debug('Failed dumping previous browser selection. {}'.format(e))
            return

    def configure_sample_table(self):
        self.table_configurer.edit_traits(kind="livemodal")

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

    def load_loads(self):
        db = self.db
        self.loads = [LoadRecordView(n) for n in db.get_measured_load_names() if n]

    def load_repositories(self):
        db = self.db
        es = db.get_repositories()
        if es:
            es = sorted([e.record_view for e in es], key=lambda x: x.name)

            self.repositories = es
            self.orepositories = es

    def load_projects(self, include_recent=True):
        db = self.db
        ps = db.get_projects(order="asc")
        ad = self._make_project_records(ps, include_recent=include_recent)
        self.projects = ad
        self.oprojects = ad

    def load_principal_investigators(self):
        self.debug("load principal investigators")
        db = self.db
        ps = db.get_principal_investigators(order="asc")
        self.debug("n pis={}".format(len(ps)))
        if ps:
            self.principal_investigators = [
                PrincipalInvestigatorRecordView(p) for p in ps
            ]
            self.principal_investigator_names = [p.name for p in ps]

    def get_analysis_groups(self, projects):
        db = self.db
        gs = db.get_analysis_groups([p.unique_id for p in projects])
        return gs

    def do_filter(self):
        self._filter_by_hook()

    def select_all(self):
        self.selected_samples = self.samples[:]

    def load_associated_groups(self, names):
        self._load_associated_groups(names)

    # private
    # column sort mixin interface
    def _sample_name_sort_key(self, v):
        v = v.name
        args = re.split("\D", v)
        if args:
            v = [ai for ai in args if ai]

        return v

    # database querying
    def _load_repository_date_range(self, names):
        lp, hp = self.db.get_repository_date_range(names)
        if lp.date() == hp.date():
            hp += timedelta(days=1)
        self._set_posts(lp, hp, enable=False)

    def _load_project_date_range(self, names):
        lp, hp = self.db.get_project_date_range(names)
        if lp.date() == hp.date():
            hp += timedelta(days=1)
        self._set_posts(lp, hp, enable=False)

    def _set_posts(self, lp, hp, enable=True):
        self.use_low_post, self.use_high_post = True, True
        # ol, oh = self.use_low_post, self.use_high_post
        self.debug("set posts lp={} hp={}".format(lp, hp))
        self.low_post, self.high_post = lp, hp

        self._suppress_post_update = True
        self.trait_property_changed("low_post", None)
        self.trait_property_changed("high_post", None)
        self._suppress_post_update = False

        self.use_low_post, self.use_high_post = enable, enable
        # self.use_low_post, self.use_high_post = ol, oh

    def _load_associated_groups(self, projects):
        """
        names: list of project names
        """
        self.debug(
            "load associated analysis groups for {}".format(
                ["{} ({})".format(p.name, p.principal_investigator) for p in projects]
            )
        )
        grps = self.get_analysis_groups(projects)
        self.analysis_groups = grps

    def _load_associated_labnumbers(self):
        """ """

        if self._suppress_load_labnumbers:
            print("skiping load associated")
            return

        sams = self._make_labnumbers()
        self.samples = sams
        self.osamples = sams

    def _populate_samples(self, lns=None):
        db = self.db

        if not lns:
            lns = [db.get_labnumber(self.identifier)]

        n = len(lns)
        self.debug("_populate_samples n={}".format(n))

        sams = self._load_sample_record_views(lns)

        sel = sams[:1] if n == 1 and sams else []
        self.set_samples(sams, sel)

    def _load_sample_record_views(self, lns):
        def func(li, prog, i, n):
            if prog:
                prog.change_message("Loading Labnumber {}".format(li.identifier))
            return LabnumberRecordView(li)

        sams = progress_loader(lns, func, step=25)
        return sams

    def _make_labnumbers(self):
        # dont query if analysis_types enabled but not analysis type specified
        if self.use_analysis_type_filtering and not self.analysis_include_types:
            self.warning_dialog(
                "Specify Analysis Types or disable Analysis Type Filtering"
            )
            return []

        sams = []
        ls = self._retrieve_labnumbers()
        if ls:
            self.debug("_retrieve_labnumbers n={}".format(len(ls)))
            sams = self._load_sample_record_views(ls)
        else:
            self.debug("No labnumbers")

        return sams

    def _retrieve_labnumbers(self):
        pass

    def _retrieve_analyses(
        self,
        samples=None,
        limit=500,
        order="asc",
        low_post=None,
        high_post=None,
        exclude_uuids=None,
        include_invalid=False,
        mass_spectrometers=None,
        repositories=None,
        loads=None,
        make_records=True,
        analysis_types=None,
    ):
        db = self.db
        if samples:
            lns = [si.labnumber for si in samples]
            self.debug("retrieving identifiers={}".format(",".join(lns)))
            # if low_post is None:
            # lps = [si.low_post for si in samples if si.low_post is not None]
            #     low_post = min(lps) if lps else None
            ans, tc = db.get_labnumber_analyses(
                lns,
                order=order,
                low_post=low_post,
                high_post=high_post,
                limit=limit,
                exclude_uuids=exclude_uuids,
                include_invalid=include_invalid,
                mass_spectrometers=mass_spectrometers,
                repositories=repositories,
                loads=loads,
            )
            self.debug("retrieved analyses n={}".format(tc))
        else:
            self.debug("retrieved analyses by date range")
            ans = db.get_analyses_by_date_range(
                low_post,
                high_post,
                order=order,
                mass_spectrometers=mass_spectrometers,
                repositories=repositories,
                limit=limit,
                analysis_types=analysis_types,
                loads=loads,
            )

        if make_records:
            return self._make_records(ans)
        else:
            return ans

    # def _retrieve_sample_analyses(self, samples, **kw):
    #    return self._retrieve_analyses(samples=samples, **kw)

    def _make_project_records(
        self, ps, ms=None, include_recent=True, include_recent_first=True
    ):
        if not ps:
            return []
        pss = sorted([ProjectRecordView(p) for p in ps], key=lambda x: x.name)
        return pss

    def _make_records(self, ans):
        n = len(ans)
        self.debug("make records {}".format(n))
        import time

        st = time.time()

        ret = progress_bind_records(ans)
        self.debug("make records {}".format(time.time() - st))
        return ret

    def _get_sample_filter_parameter(self):
        p = self.sample_filter_parameter
        if p == "Sample":
            p = "name"

        return p.lower()

    def _make_project(self, record):
        return ProjectRecordView(record)

    def _make_principal_investigator(self, record):
        return PrincipalInvestigatorRecordView(record)

    def _make_load(self, record):
        return LoadRecordView(record)

    def _make_sample(self, record):
        return LabnumberRecordView(record)

    def _load_browser_selection(self, selection):
        if not self.auto_load_database:
            for attr in ("load", "project", "principal_investigator", "sample"):
                pattr = "{}s".format(attr)
                try:
                    sel = selection[pattr]
                except KeyError:
                    return
                vs = []
                if sel:
                    if attr == "sample":
                        func = self.db.get_identifier
                    else:
                        func = getattr(self.db, "get_{}".format(attr))

                    make = getattr(self, "_make_{}".format(attr))
                    for si in sel:
                        v = func(si)
                        try:
                            vs.append(make(v))
                        except AttributeError:
                            pass

                    setattr(self, pattr, vs)
                    setattr(self, "selected_{}".format(pattr), vs)

        else:

            def load(attr, values):
                def get(n):
                    try:
                        return next((p for p in values if p.id == n), None)
                    except AttributeError as e:
                        print(e)
                        return

                try:
                    sel = selection[attr]
                except KeyError:
                    return

                vs = [get(pp) for pp in sel]
                vs = [pp for pp in vs if pp is not None]
                setattr(self, "selected_{}".format(attr), vs)

            load("principal_investigators", self.principal_investigators)
            load("projects", self.projects)
            # load('experiments', self.repositories)
            load("samples", self.samples)
            load("loads", self.loads)

    def _load_projects_for_principal_investigators(self, pis=None):
        ms = None
        if self.mass_spectrometers_enabled:
            ms = self.mass_spectrometer_includes

        if (
            not pis
            and self.principal_investigator_enabled
            and self.selected_principal_investigators
        ):
            pis = [p.name for p in self.selected_principal_investigators]

        if pis:
            self.debug("load projects for principal investigator= {}".format(pis))

        db = self.db
        ps = db.get_projects(
            principal_investigators=pis, mass_spectrometers=ms, verbose_query=True
        )

        ps = self._make_project_records(
            ps, include_recent_first=True, include_recent=True and self.include_recent
        )
        old_selection = []
        if self.selected_projects:
            old_selection = [p.name for p in self.selected_projects]
        self.projects = ps

        if old_selection:
            self.selected_projects = [p for p in ps if p.name in old_selection]

    def _load_analyses_for_group(self):
        grps = self.selected_analysis_groups
        if grps:
            self.debug("analysis group changed={}".format(grps))
            ans = [si.analysis for gi in grps for si in gi.sets]
            xx = self._make_records(ans)
            self.table.set_analyses(xx)

    # handlers
    def _selected_analysis_groups_changed(self):
        self._load_analyses_for_group()

    def _selected_principal_investigators_changed(self, new):
        if new and self.principal_investigator_enabled:
            self._load_projects_for_principal_investigators()
            self.dump_browser_selection()

    def _principal_investigator_enabled_changed(self):
        self._load_projects_for_principal_investigators()

    def _identifier_changed(self, new):
        db = self.db
        if new:
            if len(new) > 2:
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
        if self.mass_spectrometers_enabled:
            ms = self.mass_spectrometer_includes

        return db.get_labnumbers_startswith(new, mass_spectrometers=ms)

    def _identifier_change_hook(self, db, new, lns):
        pass

    # def _selected_repositories_changed(self, old, new):
    #     if new and self.repository_enabled:
    #         names = [n.name for n in new]
    #         self._load_repository_date_range(names)
    #         self._load_associated_labnumbers()
    #         self._selected_repositories_changed_hook(names)
    def _selected_loads_changed(self, new):
        if new and self.load_enabled:
            self._load_associated_labnumbers()

    def _selected_projects_changed(self, old, new):
        if new and self.project_enabled:
            # self._recent_low_post = None
            # self._recent_mass_spectrometers = None
            # isrecent = any(['RECENT' in x.name for x in new])
            # if old:
            #     if any(['RECENT' in x.name for x in old]) and not isrecent:
            #         self.use_high_post = False
            #         self.use_low_post = False

            names = [ni.name for ni in new]
            self.debug("bbmodel selected projects={}".format(names))
            # if not isrecent:
            #     self._load_project_date_range(names)
            self._load_project_date_range(names)

            self._load_associated_labnumbers()
            self._load_associated_groups(new)
        else:
            names = None

        self._selected_projects_change_hook(names)
        self.dump_browser_selection()

    def _selected_projects_change_hook(self, names):
        pass

    def _clear_sample_table_fired(self):
        self.samples = []
        self.osamples = []

    def _labnumber_tabular_adapter_changed(self):
        self.table_configurer.set_adapter(self.labnumber_tabular_adapter)

    def _clear_selection_button_fired(self):
        self.selected_projects = []
        self.selected_samples = []
        self.samples = []
        self.osamples = []

    def _use_named_date_range_changed(self, new):
        if new:
            self.use_low_post, self.use_high_post = False, False

    # def _date_configure_button_fired(self):
    #     ds = DateSelector(model=self)
    #     info = ds.edit_traits()
    #     if info.result:
    #         self._filter_by_hook()

    def _filter_by_hook(self):
        # self.high_post = datetime.now()
        # names = [ni.name for ni in self.selected_projects]
        self._load_associated_labnumbers()

    def _sample_filter_changed(self, new):
        name = self._get_sample_filter_parameter()
        comp = self.sample_filter_comparator
        if comp == "fuzzy":
            self.samples = fuzzyfinder(new, self.osamples, name)
        else:
            func = filter_func(new, name, comp)
            self.samples = [s for s in self.osamples if func(s)]
            # self.samples = list(filter(filter_func(new, name, comp), self.osamples))

    # property get/set
    def _set_low_post(self, v):
        if not self._suppress_post_update:
            self._low_post = v

    def _set_high_post(self, v):
        if not self._suppress_post_update:
            self._high_post = v

    @cached_property
    def _get_high_post(self):
        hp = None
        if self.date_enabled:
            tdy = datetime.today()
            if self.use_named_date_range:
                if self.named_date_range in ("this month", "today", "this week"):
                    hp = tdy
                elif self.named_date_range == "yesterday":
                    hp = tdy - timedelta(days=1)
            elif self.use_high_post:
                hp = self._high_post
                if not hp:
                    hp = tdy
        self.debug("GET HPOST={}".format(hp))
        return hp

    @cached_property
    def _get_low_post(self):
        lp = None
        if self.date_enabled:
            tdy = datetime.today()
            if self.use_named_date_range:
                if self.named_date_range == "this month":
                    lp = tdy - timedelta(
                        days=tdy.day,
                        seconds=tdy.second,
                        hours=tdy.hour,
                        minutes=tdy.minute,
                    )
                elif self.named_date_range == "this week":
                    days = datetime.today().weekday()
                    lp = tdy - timedelta(days=days)

            elif self.use_low_post:
                lp = self._low_post
                if not lp:
                    lp = tdy

        self.debug("GET LPOST={}".format(lp))
        return lp

    @cached_property
    def _get_sample_filter_parameters(self):
        # print 'fooooo', self.labnumber_tabular_adapter
        if self.labnumber_tabular_adapter:
            return {ci[1]: ci[0] for ci in self.labnumber_tabular_adapter.columns}
            # return dict([(ci[1], ci[0]) for ci in self.labnumber_tabular_adapter.columns])
        else:
            return {}

    @cached_property
    def _get_sample_filter_values(self):
        p = self._get_sample_filter_parameter()
        return list(set([getattr(si, p) for si in self.osamples]))

    def _get_analysis_include_types(self):
        if self.use_analysis_type_filtering:
            ats = self._analysis_include_types
            return [a.lower() for a in ats]

    def _handle_source_change(self, new):
        self.activate_browser(force=True)

    _warned = False

    @cached_property
    def _get_db(self):
        # if self.use_workspace:
        #     db = self.workspace.index_db
        if self.dvc:
            db = self.dvc
        else:
            db = self.application.get_service(DVC_PROTOCOL)

        if db is None:
            if not self._warned:
                self.warning_dialog("You need to enable the DVC plugin")
            self._warned = True
        else:
            db.on_trait_change(self._handle_source_change, "data_source")
            return db

    @property
    def selection_persistence_path(self):
        p = os.path.join(paths.hidden_dir, self.selection_persistence_name)
        return self._make_persistence_path(p)

    # persistence private
    def _get_browser_persistence(self):
        p = self.selection_persistence_path
        # p = os.path.join(paths.hidden_dir, 'browser_selection')
        if os.path.isfile(p):
            try:
                with open(p, "rb") as rfile:
                    return pickle.load(rfile)
            except (pickle.PickleError, EOFError, OSError, UnicodeDecodeError) as e:
                self.debug("Failed loaded previous browser selection. {}".format(e))
                pass
        else:
            self.debug("browser selection not a file {}".format(p))

    # defaults
    def _table_configurer_default(self):
        return SampleTableConfigurer()

    def _labnumber_tabular_adapter_default(self):
        adapter = LabnumberAdapter()
        self.table_configurer.set_adapter(adapter)
        return adapter


# ============= EOF =============================================
