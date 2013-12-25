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
import os
import re
from traits.api import List, Str, Bool, Any, Enum, Button, Int
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
from datetime import timedelta, datetime
#============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.database.orms.isotope.gen import gen_ProjectTable
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.envisage.browser.record_views import ProjectRecordView, SampleRecordView
from pychron.envisage.browser.table_configurer import SampleTableConfigurer
from pychron.paths import paths


DEFAULT_SPEC = 'Spectrometer'
DEFAULT_AT = 'Analysis Type'
DEFAULT_ED = 'Extraction Device'

from traits.api import HasTraits, Instance


class SearchCriteria(HasTraits):
    recent_hours = Int


class BrowserMixin(ColumnSorterMixin):
    projects = List
    oprojects = List

    samples = List  # Property(depends_on='selected_project')
    osamples = List

    project_filter = Str
    sample_filter = Str

    selected_projects = Any
    selected_samples = Any
    dclicked_sample = Any

    auto_select_analysis = Bool(False)

    sample_filter_values = List
    sample_filter_parameter = Str('Sample')
    sample_filter_comparator = Enum('=', 'not =')
    sample_filter_parameters = List(['Sample', 'Material', 'Labnumber'])

    configure_sample_table = Button
    clear_selection_button = Button

    filter_non_run_samples = Bool(True)

    sample_tabular_adapter = Any

    #    recent_hours = Int#(48)
    search_criteria = Instance(SearchCriteria, ())

    def load_browser_selection(self):
        #self.debug('$$$$$$$$$$$$$$$$$$$$$ Loading browser selection')
        p = os.path.join(paths.hidden_dir, 'browser_selection')
        if os.path.isfile(p):
            try:
                with open(p, 'rb') as fp:
                    sel = pickle.load(fp)
            except (pickle.PickleError, EOFError, OSError), e:
                #self.debug('Failed loaded previous browser selection. {}'.format(e))
                return

            self._load_browser_selection(sel)

    def _load_browser_selection(self, selection):
        def load(attr, values):
            def get(n):
                return next((p for p in values if p.name == n), None)

            try:
                sel = selection[attr]
            except KeyError:
                return

            vs = [get(pp) for pp in sel]
            vs = [pp for pp in vs if pp is not None]
            setattr(self, 'selected_{}'.format(attr), vs)

        load('projects', self.projects)
        load('samples', self.samples)

    def dump_browser_selection(self):
        #self.debug('$$$$$$$$$$$$$$$$$$$$$ Dumping browser selection')

        ps = []
        if self.selected_projects:
            ps = [p.name for p in self.selected_projects]

        ss = []
        if self.selected_samples:
            ss = [p.name for p in self.selected_samples]

        obj = dict(projects=ps,
                   samples=ss)

        p = os.path.join(paths.hidden_dir, 'browser_selection')
        try:
            with open(p, 'wb') as fp:
                pickle.dump(obj, fp)
        except (pickle.PickleError, EOFError, OSError), e:
            #self.debug('Failed dumping previous browser selection. {}'.format(e))
            return

    #column sort mixin interface
    def _sample_name_sort_key(self, v):
        v = v.name
        args = re.split('\D', v)
        if args:
            v = [ai for ai in args if ai]

        return v

    def set_projects(self, ps, sel):
        self.oprojects = ps
        self.projects = ps
        self.trait_set(selected_projects=sel)

    def set_samples(self, s, sel):
        self.samples = s
        self.osamples = s
        self.trait_set(selected_samples=sel)

    def load_projects(self):
        db = self.manager.db
        with db.session_ctx():
            ps = db.get_projects(order=gen_ProjectTable.name.asc())
            ms = db.get_mass_spectrometers()
            recents = [ProjectRecordView('Recent {}'.format(mi.name.capitalize())) for mi in ms]

            ad = recents + [ProjectRecordView(p) for p in ps]

            self.projects = ad
            self.oprojects = ad

    def _selected_projects_changed(self, new):
        if new:
            db = self.manager.db
            with db.session_ctx():
                if hasattr(new, '__iter__'):
                    name = new[0].name
                else:
                    name = new.name

                if name.startswith('Recent'):
                    sams = self._set_recent_samples(name)
                else:
                    sams = self._set_samples()

            self.samples = sams
            self.osamples = sams

            #if sams:
            #    self.selected_samples = sams[:1]

            p = self._get_sample_filter_parameter()
            self.sample_filter_values = [getattr(si, p) for si in sams]

    def _set_recent_samples(self, recent_name):
        args = recent_name.split(' ')
        ms = ' '.join(args[1:])

        db = self.manager.db
        with db.session_ctx():
            lpost = datetime.now() - timedelta(hours=self.search_criteria.recent_hours)
            self.debug('RECENT HOURS {} {}'.format(self.search_criteria.recent_hours, lpost))
            lns = db.get_recent_labnumbers(lpost, ms)

            sams = [SampleRecordView(li.sample, labnumber=li.identifier, low_post=lpost)
                    for li in lns if li.sample]
            #ss = db.get_recent_samples(lpost, ms)
            #print ss
            #sams = [SampleRecordView(s)
            #        for s in ss]

        return sams

    def _filter_non_run_samples_changed(self):
        self._set_samples()

    def _configure_sample_table_fired(self):
        s = SampleTableConfigurer(adapter=self.sample_tabular_adapter,
                                  title='Configure Sample Table',
                                  parent=self)
        s.edit_traits()

    def _set_samples(self):
        db = self.manager.db
        sams = []
        with db.session_ctx():
            sp = self.selected_projects
            if not hasattr(sp, '__iter__'):
                sp = (sp,)

            for pp in sp:
                ss = db.get_samples(project=pp.name)

                test = lambda x: True
                if self.filter_non_run_samples:
                    def test(sa):
                        return any([len(li.analyses) for li in sa.labnumbers])

                def make_samples(sa):
                    return [SampleRecordView(sa, labnumber=ln.identifier)
                            for ln in sa.labnumbers]

                ss = [si for s in ss if test(s)
                      for si in make_samples(s)]
                sams.extend(ss)
        return sams
        #self.samples = sams
        #self.osamples = sams

    def _filter_func(self, new, attr=None, comp=None):
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
                return getattr(x, comp_key)(new)

        return func

    def _project_filter_changed(self, new):
        self.projects = filter(self._filter_func(new, 'name'), self.oprojects)

    def _sample_filter_changed(self, new):
        name = self._get_sample_filter_parameter()
        #comp=self.sample_filter_comparator
        self.samples = filter(self._filter_func(new, name), self.osamples)

    def _get_sample_filter_parameter(self):
        p = self.sample_filter_parameter
        if p == 'Sample':
            p = 'name'

        return p.lower()

    def _sample_filter_parameter_changed(self, new):
        if new:
            vs = []
            p = self._get_sample_filter_parameter()
            for si in self.osamples:
                v = getattr(si, p)
                if not v in vs:
                    vs.append(v)

            self.sample_filter_values = vs

    def _clear_selection_button_fired(self):
        self.selected_projects = []
        self.selected_samples = []

    def _get_sample_analyses(self, samples,
                             # limit=500,
                             # page=None, page_width=None,
                             include_invalid=False):
        db = self.manager.db
        with db.session_ctx():
            lns = [si.labnumber for si in samples]
            lps=[si.low_post for si in samples if si.low_post is not None]

            low_post=min(lps) if lps else None

            # o = None
            # if page_width:
            #     if page>0:
            #         page-=1
            #     o = page * page_width
            #     limit = page_width

            ans, tc = db.get_labnumber_analyses(lns,
                                                low_post=low_post,
                                                # limit=limit,
                                                # offset=o,
                                                include_invalid=include_invalid)
            prog=None
            n=len(ans)
            if n>25 or len(lns)>2:
                prog=self.manager.open_progress(n)

            ans = [self._record_view_factory(a, progress=prog) for a in ans]
            if prog:
                prog.close()

            # if page_width:
            #     return ans, tc
            # else:
            return ans

    def _record_view_factory(self, ai, progress=None, **kw):

        iso = IsotopeRecordView(**kw)
        iso.create(ai)
        if progress:
            progress.change_message('Loading {}'.format(iso.record_id))

        return iso

#============= EOF =============================================
