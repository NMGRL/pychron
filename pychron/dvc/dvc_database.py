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
from traits.api import HasTraits, Str, List
from traitsui.api import View, Item
# ============= standard library imports ========================
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.functions import count
from sqlalchemy.util import OrderedSet
from datetime import timedelta, datetime
from sqlalchemy import not_, func, distinct, or_
# ============= local library imports  ==========================
from pychron.core.spell_correct import correct
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.core.query import compile_query, in_func
from pychron.dvc.dvc_orm import AnalysisTbl, ProjectTbl, MassSpectrometerTbl, \
    IrradiationTbl, LevelTbl, SampleTbl, \
    MaterialTbl, IrradiationPositionTbl, UserTbl, ExtractDeviceTbl, LoadTbl, \
    LoadHolderTbl, LoadPositionTbl, \
    MeasuredPositionTbl, ProductionTbl, VersionTbl, RepositoryAssociationTbl, \
    RepositoryTbl, AnalysisChangeTbl, \
    InterpretedAgeTbl, InterpretedAgeSetTbl, PrincipalInvestigatorTbl, SamplePrepWorkerTbl, SamplePrepSessionTbl, \
    SamplePrepStepTbl, SamplePrepImageTbl, RestrictedNameTbl
from pychron.pychron_constants import ALPHAS, alpha_to_int, NULL_STR


class NewMassSpectrometerView(HasTraits):
    name = Str
    kind = Str

    def traits_view(self):
        v = View(Item('name'),
                 Item('kind'),
                 buttons=['OK', 'Cancel'],
                 title='New Mass Spectrometer',
                 kind='livemodal')
        return v


class DVCDatabase(DatabaseAdapter):
    """
    mysql2sqlite
    https://gist.github.com/esperlu/943776


    update local database
    when pushing
    1. pull remote database file and merge with local
       a. pull remote to path.remote (rsync remote path.remote)
       b. create merged database at path.merge
       c. rsync path.merge path
    2. push local to remote
       a. rsync lpath remote


    """

    # test_func = 'get_database_version'

    irradiation = Str
    irradiations = List
    level = Str
    levels = List

    def __init__(self, clear=False, auto_add=False, *args, **kw):
        super(DVCDatabase, self).__init__(*args, **kw)

        # self._bind_preferences()
        # if path is None:
        #     path = paths.meta_db

        # self.path = path

        # self.synced_path = '{}.sync'.format(paths.meta_db)
        # self.merge_path = '{}.merge'.format(paths.meta_db)
        # self.remote_path = '/var/pychronmeta.sqlite'

        # if clear and os.path.isfile(self.path):
        #     os.remove(self.path)

        # if not os.path.isfile(self.path):
        # self.create_all(Base.metadata)
        # self.connect()
        # else:
        # with self.session_ctx() as sess:
        # print sess
        # Base.metadata.init(sess.bind)
        if auto_add:
            if self.connect():
                with self.session_ctx():
                    if not self.get_mass_spectrometers():
                        if auto_add:
                            self.add_mass_spectrometer('Jan', 'ArgusVI')
                        else:
                            while 1:
                                self.information_dialog(
                                    'No Mass spectrometer in the database. Add one now')
                                nv = NewMassSpectrometerView(name='Jan',
                                                             kind='ArgusVI')
                                info = nv.edit_traits()
                                if info.result:
                                    self.add_mass_spectrometer(nv.name, nv.kind)
                                    break

                    if not self.get_users():
                        self.add_user('root')

    # def add_invalid_tag(self):
    #     return self._add_default_tag('invalid', True)
    #
    # def add_ok_tag(self):
    #     return self._add_default_tag('ok', False)
    #
    # def _add_default_tag(self, name, v):
    #     with self.session_ctx():
    #         tag = TagTbl(name=name,
    #                      omit_ideo=v,
    #                      omit_spec=v,
    #                      omit_iso=v,
    #                      omit_series=v)
    #         return self._add_item(tag)
    def check_restricted_name(self, name, category, check_principal_investigator=True):
        """
        return True is name is restricted

        """
        with self.session_ctx() as sess:
            q = sess.query(RestrictedNameTbl)
            q = q.filter(RestrictedNameTbl.name == name.upper())
            q = q.filter(RestrictedNameTbl.category == category)

            ret = bool(self._query_one(q))
            if check_principal_investigator:
                q = sess.query(PrincipalInvestigatorTbl)
                lname = func.lower(PrincipalInvestigatorTbl.name)
                name = name.lower()

                q = q.filter(func.substring(lname, 2) == name)
                q = q.filter(or_(lname == name))

                pret = bool(self._query_one(q))
                ret = pret or ret

            return ret

    def get_repository_analyses(self, repo):
        with self.session_ctx():
            r = self.get_repository(repo)
            return [a.analysis for a in r.repository_associations]

    def get_analysis_info(self, li):
        with self.session_ctx():
            dbpos = self.get_identifier(li)
            if not dbpos:
                self.warning('{} is not an identifier in the database'.format(li))
                return None
            else:
                project, sample, material, irradiation, level, pos = '', '', '', '', '', ''
                sample = dbpos.sample
                if sample:
                    if sample.project:
                        project = sample.project.name

                    if sample.material:
                        material = sample.material.name
                    sample = sample.name

                level = dbpos.level.name
                pos = dbpos.position
                irradiation = dbpos.level.irradiation.name
                # irradiation = '{} {}:{}'.format(level.irradiation.name,
                #                                 level.name, dbpos.position)

            return project, sample, material, irradiation, level, pos

    def set_analysis_tag(self, uuid, tagname):
        with self.session_ctx():
            an = self.get_analysis_uuid(uuid)
            change = an.change
            change.tag = tagname
            change.user = self.save_username

    def find_references(self, times, atypes, hours=10, exclude=None,
                        exclude_invalid=True):
        with self.session_ctx() as sess:
            # delta = 60 * 60 * hours  # seconds
            delta = timedelta(hours=hours)
            refs = OrderedSet()
            ex = None
            for ti in times:
                low = ti - delta
                high = ti + delta
                # rs = self.get_analyses_data_range(low, high, atypes, exclude=ex, exclude_uuids=exclude)
                rs = self.get_analyses_by_date_range(low, high,
                                                     analysis_type=atypes,
                                                     exclude=ex,
                                                     exclude_uuids=exclude,
                                                     exclude_invalid=exclude_invalid)
                refs.update(rs)
                ex = [r.id for r in refs]
                # print rs
                # print ti, low, high, rs, refs
            # print 'refs', refs
            return [rii for ri in refs for rii in ri.record_views]

    def get_blanks(self, ms=None, limit=100):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.filter(AnalysisTbl.analysis_type.like('blank%'))

            if ms:
                q = q.filter(func.lower(AnalysisTbl.mass_spectrometer) == ms.lower())
            q = q.order_by(AnalysisTbl.timestamp.desc())
            q = q.limit(limit)
            return self._query_all(q)

    def retrieve_blank(self, kind, ms, ed, last, repository):
        self.debug('retrieve blank. kind={}, ms={}, '
                   'ed={}, last={}, repository={}'.format(kind, ms, ed, last, repository))
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)

            if repository:
                q = q.join(RepositoryAssociationTbl)
                q = q.join(RepositoryTbl)

            if last:
                q = q.filter(AnalysisTbl.analysis_type == 'blank_{}'.format(kind))
            else:
                q = q.filter(AnalysisTbl.analysis_type.startswith('blank'))

            if ms:
                q = q.filter(func.lower(AnalysisTbl.mass_spectrometer) == ms.lower())

            if ed and ed not in ('Extract Device', NULL_STR) and kind == 'unknown':
                q = q.filter(func.lower(AnalysisTbl.extract_device) == ed.lower())

            if repository:
                q = q.filter(RepositoryTbl.name == repository)

            q = q.order_by(AnalysisTbl.timestamp.desc())
            return self._query_one(q, verbose_query=True)

    # def get_analyses_data_range(self, low, high, atypes, exclude=None, exclude_uuids=None):
    #     with self.session_ctx() as sess:
    #         q = sess.query(AnalysisTbl)
    #         q = q.filter(AnalysisTbl.timestamp >= low.strftime('%Y-%m-%d %H:%M:%S'))
    #         q = q.filter(AnalysisTbl.timestamp <= high.strftime('%Y-%m-%d %H:%M:%S'))
    #
    #         if isinstance(atypes, (list, tuple)):
    #             if len(atypes) == 1:
    #                 atypes = atypes[0]
    #
    #         if not isinstance(atypes, (list, tuple)):
    #             q = q.filter(AnalysisTbl.analysis_type == atypes)
    #         else:
    #             q = q.filter(AnalysisTbl.analysis_type.in_(atypes))
    #
    #         if exclude:
    #             q = q.filter(not_(AnalysisTbl.idanalysisTbl.in_(exclude)))
    #         if exclude_uuids:
    #             q = q.filter(not_(AnalysisTbl.uuid.in_(exclude_uuids)))
    #
    #         return self._query_all(q, verbose_query=False)

    def get_production_name(self, irrad, level):
        with self.session_ctx() as sess:
            dblevel = self.get_irradiation_level(irrad, level)
            # print dblevel, dblevel.productionID, dblevel.production, dblevel.idlevelTbl
            return dblevel.production.name

    def add_save_user(self):
        with self.session_ctx():
            if not self.get_user(self.save_username):
                obj = UserTbl(name=self.save_username)
                self._add_item(obj)

    # def add_tag(self, **kw):
    #     with self.session_ctx():
    #         obj = TagTbl(**kw)
    #         return self._add_item(obj)

    def add_production(self, name):
        with self.session_ctx():
            obj = ProductionTbl(name=name)
            return self._add_item(obj)

    def add_measured_position(self, position=None, load=None, **kw):
        with self.session_ctx():
            a = MeasuredPositionTbl(**kw)
            if position:
                a.position = position
            if load:
                a.loadName = load
            return self._add_item(a)

    def add_load_holder(self, name):
        with self.session_ctx():
            a = LoadHolderTbl(name=name)
            return self._add_item(a)

    def add_load(self, name, holder):
        with self.session_ctx():
            a = LoadTbl(name=name, holderName=holder)
            return self._add_item(a)

    def add_user(self, name, **kw):
        with self.session_ctx():
            a = UserTbl(name=name, **kw)
            return self._add_item(a)

    def add_analysis(self, **kw):
        with self.session_ctx():
            a = AnalysisTbl(**kw)
            return self._add_item(a)

    def add_analysis_change(self, **kw):
        with self.session_ctx():
            a = AnalysisChangeTbl(**kw)
            return self._add_item(a)

    def add_repository_association(self, reponame, analysis):
        with self.session_ctx():
            self.debug('add association {}'.format(reponame))
            repo = self.get_repository(reponame)
            if repo is not None:
                e = RepositoryAssociationTbl()
                e.repository = repo.name
                e.analysis = analysis
                return self._add_item(e)
            else:
                self.warning('No repository named ="{}"'.format(reponame))
                self.debug('adding to repo={} instead')

    def add_material(self, name, grainsize=None):
        with self.session_ctx():
            a = self.get_material(name)
            if a is None:
                a = MaterialTbl(name=name, grainsize=grainsize)
                a = self._add_item(a)
            return a

    def add_sample(self, name, project, material, grainsize=None):
        with self.session_ctx():
            a = self.get_sample(name, project, material, grainsize)
            if a is None:
                self.debug('Adding sample {},{},{}'.format(name, project, material))
                a = SampleTbl(name=name)
                a.project = self.get_project(project)
                a.material = self.get_material(material, grainsize)
                a = self._add_item(a)
            return a

    def add_extraction_device(self, name):
        with self.session_ctx():
            a = ExtractDeviceTbl(name=name)
            return self._add_item(a)

    def add_mass_spectrometer(self, name, kind='Argus'):
        with self.session_ctx():
            a = MassSpectrometerTbl(name=name, kind=kind)
            return self._add_item(a)

    def add_irradiation(self, name):
        with self.session_ctx():
            a = IrradiationTbl(name=name)
            return self._add_item(a)

    def add_irradiation_level(self, name, irradiation, holder, production_name,
                              z=0, note=''):
        with self.session_ctx():
            dblevel = self.get_irradiation_level(irradiation, name)
            if dblevel is None:

                irradiation = self.get_irradiation(irradiation)
                production = self.get_production(production_name)
                if not production:
                    production = self.add_production(production_name)

                a = LevelTbl(name=name,
                             irradiation=irradiation,
                             holder=holder,
                             z=z,
                             note=note)
                a.production = production
                dblevel = self._add_item(a)
            return dblevel

    def add_principal_investigator(self, name):
        pi = self.get_principal_investigator(name)
        if pi is None:
            pi = PrincipalInvestigatorTbl(name=name)
            pi = self._add_item(pi)
        return pi

    def add_project(self, name, pi=None):
        with self.session_ctx():
            a = self.get_project(name, pi)
            if a is None:
                self.debug('Adding project {} {}'.format(name, pi))
                a = ProjectTbl(name=name)
                if pi:
                    dbpi = self.get_principal_investigator(pi)
                    if dbpi:
                        a.principal_investigator = pi

                a = self._add_item(a)
            return a

    def add_irradiation_position(self, irrad, level, pos, identifier=None, **kw):
        with self.session_ctx():
            dbpos = self.get_irradiation_position(irrad, level, pos)
            if dbpos is None:
                self.debug('Adding irradiation position {}{} {}'.format(irrad, level, pos))
                a = IrradiationPositionTbl(position=pos, **kw)
                if identifier:
                    a.identifier = str(identifier)

                a.level = self.get_irradiation_level(irrad, level)
                dbpos = self._add_item(a)
            else:
                self.debug('Irradiation position exists {}{} {}'.format(irrad, level, pos))

            return dbpos

    def add_load_position(self, ln, position, weight=0, note=''):
        with self.session_ctx():
            a = LoadPositionTbl(identifier=ln, position=position, weight=weight,
                                note=note)
            return self._add_item(a)

    def add_repository(self, name, principal_investigator, **kw):
        with self.session_ctx():
            repo = self.get_repository(name)
            if repo:
                return repo

            principal_investigator = self.get_principal_investigator(principal_investigator)
            if not principal_investigator:
                principal_investigator = self.add_principal_investigator(principal_investigator)
                self.flush()

            a = RepositoryTbl(name=name, principal_investigator=principal_investigator.name, **kw)
            return self._add_item(a)

    def add_interpreted_age(self, **kw):
        with self.session_ctx():
            a = InterpretedAgeTbl(**kw)
            return self._add_item(a)

    def add_interpreted_age_set(self, interpreted_age, analysis, **kw):
        with self.session_ctx():
            a = InterpretedAgeSetTbl(**kw)
            a.interpreted_age = interpreted_age
            a.analysis = analysis
            return self._add_item(a)

    # special getters
    def get_flux_value(self, identifier, attr):
        j = 0
        with self.session_ctx():
            dbpos = self.get_identifier(identifier)
            if dbpos:
                j = getattr(dbpos, attr)
        return j

    def get_greatest_identifier(self, **kw):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl.identifier)
            q = q.order_by(IrradiationPositionTbl.identifier.desc())
            ret = self._query_first(q)
            return int(ret[0]) if ret else 0

    def get_last_nhours_analyses(self, n, return_limits=False,
                                 mass_spectrometers=None, analysis_types=None):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)

            hpost = datetime.now()
            lpost = hpost - timedelta(hours=n)
            self.debug('last nhours n={}, lpost={}, mass_spec={}'.format(n, lpost, mass_spectrometers))
            if mass_spectrometers:
                q = in_func(q, AnalysisTbl.mass_spectrometer, mass_spectrometers)

            if analysis_types:
                if hasattr(analysis_types, '__iter__'):
                    analysis_types = map(str.lower, analysis_types)
                else:
                    analysis_types = analysis_types.lower()

                q = in_func(q, AnalysisTbl.analysis_type, analysis_types)
                if 'blank' in analysis_types:
                    q = q.filter(AnalysisTbl.analysis_type.like('blank_%'))

            q = q.filter(AnalysisTbl.timestamp >= lpost)
            q = q.order_by(AnalysisTbl.timestamp.asc())
            ans = self._query_all(q)
            if return_limits:
                return ans, hpost, lpost

    def get_last_n_analyses(self, n):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.order_by(AnalysisTbl.timestamp.asc())
            q = q.limit(n)
            return self._query_all(q)

    def get_last_analysis(self, ln=None, aliquot=None, spectrometer=None,
                          hours_limit=None,
                          analysis_type=None):
        self.debug(
            'get last analysis labnumber={}, aliquot={}, spectrometer={}'.format(
                ln, aliquot, spectrometer))
        with self.session_ctx() as sess:
            if ln:
                ln = self.get_identifier(ln)
                if not ln:
                    return

            q = sess.query(AnalysisTbl)
            if ln:
                q = q.join(IrradiationPositionTbl)

            if spectrometer:
                q = q.filter(AnalysisTbl.mass_spectrometer == spectrometer)

            if ln:
                q = q.filter(IrradiationPositionTbl.identifier == ln)
                if aliquot:
                    q = q.filter(AnalysisTbl.aliquot == aliquot)

            if analysis_type:
                q = q.filter(AnalysisTbl.analysis_type == analysis_type)

            if hours_limit:
                lpost = datetime.now() - timedelta(hours=hours_limit)
                q = q.filter(AnalysisTbl.timestamp >= lpost)

            q = q.order_by(AnalysisTbl.timestamp.desc())
            q = q.limit(1)
            try:
                r = q.one()
                self.debug(
                    'got last analysis {}-{}'.format(r.labnumber.identifier,
                                                     r.aliquot))
                return r
            except NoResultFound, e:
                if ln:
                    name = ln.identifier
                elif spectrometer:
                    name = spectrometer

                if name:
                    self.debug('no analyses for {}'.format(name))
                else:
                    self.debug('no analyses for get_last_analysis')

                return 0

    def get_greatest_aliquot(self, identifier):
        with self.session_ctx() as sess:
            if identifier:
                if not self.get_identifier(identifier):
                    return

                q = sess.query(AnalysisTbl.aliquot)
                q = q.join(IrradiationPositionTbl)

                q = q.filter(IrradiationPositionTbl.identifier == identifier)
                q = q.order_by(AnalysisTbl.aliquot.desc())
                result = self._query_one(q, verbose_query=True)
                if result:
                    return int(result[0])

    def get_greatest_step(self, ln, aliquot):
        """
            return greatest step for this labnumber and aliquot.
            return step as an integer. A=0, B=1...
        """
        with self.session_ctx() as sess:
            if ln:
                dbln = self.get_identifier(ln)
                if not dbln:
                    return
                q = sess.query(AnalysisTbl.increment)
                q = q.join(IrradiationPositionTbl)

                q = q.filter(IrradiationPositionTbl.identifier == ln)
                q = q.filter(AnalysisTbl.aliquot == aliquot)
                # q = q.order_by(cast(meas_AnalysisTable.step, INTEGER(unsigned=True)).desc())
                q = q.order_by(AnalysisTbl.increment.desc())
                result = self._query_one(q)
                if result:
                    increment = result[0]
                    return increment if increment is not None else -1
                    # return ALPHAS.index(step) if step else -1

    def get_unique_analysis(self, ln, ai, step=None):
        #         sess = self.get_session()
        with self.session_ctx() as sess:
            try:
                ai = int(ai)
            except ValueError, e:
                self.debug('get_unique_analysis aliquot={}.  {}'.format(ai, e))
                return

            dbln = self.get_identifier(ln)
            if not dbln:
                self.debug('get_unique_analysis, no labnumber {}'.format(ln))
                return

            q = sess.query(AnalysisTbl)
            q = q.join(IrradiationPositionTbl)

            q = q.filter(IrradiationPositionTbl.identifier == ln)
            q = q.filter(AnalysisTbl.aliquot == int(ai))
            if step:
                if not isinstance(step, int):
                    step = alpha_to_int(step)

                q = q.filter(AnalysisTbl.increment == step)

            # q = q.limit(1)
            try:
                return q.one()
            except NoResultFound:
                return

    def get_labnumbers_startswith(self, partial_id, mass_spectrometers=None,
                                  filter_non_run=True, **kw):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            if mass_spectrometers or filter_non_run:
                q = q.join(AnalysisTbl)

            q = q.filter(IrradiationPositionTbl.identifier.like(
                '%{}%'.format(partial_id)))
            if mass_spectrometers:
                q = q.filter(
                    AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
            if filter_non_run:
                q = q.group_by(IrradiationPositionTbl.id)
                q = q.having(count(AnalysisTbl.id) > 0)

            return self._query_all(q, verbose_query=True)

    def get_associated_repositories(self, idn):
        with self.session_ctx() as sess:
            q = sess.query(distinct(RepositoryTbl.name),
                           IrradiationPositionTbl.identifier)
            q = q.join(RepositoryAssociationTbl, AnalysisTbl,
                       IrradiationPositionTbl)
            q = q.filter(IrradiationPositionTbl.identifier.in_(idn))
            q = q.order_by(IrradiationPositionTbl.identifier)

            return self._query_all(q, verbose_query=False)

    def get_analysis(self, value):
        return self._retrieve_item(AnalysisTbl, value, key='id')

    def get_analysis_uuid(self, value):
        return self._retrieve_item(AnalysisTbl, value, key='uuid')

    def get_analyses_uuid(self, uuids):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.filter(AnalysisTbl.uuid.in_(uuids))
            return self._query_all(q, verbose_query=False)

    def get_analysis_runid(self, idn, aliquot, step=None):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.join(IrradiationPositionTbl)
            if step:
                if isinstance(step, (str, unicode)):
                    step = ALPHAS.index(step)

                q = q.filter(AnalysisTbl.increment == step)
            if aliquot:
                q = q.filter(AnalysisTbl.aliquot == aliquot)

            q = q.filter(IrradiationPositionTbl.identifier == idn)
            return self._query_one(q)

    def get_analysis_by_attr(self, **kw):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            for k, v in kw.iteritems():
                try:
                    q = q.filter(getattr(AnalysisTbl, k) == v)
                except AttributeError:
                    self.debug('Invalid AnalysisTbl column {}'.format(k))
            q = q.order_by(AnalysisTbl.analysis_timestamp.desc())
            return self._query_first(q)

    def get_database_version(self, **kw):
        with self.session_ctx() as sess:
            # q = self._retrieve_item(VersionTbl, 'version', )
            q = sess.query(VersionTbl)
            v = self._query_one(q, **kw)
            return v.version

    def get_labnumber_analyses(self, lns,
                               low_post=None, high_post=None,
                               omit_key=None, exclude_uuids=None,
                               include_invalid=False,
                               mass_spectrometers=None,
                               repositories=None,
                               order='asc',
                               **kw):

        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.join(IrradiationPositionTbl)
            if omit_key or not include_invalid:
                q = q.join(AnalysisChangeTbl)

            if repositories:
                q = q.join(RepositoryAssociationTbl, RepositoryTbl)

            q = in_func(q, AnalysisTbl.mass_spectrometer, mass_spectrometers)
            q = in_func(q, RepositoryTbl.name, repositories)
            q = in_func(q, IrradiationPositionTbl.identifier, lns)

            # if mass_spectrometers:
            #     if not hasattr(mass_spectrometers, '__iter__'):
            #         mass_spectrometers = (mass_spectrometers,)
            #     q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
            #
            # if experiments:
            #     if not hasattr(experiments, '__iter__'):
            #         q = q.filter(ExperimentTbl.name == experiments)
            #     else:
            #         q = q.filter(ExperimentTbl.name.in_(experiments))
            # if not hasattr(lns, '__iter__'):
            #     lns = (lns,)
            # q = q.filter(IrradiationPositionTbl.identifier.in_(lns))

            if low_post:
                q = q.filter(AnalysisTbl.timestamp >= str(low_post))

            if high_post:
                q = q.filter(AnalysisTbl.timestamp <= str(high_post))

            if exclude_uuids:
                q = q.filter(not_(AnalysisTbl.uuid.in_(exclude_uuids)))

            if not include_invalid:
                q = q.filter(AnalysisChangeTbl.tag != 'invalid')

            if omit_key:
                q = q.filter(AnalysisChangeTbl.tag != omit_key)

            if order:
                q = q.order_by(getattr(AnalysisTbl.timestamp, order)())

            tc = q.count()
            return self._query_all(q), tc

    def get_repository_date_range(self, names):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl.timestamp)
            q = q.join(RepositoryAssociationTbl)
            q = q.filter(RepositoryAssociationTbl.repository.in_(names))
            return self._get_date_range(q)

    def get_project_date_range(self, names):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl.timestamp)
            q = q.join(IrradiationPositionTbl, SampleTbl, ProjectTbl)
            if names:
                q = q.filter(ProjectTbl.name.in_(names))

            return self._get_date_range(q)

    def get_analyses_by_date_range(self, lpost, hpost,
                                   labnumber=None,
                                   limit=None,
                                   analysis_type=None,
                                   mass_spectrometers=None,
                                   extract_device=None,
                                   project=None,
                                   repositories=None,
                                   order='asc',
                                   exclude=None,
                                   exclude_uuids=None,
                                   exclude_invalid=True,
                                   verbose=False):
        with self.session_ctx() as sess:
            sess.expire_on_commit = False
            q = sess.query(AnalysisTbl)
            if exclude_invalid:
                q = q.join(AnalysisChangeTbl)
            # q = self._analysis_query(sess, meas_MeasurementTable)
            if labnumber:
                q = q.join(IrradiationPositionTbl)
            # if mass_spectrometers:
            #     q = q.join(gen_MassSpectrometerTable)
            # if extract_device:
            #     q = q.join(meas_ExtractionTable, gen_ExtractionDeviceTable)
            # if analysis_type:
            #     q = q.join(gen_AnalysisTypeTable)
            if project:
                if not labnumber:
                    q = q.join(IrradiationPositionTbl)
                q = q.join(SampleTbl, ProjectTbl)

            if labnumber:
                q = q.filter(IrradiationPositionTbl.identifier == labnumber)
            if mass_spectrometers:
                if hasattr(mass_spectrometers, '__iter__'):
                    q = q.filter(
                        AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
                else:
                    q = q.filter(
                        AnalysisTbl.mass_spectrometer == mass_spectrometers)
            if extract_device:
                q = q.filter(AnalysisTbl.extract_device == extract_device)
            if analysis_type:
                q = in_func(q, AnalysisTbl.analysis_type, analysis_type)
            if project:
                q = q.filter(ProjectTbl.name == project)
            if lpost:
                q = q.filter(AnalysisTbl.timestamp >= lpost)
                # q = q.filter(self._get_post_filter(mi, '__ge__', cast=False))
            if hpost:
                q = q.filter(AnalysisTbl.timestamp <= hpost)

            if exclude_invalid:
                q = q.filter(AnalysisChangeTbl.tag != 'invalid')
            if exclude:
                q = q.filter(not_(AnalysisTbl.id.in_(exclude)))
            if exclude_uuids:
                q = q.filter(not_(AnalysisTbl.uuid.in_(exclude_uuids)))

            q = q.order_by(getattr(AnalysisTbl.timestamp, order)())
            if limit:
                q = q.limit(limit)

            return self._query_all(q, verbose_query=verbose)

    def _get_date_range(self, q, asc=None, desc=None, hours=0):
        if asc is None:
            asc = AnalysisTbl.timestamp.asc()
        if desc is None:
            desc = AnalysisTbl.timestamp.desc()
        return super(DVCDatabase, self)._get_date_range(q, asc, desc,
                                                        hours=hours)

    def get_project_labnumbers(self, project_names, filter_non_run,
                               low_post=None, high_post=None,
                               analysis_types=None, mass_spectrometers=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            q = q.join(SampleTbl, ProjectTbl)
            # filter_non_run = False
            if filter_non_run:
                if mass_spectrometers or analysis_types or low_post or high_post:
                    q = q.join(AnalysisTbl)

                if mass_spectrometers:
                    if not hasattr(mass_spectrometers, '__iter__'):
                        mass_spectrometers = (mass_spectrometers,)
                    q = q.filter(
                        AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))

                if analysis_types:
                    q = q.filter(AnalysisTbl.analysis_type.in_(analysis_types))
                    project_names.append('references')

                q = q.group_by(IrradiationPositionTbl.identifier)
                q = q.having(count(AnalysisTbl.id) > 0)
                if low_post:
                    q = q.filter(AnalysisTbl.timestamp >= str(low_post))
                if high_post:
                    q = q.filter(AnalysisTbl.timestamp <= str(high_post))

            if project_names:
                q = q.filter(ProjectTbl.name.in_(project_names))

            self.debug(compile_query(q))
            return self._query_all(q)

    # def get_experiment_labnumbers(self, expnames):
    #     with self.session_ctx() as sess:
    #         q = sess.query(distinct(IrradiationPositionTbl.idirradiationpositionTbl), IrradiationPositionTbl)
    #         q = q.join(AnalysisTbl, ExperimentAssociationTbl)
    #         q = q.filter(ExperimentAssociationTbl.experimentName.in_(expnames))
    #         return self._query_all(q)

    def get_level_names(self, irrad):
        with self.session_ctx():
            levels = self.get_irradiation_levels(irrad)
            if levels:
                return [l.name for l in levels]
            else:
                return []

    def get_irradiation_levels(self, irradname):
        with self.session_ctx() as sess:
            q = sess.query(LevelTbl)
            q = q.join(IrradiationTbl)
            q = q.filter(IrradiationTbl.name == irradname)
            q = q.order_by(LevelTbl.name.asc())
            return self._query_all(q)

    def get_labnumbers(self, principal_investigator=None,
                       projects=None, repositories=None,
                       mass_spectrometers=None,
                       irradiation=None, level=None,
                       analysis_types=None,
                       high_post=None,
                       low_post=None):

        self.debug('------- Get Labnumbers -------')
        self.debug('------- principal_investigator: {}'.format(principal_investigator))
        self.debug('------- projects: {}'.format(projects))
        self.debug('------- experiments: {}'.format(repositories))
        self.debug('------- mass_spectrometers: {}'.format(mass_spectrometers))
        self.debug('------- irradiation: {}'.format(irradiation))
        self.debug('------- level: {}'.format(level))
        self.debug('------- analysis_types: {}'.format(analysis_types))
        self.debug('------- high_post: {}'.format(high_post))
        self.debug('------- low_post: {}'.format(low_post))
        self.debug('------------------------------')

        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            q = q.distinct(IrradiationPositionTbl.id)

            # joins
            at = False
            if repositories:
                at = True
                q = q.join(AnalysisTbl, RepositoryAssociationTbl, RepositoryTbl)

            if principal_investigator:
                q = q.join(PrincipalInvestigatorTbl)

            if projects:
                q = q.join(SampleTbl, ProjectTbl)

            if mass_spectrometers and not at:
                at = True
                q = q.join(AnalysisTbl)

            if (low_post or high_post) and not at:
                at = True
                q = q.join(AnalysisTbl)

            if analysis_types and not at:
                at = True
                q = q.join(AnalysisTbl)

            if irradiation:
                if not at:
                    q = q.join(AnalysisTbl)
                q = q.join(LevelTbl, IrradiationTbl)

            # filters
            if repositories:
                q = q.filter(RepositoryTbl.name.in_(repositories))
            if principal_investigator:
                q = q.filter(PrincipalInvestigatorTbl.name == principal_investigator)
            if projects:
                q = q.filter(ProjectTbl.name.in_(projects))
            if mass_spectrometers:
                q = q.filter(
                    AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
            if low_post:
                q = q.filter(AnalysisTbl.timestamp >= low_post)
            if high_post:
                q = q.filter(AnalysisTbl.timestamp <= high_post)
            if analysis_types:
                if 'blank' in analysis_types:
                    analysis_types.remove('blank')
                    q = q.filter(
                        or_(AnalysisTbl.analysis_type.startswith('blank'),
                            AnalysisTbl.analysis_type.in_(analysis_types)))
                else:
                    q = q.filter(AnalysisTbl.analysis_type.in_(analysis_types))
            if irradiation:
                q = q.filter(IrradiationTbl.name == irradiation)
                q = q.filter(LevelTbl.name == level)

            return self._query_all(q, verbose_query=True)

    def get_analysis_groups(self, **kw):
        return []

    # single getters
    def get_user(self, name):
        return self._retrieve_item(UserTbl, name)

    def get_extraction_device(self, name):
        return self._retrieve_item(ExtractDeviceTbl, name)

    def get_mass_spectrometer(self, name):
        return self._retrieve_item(MassSpectrometerTbl, name)

    def get_repository(self, name):
        return self._retrieve_item(RepositoryTbl, name)

    def get_load_position(self, loadname, pos):
        with self.session_ctx() as sess:
            q = sess.query(LoadPositionTbl)
            q = q.join(LoadTbl)
            q = q.filter(LoadTbl.name == loadname)
            q = q.filter(LoadPositionTbl.position == pos)
            return self._query_one(q)

    def get_load_holder(self, name):
        return self._retrieve_item(LoadHolderTbl, name)

    def get_loadtable(self, name=None):
        if name is not None:
            lt = self._retrieve_item(LoadTbl, name)
        else:
            with self.session_ctx() as s:
                q = s.query(LoadTbl)
                q = q.order_by(LoadTbl.create_date.desc())
                lt = self._query_first(q)

        return lt

    def get_identifier(self, identifier):
        return self._retrieve_item(IrradiationPositionTbl, identifier,
                                   key='identifier')

    def get_irradiation_position(self, irrad, level, pos):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            q = q.join(LevelTbl, IrradiationTbl)
            q = q.filter(IrradiationTbl.name == irrad)
            q = q.filter(LevelTbl.name == level)
            q = q.filter(IrradiationPositionTbl.position == pos)

        return self._query_one(q)

    def get_production(self, name):
        return self._retrieve_item(ProductionTbl, name)

    def get_project(self, name, pi=None):
        if pi:
            with self.session_ctx() as sess:

                q = sess.query(ProjectTbl)
                q = q.join(PrincipalInvestigatorTbl)
                q = q.filter(ProjectTbl.name == name)

                if pi:
                    pi = self.get_principal_investigator(pi)
                q = q.filter(PrincipalInvestigatorTbl.name == pi.name)
                return self._query_one(q)
        else:
            return self._retrieve_item(ProjectTbl, name)

    def get_principal_investigator(self, name):
        return self._retrieve_item(PrincipalInvestigatorTbl, name)

    def get_irradiation_level(self, irrad, name):
        with self.session_ctx() as sess:
            irrad = self.get_irradiation(irrad)
            if irrad:
                q = sess.query(LevelTbl)
                q = q.filter(LevelTbl.irradiationID == irrad.id)
                q = q.filter(LevelTbl.name == name)
                return self._query_one(q)

    def get_irradiation(self, name):
        return self._retrieve_item(IrradiationTbl, name)

    def get_material(self, name, grainsize=None):
        if not isinstance(name, str) and not isinstance(name, unicode):
            return name

        with self.session_ctx() as sess:
            q = sess.query(MaterialTbl)
            q = q.filter(MaterialTbl.name == name)
            if grainsize:
                q = q.filter(MaterialTbl.grainsize == grainsize)
            return self._query_one(q)

    def get_sample(self, name, project, material, grainsize=None):
        with self.session_ctx() as sess:
            q = sess.query(SampleTbl)
            q = q.join(ProjectTbl)

            project = self.get_project(project)
            material = self.get_material(material, grainsize)

            q = q.filter(SampleTbl.project == project)
            q = q.filter(SampleTbl.material == material)
            q = q.filter(SampleTbl.name == name)

            return self._query_one(q, verbose_query=True)

    def get_last_identifier(self, sample=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            if sample:
                q = q.join(SampleTbl)
                q = q.filter(SampleTbl.name == sample)

            q = q.order_by(func.abs(IrradiationPositionTbl.identifier).desc())
            return self._query_first(q)

    def get_latest_load(self):
        return self._retrieve_first(LoadTbl,
                                    order_by=LoadTbl.create_date.desc())

    # similar getters

    def get_similar_pi(self, name):
        name = name.lower()
        with self.session_ctx() as sess:
            q = sess.query(PrincipalInvestigatorTbl)
            attr = func.lower(PrincipalInvestigatorTbl.name)
            return self._get_similar(name, attr, q)

    def get_similar_material(self, name):
        name = name.lower()
        with self.session_ctx() as sess:
            q = sess.query(MaterialTbl)
            attr = func.lower(MaterialTbl.name)
            return self._get_similar(name, attr, q)

    def get_similar_project(self, name, pi):
        name = name.lower()
        with self.session_ctx() as sess:
            q = sess.query(ProjectTbl)
            q = q.join(PrincipalInvestigatorTbl)
            q = q.filter(PrincipalInvestigatorTbl.name == pi)

            attr = func.lower(ProjectTbl.name)
            return self._get_similar(name, attr, q)

    def _get_similar(self, name, attr, q):
        f = or_(attr == name,
                attr.like('{}%{}'.format(name[0], name[-1])))
        q = q.filter(f)
        items = self._query_all(q)
        if len(items) > 1:
            # get the most likely name
            obj = self.get_principal_investigator(correct(name, [i.name for i in items]))
            return obj
        elif items:
            return items[0]

    # multi getters
    def get_analyses(self, analysis_type=None, mass_spectrometer=None,
                     reverse_order=False):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            if mass_spectrometer:
                q = q.filter(AnalysisTbl.mass_spectrometer == mass_spectrometer)
            if analysis_type:
                q = q.filter(AnalysisTbl.analysis_type == analysis_type)

            q = q.order_by(getattr(AnalysisTbl.timestamp,
                                   'desc' if reverse_order else 'asc')())
            return self._query_all(q)

    def get_analysis_types(self):
        return []

    # def get_load_holders(self):
    #     with self.session_ctx():
    #         return [ni.name for ni in self._retrieve_items(LoadHolderTbl)]
    def get_measured_positions(self, loadname, pos):
        with self.session_ctx() as sess:
            q = sess.query(MeasuredPositionTbl)
            q = q.filter(MeasuredPositionTbl.loadName == loadname)
            q = q.filter(MeasuredPositionTbl.position == pos)
            return self._query_all(q)

    def get_last_identifiers(self, sample=None, limit=1000, excludes=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            if sample:
                q = q.join(SampleTbl)
                q = q.filter(SampleTbl.name == sample)
                if excludes:
                    q = q.filter(not_(SampleTbl.name.in_(excludes)))
            elif excludes:
                q = q.join(SampleTbl)
                q = q.filter(not_(SampleTbl.name.in_(excludes)))
            q = q.filter(IrradiationPositionTbl.identifier.isnot(None))
            q = q.order_by(func.abs(IrradiationPositionTbl.identifier).desc())
            q = q.limit(limit)
            return [ni.identifier for ni in
                    self._query_all(q, verbose_query=True)]

    def get_loads(self, names=None, exclude_archived=True, **kw):
        with self.session_ctx():
            if 'order' not in kw:
                kw['order'] = LoadTbl.create_date.desc()

            if exclude_archived:
                kw = self._append_filters(not_(LoadTbl.archived), kw)

            if names:
                kw = self._append_filters(LoadTbl.name.in_(names), kw)

            loads = self._retrieve_items(LoadTbl, **kw)
            if loads:
                return [ui.name for ui in loads]

    def get_extraction_devices(self):
        return self.get_extract_devices()

    def get_extraction_device_names(self):
        names = []
        with self.session_ctx():
            eds = self.get_extract_devices()
            if eds:
                names = [e.name for e in eds]
        return names

    def get_users(self):
        return self._retrieve_items(UserTbl)

    def get_usernames(self):
        return self._get_table_names(UserTbl)

    def get_project_names(self):
        return self._get_table_names(ProjectTbl, use_distinct=ProjectTbl.name)

    def get_material_names(self):
        return self._get_table_names(MaterialTbl, use_distinct=MaterialTbl.name)

    def get_project_pnames(self):
        with self.session_ctx() as sess:
            q = sess.query(ProjectTbl)
            ms = self._query_all(q)
            return [mi.gname for mi in ms]

    def get_material_gnames(self):
        with self.session_ctx() as sess:
            q = sess.query(MaterialTbl)
            ms = self._query_all(q)
            return [mi.gname for mi in ms]

    def get_principal_investigator_names(self, *args, **kw):
        return self._get_table_names(PrincipalInvestigatorTbl)

    def get_principal_investigators(self, order=None, **kw):
        if order:
            order = getattr(PrincipalInvestigatorTbl.name, order)()

        return self._retrieve_items(PrincipalInvestigatorTbl, order=order, **kw)

    def get_grainsizes(self):
        with self.session_ctx() as sess:
            q = sess.query(distinct(MaterialTbl.grainsize))
            gs = self._query_all(q)
            return [g[0] for g in gs if g[0]]

    def get_sample_id(self, id):
        return self._retrieve_item(SampleTbl, id, key='id')

    def get_samples_by_name(self, name):
        with self.session_ctx() as sess:
            q = sess.query(SampleTbl)
            q = q.filter(SampleTbl.name.like('%{}%'.format(name)))
            return self._query_all(q, verbose_query=True)

    def get_samples(self, project=None, **kw):
        if project:
            if hasattr(project, '__iter__'):
                kw = self._append_filters(ProjectTbl.name.in_(project), kw)
            else:
                kw = self._append_filters(ProjectTbl.name == project, kw)
            kw = self._append_joins(ProjectTbl, kw)
        return self._retrieve_items(SampleTbl, verbose_query=False, **kw)

    def get_irradiations_by_repositories(self, repositories):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationTbl)
            q = q.join(LevelTbl, IrradiationPositionTbl, AnalysisTbl,
                       RepositoryAssociationTbl, RepositoryTbl)

            q = in_func(q, RepositoryTbl.name, repositories)
            return self._query_all(q)

    def get_level_identifiers(self, irrad, level):
        lns = []
        with self.session_ctx():
            level = self.get_irradiation_level(irrad, level)
            if level:
                lns = [str(pi.identifier).strip()
                       for pi in level.positions if pi.identifier]
                lns = [li for li in lns if li]
                lns = sorted(lns)
        return lns

    def get_irradiation_names(self, **kw):
        names = []
        with self.session_ctx():
            ns = self.get_irradiations(**kw)
            if ns:
                names = [i.name for i in ns]

        return names

    def get_irradiations(self, names=None, order_func='desc',
                         project_names=None,
                         mass_spectrometers=None, **kw):

        if names is not None:
            if hasattr(names, '__call__'):
                f = names(IrradiationTbl)
            else:
                f = (IrradiationTbl.name.in_(names),)
            kw = self._append_filters(f, kw)
        if project_names:
            kw = self._append_filters(ProjectTbl.name.in_(project_names), kw)
            kw = self._append_joins(
                (LevelTbl, IrradiationPositionTbl, SampleTbl), kw)

        if mass_spectrometers:
            kw = self._append_filters(
                AnalysisTbl.mass_spectrometer.name.in_(mass_spectrometers), kw)
            kw = self._append_joins(LevelTbl, IrradiationPositionTbl,
                                    AnalysisTbl, kw)

        order = None
        if order_func:
            order = getattr(IrradiationTbl.name, order_func)()

        return self._retrieve_items(IrradiationTbl, order=order, **kw)

    def get_projects(self, principal_investigator=None,
                     irradiation=None, level=None,
                     mass_spectrometers=None, order=None):

        if order:
            order = getattr(ProjectTbl.name, order)()

        if principal_investigator or irradiation or mass_spectrometers:
            with self.session_ctx() as sess:
                q = sess.query(ProjectTbl)

                # joins
                if principal_investigator:
                    q = q.join(PrincipalInvestigatorTbl)

                if irradiation:
                    q = q.join(SampleTbl, IrradiationPositionTbl)
                    if level:
                        q = q.join(LevelTbl)

                if mass_spectrometers:
                    q = q.join(SampleTbl, IrradiationPositionTbl, AnalysisTbl)

                # filters
                if principal_investigator:
                    q = q.filter(PrincipalInvestigatorTbl.name == principal_investigator)

                if irradiation:
                    if level:
                        q = q.filter(LevelTbl.name == level)
                    q = q.filter(IrradiationTbl.name == irradiation)

                if mass_spectrometers:
                    if not hasattr(mass_spectrometers, '__iter__'):
                        mass_spectrometers = (mass_spectrometers,)
                    q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))

                if order is not None:
                    q = q.order_by(order)

                ps = self._query_all(q)
        else:
            ps = self._retrieve_items(ProjectTbl, order=order)
        return ps

    # def get_tag(self, name):
    #     return self._retrieve_item(TagTbl, name)

    # def get_tags(self):
    #     return self._retrieve_items(TagTbl)

    def get_repositories(self):
        return self._retrieve_items(RepositoryTbl)

    def get_extract_devices(self):
        return self._retrieve_items(ExtractDeviceTbl)

    def get_mass_spectrometer_names(self):
        with self.session_ctx():
            ms = self.get_mass_spectrometers()
            return [mi.name for mi in ms]

    def get_mass_spectrometers(self):
        return self._retrieve_items(MassSpectrometerTbl)

    def get_repository_identifiers(self):
        return self._get_table_names(RepositoryTbl)

    def get_unknown_positions(self, *args, **kw):
        kw['invert'] = True
        return self._flux_positions(*args, **kw)

    def get_flux_monitors(self, *args, **kw):
        return self._flux_positions(*args, **kw)

    def _flux_positions(self, irradiation, level, sample, invert=False):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            q = q.join(LevelTbl, IrradiationTbl, SampleTbl)
            q = q.filter(IrradiationTbl.name == irradiation)
            q = q.filter(LevelTbl.name == level)
            if invert:
                q = q.filter(not_(SampleTbl.name == sample))
            else:
                q = q.filter(SampleTbl.name == sample)

            return self._query_all(q)

    def get_flux_monitor_analyses(self, irradiation, level, sample):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.join(IrradiationPositionTbl, LevelTbl, IrradiationTbl,
                       SampleTbl, AnalysisChangeTbl)
            # q = q.options(joinedload('experiment_associations'))
            # q = q.options(joinedload('irradiation_position'))
            q = q.filter(IrradiationTbl.name == irradiation)
            q = q.filter(LevelTbl.name == level)
            q = q.filter(SampleTbl.name == sample)
            q = q.filter(AnalysisChangeTbl.tag != 'invalid')
            # q = q.filter(not_(IrradiationPositionTbl.identifier.in_(('24061','24062', '24063', '24076'))))
            # q = q.filter(SampleTbl.name.in_(('BW-2014-3', 'BW-2014-4')))

            return self._query_all(q, verbose_query=True)

    def delete_tag(self, name):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl.id)
            q = q.join(AnalysisChangeTbl)
            q = q.filter(AnalysisChangeTbl.tag == name)
            n = q.count()
            if n:
                a = 'analyses' if n > 1 else 'analysis'

                if not self.confirmation_dialog(
                        'The Tag "{}" is applied to {} {}. '
                        'Are you sure to want to delete it?'.format(name, n,
                                                                    a)):
                    return

            self._delete_item(name, name='tag')
            return True

    # ============================================================
    # Sample Prep
    # ============================================================
    # with self.session_ctx():
    #     a = self.get_sample(name, project, material, grainsize)
    #     if a is None:
    #         self.debug('Adding sample {},{},{}'.format(name, project, material))
    #         a = SampleTbl(name=name)
    #         a.project = self.get_project(project)
    #         a.material = self.get_material(material, grainsize)
    #         a = self._add_item(a)
    #     return a
    def add_sample_prep_worker(self, name, fullname, email, phone, comment):
        with self.session_ctx():
            w = self.get_sample_prep_worker(name)
            if w is None:
                obj = SamplePrepWorkerTbl(name=name, fullname=fullname,
                                          email=email, phone=phone, comment=comment)
                self._add_item(obj)
                return True

    def update_sample_prep_session(self, name, worker, **kw):
        with self.session_ctx():
            s = self.get_sample_prep_session(name, worker)
            if s:
                for k, v in kw.iteritems():
                    setattr(s, k, v)

    def move_sample_to_session(self, current, sample, session, worker):
        with self.session_ctx() as sess:
            session = self.get_sample_prep_session(session, worker)
            q = sess.query(SamplePrepStepTbl)
            q = q.join(SamplePrepSessionTbl)
            q = q.join(SampleTbl)

            q = q.filter(SamplePrepSessionTbl.name == current)
            q = q.filter(SamplePrepSessionTbl.worker_name == worker)
            q = q.filter(SampleTbl.name == sample['name'])
            q = q.filter(MaterialTbl.name == sample['material'])
            q = q.filter(ProjectTbl.name == sample['project'])
            ss = self._query_all(q)
            for si in ss:
                si.sessionID = session.id



                # for s in samples:
                #     sample = self.get_sample()
                #

    def add_sample_prep_session(self, name, worker, comment):
        with self.session_ctx():
            s = self.get_sample_prep_session(name, worker)
            if s is None:
                obj = SamplePrepSessionTbl(name=name, worker_name=worker,
                                           comment=comment)
                self._add_item(obj)
                return True

    def add_sample_prep_step(self, sampleargs, worker, session, **kw):
        with self.session_ctx():
            sample = self.get_sample(*sampleargs)
            session = self.get_sample_prep_session(session, worker)
            obj = SamplePrepStepTbl(**kw)
            obj.sampleID = sample.id
            obj.sessionID = session.id
            self._add_item(obj)

    def add_sample_prep_image(self, stepid, host, path):
        with self.session_ctx():
            obj = SamplePrepImageTbl(host=host,
                                     path=path,
                                     stepID=stepid)
            self._add_item(obj)

    def get_sample_prep_samples(self, worker, session):
        with self.session_ctx() as sess:
            q = sess.query(SampleTbl)
            q = q.join(SamplePrepStepTbl)
            q = q.join(SamplePrepSessionTbl)
            q = q.filter(SamplePrepSessionTbl.name == session)
            q = q.filter(SamplePrepSessionTbl.worker_name == worker)
            return self._query_all(q)

    def get_sample_prep_step_by_id(self, id):
        return self._retrieve_item(SamplePrepStepTbl, id, 'id')

    def get_sample_prep_session(self, name, worker):
        return self._retrieve_item(SamplePrepSessionTbl, (name, worker), ('name', 'worker_name'))

    def get_sample_prep_worker(self, name):
        return self._retrieve_item(SamplePrepWorkerTbl, name)

    def get_sample_prep_worker_names(self):
        return self._get_table_names(SamplePrepWorkerTbl)

    def get_sample_prep_session_names(self, worker):
        with self.session_ctx() as sess:
            q = sess.query(SamplePrepSessionTbl.name)
            q = q.filter(SamplePrepSessionTbl.worker_name == worker)
            return [i[0] for i in self._query_all(q)]

    def get_sample_prep_sessions(self, sample):
        with self.session_ctx() as sess:
            q = sess.query(SamplePrepSessionTbl)
            q = q.join(SamplePrepStepTbl)
            q = q.join(SampleTbl)
            q = q.filter(SampleTbl.name == sample)
            return self._query_all(q)

    def get_sample_prep_steps(self, worker, session, sample, project, material, grainsize):
        with self.session_ctx() as sess:
            q = sess.query(SamplePrepStepTbl)
            q = q.join(SamplePrepSessionTbl)
            q = q.join(SampleTbl)
            q = q.join(ProjectTbl)
            q = q.join(MaterialTbl)

            q = q.filter(SamplePrepStepTbl.added.is_(None))
            q = q.filter(SamplePrepSessionTbl.worker_name == worker)
            q = q.filter(SamplePrepSessionTbl.name == session)
            q = q.filter(SampleTbl.name == sample)
            q = q.filter(ProjectTbl.name == project)
            q = q.filter(MaterialTbl.name == material)
            if grainsize:
                q = q.filter(MaterialTbl.grainsize == grainsize)

            return self._query_all(q)

    # private
    def _get_table_names(self, tbl, order='asc', use_distinct=False, **kw):
        with self.session_ctx():
            if order:
                order = getattr(tbl.name, order)()

            names = self._retrieve_items(tbl, order=order, distinct_=use_distinct, **kw)
            if use_distinct:
                return [ni[0] for ni in names]
            else:
                return [ni.name for ni in names or []]

# ============= EOF =============================================
