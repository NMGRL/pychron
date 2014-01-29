#===============================================================================
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
from traits.api import String, Property, Event, \
    cached_property, Any, Bool
from apptools.preferences.preference_binding import bind_preference
#============= standard library imports ========================
import weakref
#============= local library imports  ==========================
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.core.helpers.iterfuncs import partition
from pychron.core.ui.progress_dialog import myProgressDialog

from pychron.processing.analyses.analysis import DBAnalysis, VCSAnalysis
from pychron.loggable import Loggable
from pychron.database.orms.isotope.meas import meas_AnalysisTable
from pychron.experiment.utilities.identifier import make_runid


ANALYSIS_CACHE = {}
ANALYSIS_CACHE_COUNT = {}
CACHE_LIMIT = 500


class BaseIsotopeDatabaseManager(Loggable):
    db = Any
    _db_klass = Any
    datasource_url = Property
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

    def isConnected(self):
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

    use_vcs=Bool
    use_offline_database=Bool
    vcs = Any
    offline_bridge=Any

    def bind_preferences(self):
        super(IsotopeDatabaseManager, self).bind_preferences()

        prefid='pychron.vcs'
        bind_preference(self, 'use_vcs', '{}.use_vcs'.format(prefid))
        self._use_vcs_changed()

        prefid = 'pychron.offline'
        bind_preference(self, 'use_offline_database', '{}.use_offline_database'.format(prefid))
        self._use_offline_database_changed()

    def _use_offline_database_changed(self):
        if self.use_offline_database:
            from pychron.database.offline_bridge import OfflineBridge
            if not self.offline_bridge:
                self.offline_bridge=OfflineBridge()
                self.offline_bridge.init()

    def _use_vcs_changed(self):
        if self.use_vcs:
            from pychron.processing.vcs_data.vcs_manager import IsotopeVCSManager
            if not self.vcs:
                self.vcs=IsotopeVCSManager()

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

    def make_analysis(self, ai, **kw):
        return self.make_analyses((ai,), **kw)[0]

    def make_analyses(self, ans,
                      progress=None,
                      exclude=None,
                      use_cache=True,
                      unpack=False,
                      **kw):
        """
            loading the analysis' signals appears to be the most expensive operation.
            the majority of the load time is in _construct_analysis
        """

        if exclude:
            ans = self.filter_analysis_tag(ans, exclude)

        if not ans:
            return []

        db=self.db
        with db.session_ctx():
            if ans:
                #partition into DBAnalysis vs IsotopeRecordView
                db_ans, no_db_ans = map(list, partition(ans, lambda x: isinstance(x, DBAnalysis)))

                if no_db_ans:
                    #partition into cached and non cached analyses
                    cached_ans, no_db_ans = partition(no_db_ans,
                                                      lambda x: x.uuid in ANALYSIS_CACHE)
                    cached_ans = list(cached_ans)
                    no_db_ans = list(no_db_ans)

                    #if unpack is true make sure cached analyses have raw data
                    if unpack:
                        for ci in cached_ans:
                            ca=ANALYSIS_CACHE[ci.uuid]
                            if not ca.has_raw_data:
                                print ca.record_id, 'no rawasffas'
                                no_db_ans.append(ci)
                            else:
                                db_ans.append(ca)
                    else:
                        #add analyses from cache to db_ans
                        db_ans.extend([ANALYSIS_CACHE[ci.uuid] for ci in cached_ans])

                    #increment value in cache_count
                    for ci in cached_ans:
                        self._add_to_cache(ci)

                    #load remaining analyses
                    n = len(no_db_ans)
                    if n:

                        if self.use_vcs:
                            #clone the necessary project repositories
                            def f(x):
                                try:
                                    return x.labnumber.sample.project.name
                                except AttributeError:
                                    pass
                            prs=filter(lambda x: not x is None, (f(ai) for ai in no_db_ans))
                            self.vcs.clone_project_repos(prs)

                        if n > 1:
                            if progress is not None:
                                if progress.max < (n + progress.get_value()):
                                    progress.increase_max(n+2)
                            else:
                                progress = self._open_progress(n+2)

                        new_ans=[]
                        for i, ai in enumerate(no_db_ans):
                            if progress:
                                if progress.canceled:
                                    self.debug('canceling make analyses')
                                    db_ans=[]
                                    new_ans=[]
                                    break
                                elif progress.accepted:
                                    self.debug('accepting {}/{} analyses'.format(i, n))
                                    break

                            a = self._construct_analysis(ai, progress, unpack=unpack, **kw)
                            if a:
                                if use_cache:
                                    self._add_to_cache(a)
                                new_ans.append(a)

                                # if progress:
                                #     progress.on_trait_change(self._progress_closed,
                                #                              'closed', remove=True)

                        db_ans.extend(new_ans)

                        # self.debug('use vcs {}'.format(self.use_vcs))
                        # if self.use_vcs:
                        #     if progress:
                        #         progress.increase_max(len(new_ans)+1)
                        #         progress.change_message('Adding analyses to vcs')
                        #
                        #     self.vcs.add_analyses(new_ans, progress=progress)

                        self.debug('use offline database {}'.format(self.use_offline_database))
                        if self.use_offline_database:
                            if progress:
                                progress.increase_max(len(new_ans)+1)
                                progress.change_message('Transfering analyses for offline usage')
                            self.offline_bridge.add_analyses(db, new_ans, progress=progress)

                if progress:
                    progress.soft_close()

                return db_ans

    def get_level(self, level, irradiation=None):
        if irradiation is None:
            irradiation = self.irradiation

        return self.db.get_irradiation_level(irradiation, level)

    def remove_from_cache(self, uuid):
        if uuid in ANALYSIS_CACHE:
            ANALYSIS_CACHE.pop(uuid)
            ANALYSIS_CACHE_COUNT.pop(uuid)
    #===============================================================================
    # private
    #===============================================================================
    def _add_to_cache(self, rec):
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

    def _construct_analysis(self, rec, prog, calculate_age=True, unpack=False, load_changes=False):
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

        meas_analysis = self.db.get_analysis_uuid(rec.uuid)

        klass=DBAnalysis if not self.use_vcs else VCSAnalysis
        ai = klass(group_id=group_id,
                   graph_id=graph_id)

        # if not self.use_vcs:
        synced=False
        if atype in ('unknown', 'cocktail'):
            if calculate_age:
                ai.sync(meas_analysis, unpack=unpack, load_changes=load_changes)
                ai.calculate_age(force=not self.use_vcs)
                synced=True

        if not synced:
            ai.sync(meas_analysis, unpack=unpack, load_changes=load_changes)

        return ai

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