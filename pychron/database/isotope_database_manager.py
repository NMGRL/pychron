# ===============================================================================
# Copyright 2012 Jake Ross
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
from itertools import groupby

from traits.api import String, Property, Event, \
    cached_property, Any, Bool, Int
from apptools.preferences.preference_binding import bind_preference



#============= standard library imports ========================
import weakref
#============= local library imports  ==========================
from traits.has_traits import provides
from pychron.core.i_datastore import IDatastore
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.core.helpers.iterfuncs import partition
from pychron.core.ui.progress_dialog import myProgressDialog

from pychron.loggable import Loggable
from pychron.database.orms.isotope.meas import meas_AnalysisTable
from pychron.experiment.utilities.identifier import make_runid
from pychron.processing.analyses.dbanalysis import DBAnalysis
from pychron.processing.analyses.vcs_analysis import VCSAnalysis


ANALYSIS_CACHE = {}
ANALYSIS_CACHE_COUNT = {}
CACHE_LIMIT = 1000


class CancelLoadingError(BaseException):
    pass


@provides(IDatastore)
class BaseIsotopeDatabaseManager(Loggable):
    db = Any
    _db_klass = Any
    datasource_url = Property
    precedence = Int(0)

    def __init__(self, bind=True, connect=True, warn=True, *args, **kw):
        super(BaseIsotopeDatabaseManager, self).__init__(*args, **kw)

        if bind:
            try:
                self.bind_preferences()
            except AttributeError:
                import traceback

                traceback.print_exc()

        if connect:
            self.db.connect(warn=warn)

    #IDatastore protocol
    def get_greatest_aliquot(self, identifier):
        ret = 0
        if self.db:
            ret = self.db.get_greatest_aliquot(identifier)
        return ret

    def get_greatest_step(self, identifier, aliquot):
        ret = 0
        if self.db:
            ret = self.db.get_greatest_step(identifier, aliquot)
        return ret

    def connect(self, *args, **kw):
        if self.db:
            return self.db.connect(*args, **kw)

    def is_connected(self):
        if self.db:
            return self.db.connected

    def load(self):
        self.populate_default_tables()
        return True

    def populate_default_tables(self, db=None):
        self.debug('populating default tables')
        if db is None:
            db = self.db

        if db:
            if db.connect(force=False):
                from pychron.database.defaults import load_isotopedb_defaults

                load_isotopedb_defaults(db)
                self.debug('defaults finished')
                return True

    def verify_database_connection(self, inform=True):
        if self.db is not None:
            if self.db.connect(force=True):
                return True
                #                 self.db.flush()
                #                 self.db.reset()
        elif inform:
            self.warning_dialog('Not Database available')

    def bind_preferences(self):
        if self.db is None:
            self.db = self._db_factory()

        prefid = 'pychron.database'
        bind_preference(self.db, 'kind', '{}.kind'.format(prefid))
        if self.db.kind == 'mysql':
            bind_preference(self.db, 'host', '{}.host'.format(prefid))
            bind_preference(self.db, 'username', '{}.username'.format(prefid))
            bind_preference(self.db, 'password', '{}.password'.format(prefid))

        bind_preference(self.db, 'name', '{}.db_name'.format(prefid))
        bind_preference(self.db, 'save_username', '{}.save_username'.format(prefid))

    def open_progress(self, n=2, **kw):
        return self._open_progress(n, **kw)

    def _open_progress(self, n, close_at_end=True):

        pd = myProgressDialog(max=n - 1,
                              #dialog_size=(0,0, 550, 15),
                              close_at_end=close_at_end,
                              can_cancel=True,
                              can_ok=True)
        pd.open()
        # pd.on_trait_change(self._progress_closed, 'closed')
        return pd

    def _progress_closed(self):
        if self.application:
            win = self.application.windows[-1]
            win.activate()

    def _db_factory(self):
        db = self._db_klass(application=self.application)
        return db

    def _get_datasource_url(self):
        if self.db:
            return self.db.datasource_url

    #===============================================================================
    # defaults
    #===============================================================================
    def _db_default(self):
        return self._db_factory()


class IsotopeDatabaseManager(BaseIsotopeDatabaseManager):
    _db_klass = IsotopeAdapter

    irradiation = String
    level = String

    irradiations = Property(depends_on='saved, updated')
    levels = Property(depends_on='irradiation, saved, updated')

    saved = Event
    updated = Event

    use_vcs = Bool
    use_offline_database = Bool
    vcs = Any
    offline_bridge = Any

    def bind_preferences(self):
        super(IsotopeDatabaseManager, self).bind_preferences()

        prefid = 'pychron.vcs'
        bind_preference(self, 'use_vcs', '{}.use_vcs'.format(prefid))
        self._use_vcs_changed()

        prefid = 'pychron.offline'
        bind_preference(self, 'use_offline_database', '{}.use_offline_database'.format(prefid))
        self._use_offline_database_changed()

    def _use_offline_database_changed(self):
        if self.use_offline_database:
            from pychron.database.offline_bridge import OfflineBridge

            if not self.offline_bridge:
                self.offline_bridge = OfflineBridge()
                self.offline_bridge.init()

    def _use_vcs_changed(self):
        if self.use_vcs:
            from pychron.processing.vcs_data.vcs_manager import IsotopeVCSManager

            if not self.vcs:
                self.vcs = IsotopeVCSManager()

    def progress_loader(self, xs, func, threshold=50, progress=None, reraise_cancel=False):

        def gen(prog):
            n = len(xs)
            if n > threshold or prog:
                if not prog:
                    prog = self.open_progress(n)

                for i, x in enumerate(xs):
                    if prog.canceled:
                        raise CancelLoadingError
                    elif prog.accepted:
                        break
                    yield func(x, prog, i, n)
            else:
                for x in xs:
                    yield func(x, None, 0, 0)

        try:
            return list(gen(progress))
        except CancelLoadingError:
            if reraise_cancel:
                raise CancelLoadingError
            else:
                return []

    def update_vcs_analysis(self, an, msg):
        if self.use_vcs:
            self.vcs.update_analysis(an, msg)

    def update_vcs_analyses(self, ans, msg):
        if self.use_vcs:
            self.vcs.update_analyses(ans, msg)

    def filter_analysis_tag(self, ans, exclude):
        if not isinstance(exclude, (list, tuple)):
            exclude = (exclude,)

        return filter(lambda x: not x.tag in exclude, ans)

    def load_raw_data(self, ai):
        if not ai.has_raw_data:
            db = self.db
            with db.session_ctx():
                dban = db.get_analysis_uuid(ai.uuid)
                for dbiso in dban.isotopes:
                    name = dbiso.molecular_weight.name
                    try:
                        iso = ai.isotopes[name]
                        blob = dbiso.signal.data
                        if dbiso.kind == 'signal':
                            iso.unpack_data(blob)
                        elif dbiso.kind == 'baseline':
                            iso.baseline.unpack_data(blob)
                        elif dbiso.kind == 'sniff':
                            iso.sniff.unpack_data(blob)
                    except KeyError:
                        self.debug('load_raw_data: no matching isotope for {}, {}'.format(name,
                                                                                          ','.join(ai.isotope_keys)))

                # !!using db.get_analysis_isotopes is extremely slow!! why is unknown

                # dbisos = db.get_analysis_isotopes(ai.uuid)
                # isos = ai.isotopes
                # for dban, dbiso, dbmw in dbisos:
                # name = dbmw.name
                #     if name in isos:
                #         blob = dbiso.signal.data
                #         iso = isos[name]
                #         if dbiso.kind == 'signal':
                #             iso.unpack_data(blob)
                #         elif dbiso.kind == 'baseline':
                #             iso.baseline.unpack_data(blob)
                #         elif dbiso.kind == 'sniff':
                #             iso.sniff.unpack_data(blob)

                ai.has_raw_data = True

    def make_analysis(self, ai, **kw):
        return self.make_analyses((ai,), **kw)[0]

    def _calculate_cached_ages(self, ans, calculate_age):
        if calculate_age and ans:
            self.debug('calculated cached analysis ages')
            for ca in ans:
                ca.calculate_age()

    def _unpack_cached_analyses(self, ans, calculate_age):
        no_db_ans = []
        db_ans = []
        for ca in ans:
            if not ca.has_raw_data:
                print ca.record_id, 'no rawasffas'
                no_db_ans.append(ca)
            else:
                if calculate_age:
                    ca.calculate_age()
                db_ans.append(ca)
        return db_ans, no_db_ans

    def _increment_cache(self, cached_ans, use_cache):
        if use_cache:
            for ci in cached_ans:
                self._add_to_cache(ci)

    def _clone_vcs_repos(self, no_db_ans):
        if self.use_vcs:
            #clone the necessary project repositories
            def f(x):
                try:
                    return x.labnumber.sample.project.name
                except AttributeError:
                    pass

            prs = filter(lambda x: not x is None, (f(ai) for ai in no_db_ans))
            self.vcs.clone_project_repos(prs)

    def _setup_progress(self, n, progress, use_progress):
        if n > 1:
            if progress is not None:
                if progress.max < (n + progress.get_value()):
                    progress.increase_max(n + 2)
            elif use_progress:
                progress = self._open_progress(n + 2)
        return progress

    def make_analyses(self, ans,
                      progress=None,
                      use_progress=True,
                      exclude=None,
                      use_cache=True,
                      unpack=False,
                      calculate_age=False,
                      **kw):
        """
            loading the analysis' signals appears to be the most expensive operation.
            the majority of the load time is in _construct_analysis
        """
        if exclude:
            ans = self.filter_analysis_tag(ans, exclude)

        if not ans:
            self.debug('no analyses to load')
            return []

        db = self.db
        with db.session_ctx():
            # partition into DBAnalysis vs IsotopeRecordView
            db_ans, no_db_ans = map(list, partition(ans, lambda x: isinstance(x, DBAnalysis)))
            self._calculate_cached_ages(db_ans, calculate_age)

            if unpack:
                for di in db_ans:
                    if not di.has_raw_data:
                        no_db_ans.append(di)
                        db_ans.remove(di)

            if no_db_ans:
                if use_cache:
                    # partition into cached and non cached analyses
                    cached_ans, no_db_ans = partition(no_db_ans,
                                                      lambda x: x.uuid in ANALYSIS_CACHE)
                    cached_ans = list(cached_ans)
                    no_db_ans = list(no_db_ans)

                    cns = [ANALYSIS_CACHE[ci.uuid] for ci in cached_ans]

                    # if unpack is true make sure cached analyses have raw data
                    if unpack:
                        a, b = self._unpack_cached_analyses(cns, calculate_age)
                        db_ans.extend(a)
                        no_db_ans.extend(b)
                    else:
                        self._calculate_cached_ages(cns, calculate_age)
                        #add analyses from cache to db_ans
                        db_ans.extend(cns)

                    # increment value in cache_count
                    self._increment_cache(cached_ans, use_cache)

                # load remaining analyses
                n = len(no_db_ans)
                if n:
                    self._clone_vcs_repos(no_db_ans)

                    progress = self._setup_progress(n, progress, use_progress)

                    db_ans, new_ans = self._construct_analyses(no_db_ans, db_ans, progress,
                                                               calculate_age, unpack, use_cache, **kw)
                    db_ans.extend(new_ans)

                    # self.debug('use vcs {}'.format(self.use_vcs))
                    # if self.use_vcs:
                    # if progress:
                    #         progress.increase_max(len(new_ans)+1)
                    #         progress.change_message('Adding analyses to vcs')
                    #
                    #     self.vcs.add_analyses(new_ans, progress=progress)

                    self.debug('use offline database {}'.format(self.use_offline_database))
                    if self.use_offline_database:
                        if progress:
                            progress.increase_max(len(new_ans) + 1)
                            progress.change_message('Transfering analyses for offline usage')
                        self.offline_bridge.add_analyses(db, new_ans, progress=progress)

            if progress:
                progress.soft_close()

            return db_ans

    def get_level(self, level, irradiation=None):
        if irradiation is None:
            irradiation = self.irradiation

        return self.db.get_irradiation_level(irradiation, level)

    def remove_from_cache(self, ans):
        if not isinstance(ans, (list, tuple)):
            ans = ans,

        for ai in ans:
            uuid = ai.uuid
            if uuid in ANALYSIS_CACHE:
                self.debug('remove {} from cache'.format(ai.record_id))
                ANALYSIS_CACHE.pop(uuid)
                ANALYSIS_CACHE_COUNT.pop(uuid)

    #===============================================================================
    # private
    #===============================================================================
    def _construct_analyses(self, no_db_ans, db_ans, progress, calculate_age, unpack, use_cache, **kw):
        uuids = [ri.uuid for ri in no_db_ans]

        #get all dbrecords with one call
        ms = self.db.get_analyses_uuid(uuids)
        construct = self._construct_analysis
        add_to_cache = self._add_to_cache

        key = lambda x: x[0]
        dbrecords = groupby(ms, key=key)

        def func(x, prog, i, n):
            _, gi = dbrecords.next()
            a = construct(x, gi, prog, unpack=unpack, calculate_age=calculate_age, **kw)
            if use_cache:
                add_to_cache(a)
            return a

        try:
            return db_ans, self.progress_loader(no_db_ans, func, progress=progress, reraise_cancel=True)
        except CancelLoadingError:
            return [], []

    def _construct_analysis(self, rec, group, prog, calculate_age=True, unpack=False, load_changes=False):
        atype = None
        if isinstance(rec, meas_AnalysisTable):
            rid = make_runid(rec.labnumber.identifier, rec.aliquot, rec.step)
            atype = rec.measurement.analysis_type.name
        elif hasattr(rec, 'record_id'):
            rid = rec.record_id
        else:
            rid = id(rec)

        graph_id = 0
        group_id = 0

        if hasattr(rec, 'group_id'):
            group_id = rec.group_id

        if hasattr(rec, 'graph_id'):
            graph_id = rec.graph_id

        if atype is None:
            atype = rec.analysis_type

        if prog:
            show_age = calculate_age and atype in ('unknown', 'cocktail')
            m = 'calculating age' if show_age else ''
            msg = 'loading {}. {}'.format(rid, m)
            prog.change_message(msg)

        klass = DBAnalysis if not self.use_vcs else VCSAnalysis
        ai = klass(group_id=group_id,
                   graph_id=graph_id)

        # if not self.use_vcs:
        ai.sync(group, unpack=unpack, load_changes=load_changes)
        # timethis(ai.sync, args=(group,),
        #          kwargs=dict(unpack=unpack, load_changes=load_changes))

        if atype in ('unknown', 'cocktail'):
            if calculate_age:
                # timethis(ai.sync, args=(meas_analysis, ),
                #          kwargs=dict(unpack=unpack, load_changes=load_changes))
                # timethis(ai.calculate_age, kwargs=dict(force=not self.use_vcs))
                ai.calculate_age(force=not self.use_vcs)
                # timethis(ai.sync, args=(meas_analysis,),
                #          kwargs=dict(unpack=unpack, load_changes=load_changes))
                # timethis(ai.calculate_age)

                # synced = True

        # if not synced:
        #     ai.sync(group, unpack=unpack, load_changes=load_changes)

        return ai

    def _add_to_cache(self, rec):
        if rec is None:
            self.debug('cannot add None to cache')

        if not rec.uuid in ANALYSIS_CACHE:
            #self.debug('Adding {} to cache'.format(rec.record_id))
            ANALYSIS_CACHE[rec.uuid] = weakref.ref(rec)()
            ANALYSIS_CACHE_COUNT[rec.uuid] = 1
        else:
            ANALYSIS_CACHE_COUNT[rec.uuid] += 1

        #remove items from cached based on frequency of use
        if len(ANALYSIS_CACHE) > CACHE_LIMIT:
            s = sorted(ANALYSIS_CACHE_COUNT.iteritems(), key=lambda x: x[1])
            k, v = s[0]
            ANALYSIS_CACHE.pop(k)
            ANALYSIS_CACHE_COUNT.pop(k)
            self.debug('Cache limit exceeded {}. removing {} n uses={}'.format(CACHE_LIMIT, k, v))

    #===============================================================================
    # property get/set
    #===============================================================================
    @cached_property
    def _get_irradiations(self):
        r = []
        db = self.db
        if db and db.connected:
            with db.session_ctx():
                r = [str(ri.name) for ri in db.get_irradiations()
                     if ri.name]

            if r and not self.irradiation:
                self.irradiation = r[0]

        return r

    @cached_property
    def _get_levels(self):
        r = []
        if self.db and self.db.connected:

            with self.db.session_ctx():
                irrad = self.db.get_irradiation(self.irradiation)
                if irrad:
                    r = sorted([str(ri.name) for ri in irrad.levels
                                if ri.name])
                    if r and not self.level:
                        self.level = r[0]

        return r

    #===============================================================================
    # handlers
    #===============================================================================
    def _irradiation_changed(self):
        self.level = ''


        #============= EOF =============================================
        # def _add_arar(self, meas_analysis, analysis):
        #
        #         db = self.db
        #         with db.session_ctx() as sess:
        #             hist = db.add_arar_history(meas_analysis)
        #             #a, e=age.nominal_value, age.std_dev
        #             d = dict()
        #             attrs = ['k39', 'ca37', 'cl36', 'rad40',
        #                      'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']
        #
        #             for a in attrs:
        #                 v = getattr(analysis, a)
        #                 ek = '{}_err'.format(a)
        #                 d[a] = float(v.nominal_value)
        #                 d[ek] = float(v.std_dev)
        #
        #             age_scalar = analysis.arar_constants.age_scalar
        #             d['age_err_wo_j'] = analysis.age_error_wo_j * age_scalar
        #
        #             age = analysis.age
        #             d['age'] = age.nominal_value * age_scalar
        #             d['age_err'] = age.std_dev * age_scalar
        #
        #             db.add_arar(hist, **d)
        #
        #             meas_analysis.selected_histories.selected_arar = hist
        #             sess.commit()
        #             #hist.selected=analysis.selected_histories
        #             #analysis.selected_histories.selected_arar=hist