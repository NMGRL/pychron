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
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy.sql.functions import count
from sqlalchemy.util import OrderedSet
from traits.api import HasTraits, Str, List
from traitsui.api import View, Item

# ============= standard library imports ========================
from datetime import timedelta, datetime
from sqlalchemy import not_, func, distinct, or_
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.core.query import compile_query
from pychron.dvc.dvc_orm import AnalysisTbl, ProjectTbl, MassSpectrometerTbl, IrradiationTbl, LevelTbl, SampleTbl, \
    MaterialTbl, IrradiationPositionTbl, UserTbl, ExtractDeviceTbl, LoadTbl, LoadHolderTbl, LoadPositionTbl, \
    MeasuredPositionTbl, ProductionTbl, VersionTbl, ExperimentAssociationTbl, ExperimentTbl, TagTbl, AnalysisChangeTbl, \
    InterpretedAgeTbl, InterpretedAgeSetTbl
from pychron.pychron_constants import ALPHAS, alpha_to_int


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

    def __init__(self, path=None, clear=False, auto_add=False, *args, **kw):
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
                                self.information_dialog('No Mass spectrometer in the database. Add one now')
                                nv = NewMassSpectrometerView(name='Jan', kind='ArgusVI')
                                info = nv.edit_traits()
                                if info.result:
                                    self.add_mass_spectrometer(nv.name, nv.kind)
                                    break

                    if not self.get_users():
                        self.add_user('root')

    def set_analysis_tag(self, uuid, tagname):
        with self.session_ctx():
            an = self.get_analysis_uuid(uuid)
            change = an.change
            change.tag = tagname
            change.user = self.save_username

    def find_references(self, times, atypes, hours=10, exclude=None):
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
                                                     analysis_type=atypes, exclude=ex, exclude_uuids=exclude)
                refs.update(rs)
                ex = [r.idanalysisTbl for r in refs]
                # print rs
                # print ti, low, high, rs, refs
            # print 'refs', refs
            return [ri.record_view for ri in refs]

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

    def add_tag(self, **kw):
        with self.session_ctx():
            obj = TagTbl(**kw)
            return self._add_item(obj)

    def add_production(self, name):
        with self.session_ctx():
            obj = ProductionTbl(name=name)
            return self._add_item(obj)

    def add_measured_position(self, position=None, load=None, **kw):
        a = MeasuredPositionTbl(**kw)
        if position:
            a.position = position
        if load:
            a.loadName = load
        return self._add_item(a)

    def add_load_holder(self, name):
        a = LoadHolderTbl(name=name)
        return self._add_item(a)

    def add_load(self, name, holder):
        a = LoadTbl(name=name, holderName=holder)
        return self._add_item(a)

    def add_user(self, name, **kw):
        a = UserTbl(name=name, **kw)
        return self._add_item(a)

    def add_analysis(self, **kw):
        a = AnalysisTbl(**kw)
        return self._add_item(a)

    def add_analysis_change(self, **kw):
        a = AnalysisChangeTbl(**kw)
        return self._add_item(a)

    def add_experiment_association(self, experiment, analysis):
        self.debug('add association {}'.format(experiment))
        experiment = self.get_experiment(experiment)
        e = ExperimentAssociationTbl()
        e.experiment = experiment
        e.analysis = analysis
        self._add_item(e)

    def add_material(self, name):
        a = self.get_material(name)
        if a is None:
            a = MaterialTbl(name=name)
            a = self._add_item(a)
        return a

    def add_sample(self, name, project, material):
        # self.debug('ADDING SAMPLE {},{},{}'.format(name,project,material))
        a = self.get_sample(name, project)
        if a is None:
            a = SampleTbl(name=name)
            a.project = self.get_project(project)
            a.material = self.get_material(material)
            a = self._add_item(a)
        # else:
        # self.debug('SAMPLE {},{} ALREADY EXISTS'.format(name,project))
        return a

    def add_mass_spectrometer(self, name, kind='Argus'):
        a = MassSpectrometerTbl(name=name, kind=kind)
        return self._add_item(a)

    def add_irradiation(self, name):
        a = IrradiationTbl(name=name)
        return self._add_item(a)

    def add_irradiation_level(self, name, irradiation, holder, production, z=0, note=''):
        irradiation = self.get_irradiation(irradiation)
        production = self.get_production(production)
        a = LevelTbl(name=name,
                     irradiation=irradiation,
                     holder=holder,
                     z=z,
                     note=note)
        a.production = production

        return self._add_item(a)

    def add_project(self, name):
        a = self.get_project(name)
        if a is None:
            a = ProjectTbl(name=name)
            a = self._add_item(a)
        return a

    def add_irradiation_position(self, irrad, level, pos):
        a = IrradiationPositionTbl(position=pos)
        a.level = self.get_irradiation_level(irrad, level)
        return self._add_item(a)

    def add_load_position(self, ln, position, weight=0, note=''):
        a = LoadPositionTbl(identifier=ln, position=position, weight=weight, note=note)
        return self._add_item(a)

    def add_experiment(self, name, creator_name, **kw):
        creator = self.get_user(creator_name)
        if not creator:
            creator = self.add_user(creator_name)
            self.flush()

        a = ExperimentTbl(name=name, creator=creator.name, **kw)
        return self._add_item(a)

    def add_interpreted_age(self, **kw):
        a = InterpretedAgeTbl(**kw)
        return self._add_item(a)

    def add_interpreted_age_set(self, interpreted_age, analysis, **kw):
        a = InterpretedAgeSetTbl(**kw)
        a.interpreted_age = interpreted_age
        a.analysis = analysis
        return self._add_item(a)

    # special getters
    def get_greatest_identifier(self, **kw):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl.identifier)
            q = q.order_by(IrradiationPositionTbl.identifier.desc())
            ret = self._query_first(q)
            return int(ret[0]) if ret else 0

    def get_last_analysis(self, ln=None, aliquot=None, spectrometer=None,
                          hours_limit=None,
                          analysis_type=None):
        self.debug('get last analysis labnumber={}, aliquot={}, spectrometer={}'.format(ln, aliquot, spectrometer))
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
                self.debug('got last analysis {}-{}'.format(r.labnumber.identifier, r.aliquot))
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
                ln = self.get_identifier(ln)
                if not ln:
                    return
                q = sess.query(AnalysisTbl.step)
                q = q.join(IrradiationPositionTbl)

                q = q.filter(IrradiationPositionTbl.identifier == ln)
                q = q.filter(AnalysisTbl.aliquot == aliquot)
                # q = q.order_by(cast(meas_AnalysisTable.step, INTEGER(unsigned=True)).desc())
                q = q.order_by(AnalysisTbl.increment.desc())
                result = self._query_one(q)
                if result:
                    step = result[0]
                    return ALPHAS.index(step) if step else -1

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

    def get_labnumbers_startswith(self, partial_id, mass_spectrometers=None, filter_non_run=True, **kw):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            if mass_spectrometers or filter_non_run:
                q = q.join(AnalysisTbl)

            q = q.filter(IrradiationPositionTbl.identifier.like('%{}%'.format(partial_id)))
            if mass_spectrometers:
                q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
            if filter_non_run:
                q = q.group_by(IrradiationPositionTbl.idirradiationpositionTbl)
                q = q.having(count(AnalysisTbl.idanalysisTbl) > 0)

            return self._query_all(q, verbose_query=True)

    def get_associated_experiments(self, idn):
        with self.session_ctx() as sess:
            q = sess.query(distinct(ExperimentTbl.name), IrradiationPositionTbl.identifier)
            q = q.join(ExperimentAssociationTbl, AnalysisTbl, IrradiationPositionTbl)
            q = q.filter(IrradiationPositionTbl.identifier.in_(idn))
            q = q.order_by(IrradiationPositionTbl.identifier)

            return self._query_all(q, verbose_query=False)

    def get_analysis_uuid(self, value):
        return self._retrieve_item(AnalysisTbl, value, key='uuid')

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
                               mass_spectrometers=None, order='asc',
                               **kw):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.join(IrradiationPositionTbl)
            if omit_key or not include_invalid:
                q = q.join(AnalysisChangeTbl)

            if mass_spectrometers:
                if not hasattr(mass_spectrometers, '__iter__'):
                    mass_spectrometers = (mass_spectrometers,)
                q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))

            if not hasattr(lns, '__iter__'):
                lns = (lns,)
            q = q.filter(IrradiationPositionTbl.identifier.in_(lns))

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

    def get_experiment_date_range(self, names):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl.timestamp)
            q = q.join(ExperimentAssociationTbl)
            q = q.filter(ExperimentAssociationTbl.experimentName.in_(names))
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
                                   order='asc',
                                   exclude=None,
                                   exclude_uuids=None,
                                   exclude_invalid=True,
                                   verbose=False):
        with self.session_ctx() as sess:
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
                    q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
                else:
                    q = q.filter(AnalysisTbl.mass_spectrometer == mass_spectrometers)
            if extract_device:
                q = q.filter(AnalysisTbl.extract_device == extract_device)
            if analysis_type:
                q = q.filter(AnalysisTbl.analysis_type == analysis_type)
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
                q = q.filter(not_(AnalysisTbl.idanalysisTbl.in_(exclude)))
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
        return super(DVCDatabase, self)._get_date_range(q, asc, desc, hours=hours)

    def get_project_labnumbers(self, project_names, filter_non_run, low_post=None, high_post=None,
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
                    q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))

                if analysis_types:
                    q = q.filter(AnalysisTbl.analysis_type.in_(analysis_types))
                    project_names.append('references')

                q = q.group_by(IrradiationPositionTbl.identifier)
                q = q.having(count(AnalysisTbl.idanalysisTbl) > 0)
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
            dbirrad = self.get_irradiation(irrad)
            return [l.name for l in dbirrad.levels]

    def get_labnumbers(self, projects=None, experiments=None, mass_spectrometers=None,
                       irradiation=None, level=None,
                       analysis_types=None,
                       high_post=None,
                       low_post=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            q = q.distinct(IrradiationPositionTbl.idirradiationpositionTbl)

            # joins
            at = False
            if experiments:
                at = True
                q = q.join(AnalysisTbl, ExperimentAssociationTbl)
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
                q = q.join(IrradiationPositionTbl, LevelTbl, IrradiationTbl)

            # filters
            if experiments:
                q = q.filter(ExperimentAssociationTbl.experimentName.in_(experiments))
            if projects:
                q = q.filter(ProjectTbl.name.in_(projects))
            if mass_spectrometers:
                q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
            if low_post:
                q = q.filter(AnalysisTbl.timestamp >= low_post)
            if high_post:
                q = q.filter(AnalysisTbl.timestamp <= high_post)
            if analysis_types:
                if 'blank' in analysis_types:
                    analysis_types.remove('blank')
                    q = q.filter(or_(AnalysisTbl.analysis_type.startswith('blank'),
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

    def get_mass_spectrometer(self, name):
        return self._retrieve_item(MassSpectrometerTbl, name)

    def get_experiment(self, name):
        return self._retrieve_item(ExperimentTbl, name)

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
        return self._retrieve_item(IrradiationPositionTbl, identifier, key='identifier')

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

    def get_project(self, name):
        return self._retrieve_item(ProjectTbl, name)

    def get_irradiation_level(self, irrad, name):
        with self.session_ctx() as sess:
            irrad = self.get_irradiation(irrad)
            if irrad:
                q = sess.query(LevelTbl)
                q = q.filter(LevelTbl.irradiationID == irrad.idirradiationTbl)
                q = q.filter(LevelTbl.name == name)
                return self._query_one(q)

    def get_irradiation(self, name):
        return self._retrieve_item(IrradiationTbl, name)

    def get_material(self, name):
        return self._retrieve_item(MaterialTbl, name)

    def get_sample(self, name, project):
        with self.session_ctx() as sess:
            q = sess.query(SampleTbl)
            q = q.join(ProjectTbl)

            project = self.get_project(project)

            q = q.filter(SampleTbl.project == project)
            q = q.filter(SampleTbl.name == name)

            return self._query_one(q)

    def get_last_identifier(self, sample=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            if sample:
                q = q.join(SampleTbl)
                q = q.filter(SampleTbl.name == sample)

            q = q.order_by(func.abs(IrradiationPositionTbl.identifier).desc())
            return self._query_first(q)

    def get_latest_load(self):
        return self._retrieve_first(LoadTbl, order_by=LoadTbl.create_date.desc())

    # multi getters
    def get_analyses(self, analysis_type=None, mass_spectrometer=None, reverse_order=False):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            if mass_spectrometer:
                q = q.filter(AnalysisTbl.mass_spectrometer == mass_spectrometer)
            if analysis_type:
                q = q.filter(AnalysisTbl.analysis_type == analysis_type)

            q = q.order_by(getattr(AnalysisTbl.timestamp, 'desc' if reverse_order else 'asc')())
            return self._query_all(q)

    def get_analysis_types(self):
        return []

    def get_load_holders(self):
        with self.session_ctx():
            return [ni.name for ni in self._retrieve_items(LoadHolderTbl)]

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
            return [ni.identifier for ni in self._query_all(q, verbose_query=True)]

    def get_loads(self):
        with self.session_ctx():
            loads = self._retrieve_items(LoadTbl)
            return [ui.name for ui in loads]

    def get_extraction_devices(self):
        with self.session_ctx():
            eds = self._retrieve_items(ExtractDeviceTbl)
            return [ui.name for ui in eds]

    def get_users(self):
        return self._retrieve_items(UserTbl)

    def get_usernames(self):
        with self.session_ctx():
            return [ui.name for ui in self.get_users()]

    def get_project_names(self):
        return self._get_table_names(ProjectTbl)

    def get_material_names(self):
        return self._get_table_names(MaterialTbl)

    def get_samples(self, project=None, **kw):
        if project:
            if hasattr(project, '__iter__'):
                kw = self._append_filters(ProjectTbl.name.in_(project), kw)
            else:
                kw = self._append_filters(ProjectTbl.name == project, kw)
            kw = self._append_joins(ProjectTbl, kw)
        return self._retrieve_items(SampleTbl, verbose_query=False, **kw)

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
            kw = self._append_joins((LevelTbl, IrradiationPositionTbl, SampleTbl), kw)

        if mass_spectrometers:
            kw = self._append_filters(AnalysisTbl.mass_spectrometer.name.in_(mass_spectrometers), kw)
            kw = self._append_joins(LevelTbl, IrradiationPositionTbl, AnalysisTbl, kw)

        order = None
        if order_func:
            order = getattr(IrradiationTbl.name, order_func)()

        return self._retrieve_items(IrradiationTbl, order=order, **kw)

    def get_projects(self, irradiation=None, level=None, mass_spectrometers=None, order=None):

        if order:
            order = getattr(ProjectTbl.name, order)()

        if irradiation or mass_spectrometers:
            with self.session_ctx() as sess:
                q = sess.query(ProjectTbl)
                q = q.join(SampleTbl, IrradiationPositionTbl)
                if irradiation:
                    q = q.join(LevelTbl, IrradiationPositionTbl)
                    q = q.filter(LevelTbl.name == level)
                    q = q.filter(IrradiationTbl.name == irradiation)

                else:
                    if not hasattr(mass_spectrometers, '__iter__'):
                        mass_spectrometers = (mass_spectrometers,)

                    q = q.join(AnalysisTbl)

                    q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
                    if order:
                        q = q.order_by(order)
                ps = self._query_all(q)
        else:
            ps = self._retrieve_items(ProjectTbl, order=order)
        return ps

    def get_tag(self, name):
        return self._retrieve_item(TagTbl, name)

    def get_tags(self):
        return self._retrieve_items(TagTbl)

    def get_experiments(self):
        return self._retrieve_items(ExperimentTbl)

    def get_extract_devices(self):
        return self._retrieve_items(ExtractDeviceTbl)

    def get_mass_spectrometer_names(self):
        with self.session_ctx():
            ms = self.get_mass_spectrometers()
            return [mi.name for mi in ms]

    def get_mass_spectrometers(self):
        return self._retrieve_items(MassSpectrometerTbl)

    def get_experiment_identifiers(self):
        return self._get_table_names(ExperimentTbl)

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
            q = q.join(IrradiationPositionTbl, LevelTbl, IrradiationTbl, SampleTbl, AnalysisChangeTbl)
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
            q = sess.query(AnalysisTbl.idanalysisTbl)
            q = q.join(AnalysisChangeTbl)
            q = q.filter(AnalysisChangeTbl.tag == name)
            n = q.count()
            if n:
                a = 'analyses' if n > 1 else 'analysis'

                if not self.confirmation_dialog('The Tag "{}" is applied to {} {}. '
                                                'Are you sure to want to delete it?'.format(name, n, a)):
                    return

            self._delete_item(name, name='tag')
            return True

    # private
    def _get_table_names(self, tbl):
        with self.session_ctx():
            names = self._retrieve_items(tbl)
            return [ni.name for ni in names]

# ============= EOF =============================================
