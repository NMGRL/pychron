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
# ============= standard library imports ========================
from sqlalchemy import Column, Integer, String, TIMESTAMP, Float, BLOB, func, Boolean, ForeignKey, DATE, DATETIME, TEXT
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship

from pychron.core.helpers.datetime_tools import make_timef
from pychron.database.orms import stringcolumn, primary_key
from pychron.database.records.isotope_record import DVCIsotopeRecordView
from pychron.experiment.utilities.identifier import make_runid

Base = declarative_base()


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__


class NameMixin(BaseMixin):
    name = stringcolumn(80)

    def __repr__(self):
        return '{}<{}>'.format(self.__class__.__name__, self.name)


class InterpretedAgeTbl(Base, BaseMixin):
    idinterpretedagetbl = Column(Integer, primary_key=True)
    age_kind = stringcolumn(32)
    kca_kind = stringcolumn(32)

    age = Column(Float)
    age_err = Column(Float)
    display_age_units = stringcolumn(2)

    kca = Column(Float)
    kca_err = Column(Float)
    mswd = Column(Float)

    age_error_kind = stringcolumn(80)
    include_j_error_in_mean = Column(Boolean)
    include_j_error_in_plateau = Column(Boolean)
    include_j_error_in_individual_analyses = Column(Boolean)

    analyses = relationship('InterpretedAgeSetTbl', backref='interpreted_age')


class InterpretedAgeSetTbl(Base, BaseMixin):
    idinterpretedagesettbl = Column(Integer, primary_key=True)
    interpreted_ageID = Column(Integer, ForeignKey('InterpretedAgeTbl.idinterpretedagetbl'))
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))
    forced_plateau_step = Column(Boolean)
    plateau_step = Column(Boolean)
    tag = stringcolumn(80)

    analysis = relationship('AnalysisTbl', uselist=False)


class RepositoryTbl(Base, BaseMixin):
    name = Column(String(80), primary_key=True)
    principal_investigatorID = Column(Integer, ForeignKey('PrincipalInvestigatorTbl.id'))
    # timestamp = Column(TIMESTAMP, default=func.now())
    # creator = stringcolumn(80)

    repository_associations = relationship('RepositoryAssociationTbl', backref='repository_item')

    @property
    def record_view(self):
        from pychron.envisage.browser.record_views import RepositoryRecordView

        v = RepositoryRecordView()
        v.name = self.name
        if self.principal_investigator:
            v.principal_investigator = self.principal_investigator.name
        return v


class RepositoryAssociationTbl(Base, BaseMixin):
    idrepositoryassociationTbl = Column(Integer, primary_key=True)
    repository = Column(String(80), ForeignKey('RepositoryTbl.name'))
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))
    # experiments = relationship('ExperimentTbl')
    # analyses = relationship('AnalysisTbl', backref='experiment_associations')


class AnalysisChangeTbl(Base, BaseMixin):
    idanalysischangeTbl = Column(Integer, primary_key=True)
    # tag = Column(String(40), ForeignKey('TagTbl.name'))
    tag = stringcolumn(40)
    timestamp = Column(TIMESTAMP)
    user = stringcolumn(40)
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))


class AnalysisTbl(Base, BaseMixin):
    id = primary_key()
    timestamp = Column(TIMESTAMP)
    # tag = stringcolumn(45)
    uuid = stringcolumn(32)
    analysis_type = stringcolumn(45)
    aliquot = Column(Integer)
    increment = Column(Integer)

    irradiation_positionID = Column(Integer, ForeignKey('IrradiationPositionTbl.id'))

    measurementName = stringcolumn(45)
    extractionName = stringcolumn(45)
    postEqName = stringcolumn(45)
    postMeasName = stringcolumn(45)

    mass_spectrometer = Column(String(45), ForeignKey('MassSpectrometerTbl.name'))
    extract_device = stringcolumn(45)
    extract_value = Column(Float)
    extract_units = stringcolumn(45)
    cleanup = Column(Float)
    duration = Column(Float)

    weight = Column(Float)
    comment = stringcolumn(80)
    repository_associations = relationship('RepositoryAssociationTbl', backref='analysis')
    group_sets = relationship('AnalysisGroupSetTbl', backref='analysis')

    change = relationship('AnalysisChangeTbl', uselist=False, backref='analysis')
    measured_position = relationship('MeasuredPositionTbl', uselist=False, backref='analysis')
    media = relationship('MediaTbl', backref='analysis')

    _record_view = None
    group_id = 0
    frozen = False

    delta_time = 0

    @property
    def is_plateau_step(self):
        return

    @property
    def timestampf(self):
        return make_timef(self.timestamp)

    @property
    def identifier(self):
        return self.irradiation_position.identifier

    @property
    def irradiation_info(self):
        return '{}{} {}'.format(self.irradiation, self.irradiation_level, self.irradiation_position_position)

    @property
    def irradiation(self):
        return self.irradiation_position.level.irradiation.name

    @property
    def irradiation_level(self):
        return self.irradiation_position.level.name

    @property
    def project(self):
        return self.irradiation_position.sample.project.name

    @property
    def sample(self):
        return self.irradiation_position.sample.name

    @property
    def irradiation_position_position(self):
        return self.irradiation_position.position

    @property
    def tag(self):
        return self.change.tag

    # @property
    # def tag_dict(self):
    #     return {k: getattr(self.change.tag_item, k) for k in ('name',) + OMIT_KEYS}

    # @property
    # def labnumber(self):
    #     return self.irradiation_position

    @property
    def analysis_timestamp(self):
        return self.timestamp

    @property
    def rundate(self):
        return self.timestamp

    @property
    def repository_identifier(self):
        if self.repository_associations and len(self.repository_associations) == 1:
            return self.repository_associations[0].repository

    @property
    def record_id(self):
        return make_runid(self.irradiation_position.identifier, self.aliquot, self.increment)

    @property
    def repository_identifier(self):
        es = [e.repository for e in self.repository_associations]
        if len(es) == 1:
            return es[0]

    @property
    def record_views(self):
        repos = self.repository_associations
        if len(repos) == 1:
            return self._make_record_view(repos[0].repository),
        else:
            return [self._make_record_view(r.repository, use_suffix=True) for r in repos]

    def make_record_view(self, repository, use_suffix=False):
        for repo in self.repository_associations:
            if repo.repository == repository:
                return self._make_record_view(repo.repository, use_suffix=use_suffix)
        else:
            return self._make_record_view(self.repository_associations[0].repository)

    def _make_record_view(self, repo, use_suffix=False):
        iv = DVCIsotopeRecordView(self)
        # iv.repository_ids = es = [e.repository for e in self.repository_associations]
        # if len(es) == 1:
        #     iv.repository_identifier = es[0]
        iv.repository_identifier = repo
        iv.use_repository_suffix = use_suffix
        iv.init()
        return iv


class ProjectTbl(Base, NameMixin):
    id = primary_key()
    principal_investigatorID = Column(Integer, ForeignKey('PrincipalInvestigatorTbl.id'))

    samples = relationship('SampleTbl', backref='project')
    analysis_groups = relationship('AnalysisGroupTbl', backref='project')
    checkin_date = Column(DATE)
    comment = Column(BLOB)
    lab_contact = stringcolumn(80)
    institution = stringcolumn(80)

    @property
    def pname(self):
        return '{} ({})'.format(self.name, self.principal_investigator.name) if self.principal_investigator else \
            self.name


class MaterialTbl(Base, NameMixin):
    id = primary_key()
    samples = relationship('SampleTbl', backref='material')
    grainsize = stringcolumn(80)

    @property
    def gname(self):
        return '{} ({})'.format(self.name, self.grainsize) if self.grainsize else self.name


class SampleTbl(Base, NameMixin):
    id = primary_key()
    materialID = Column(Integer, ForeignKey('MaterialTbl.id'))
    projectID = Column(Integer, ForeignKey('ProjectTbl.id'))
    positions = relationship('IrradiationPositionTbl', backref='sample')
    note = stringcolumn(140)


class ProductionTbl(Base, NameMixin):
    id = primary_key()
    levels = relationship('LevelTbl', backref='production')


class LevelTbl(Base, NameMixin):
    id = primary_key()
    irradiationID = Column(Integer, ForeignKey('IrradiationTbl.id'))
    productionID = Column(Integer, ForeignKey('ProductionTbl.id'))
    holder = stringcolumn(45)
    z = Column(Float)

    positions = relationship('IrradiationPositionTbl', backref='level')

    note = Column(BLOB)


class IrradiationTbl(Base, NameMixin):
    id = primary_key()
    levels = relationship('LevelTbl', backref='irradiation')
    create_date = Column(TIMESTAMP)


class IrradiationPositionTbl(Base, BaseMixin):
    id = primary_key()
    identifier = stringcolumn(80)
    sampleID = Column(Integer, ForeignKey('SampleTbl.id'))
    levelID = Column(Integer, ForeignKey('LevelTbl.id'))
    position = Column(Integer)
    note = Column(BLOB)
    weight = Column(Float)
    j = Column(Float)
    j_err = Column(Float)

    analyses = relationship('AnalysisTbl', backref='irradiation_position')

    @property
    def analysis_count(self):
        return object_session(self).query(AnalysisTbl).with_parent(self).count()

    @property
    def analyzed(self):
        return bool(self.analysis_count)
    # @property
    # def irradiation_position(self):
    #     return self


# class TagTbl(Base, BaseMixin):
#     name = Column(String(40), primary_key=True)
#     omit_ideo = Column(Boolean)
#     omit_spec = Column(Boolean)
#     omit_iso = Column(Boolean)
#     omit_series = Column(Boolean)
#
#     analyses = relationship('AnalysisChangeTbl', backref='tag_item')


class MassSpectrometerTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    kind = stringcolumn(45)
    # active = Column(Bool)
    active = True

class ExtractDeviceTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)


class PrincipalInvestigatorTbl(Base, BaseMixin):
    id = primary_key()
    affiliation = stringcolumn(140)
    email = stringcolumn(140)
    last_name = Column(String(140))
    first_initial = Column(String(10))

    projects = relationship('ProjectTbl', backref='principal_investigator')
    repositories = relationship('RepositoryTbl', backref='principal_investigator')
    irs = relationship('IRTbl', backref='principal_investigator')

    @property
    def name(self):
        return '{}, {}'.format(self.last_name, self.first_initial) if self.first_initial else self.last_name

    @property
    def record_view(self):
        from pychron.envisage.browser.record_views import PrincipalInvestigatorRecordView
        r = PrincipalInvestigatorRecordView(self)
        return r


class UserTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    affiliation = stringcolumn(80)
    category = stringcolumn(80)
    email = stringcolumn(80)

    media = relationship('MediaTbl', backref='user')


class LoadTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    create_date = Column(TIMESTAMP, default=func.now())
    archived = Column(Boolean, default=False)

    holderName = Column(String(45), ForeignKey('LoadHolderTbl.name'))
    loaded_positions = relationship('LoadPositionTbl', backref='load')
    measured_positions = relationship('MeasuredPositionTbl', backref='load')


class LoadHolderTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    loads = relationship('LoadTbl', backref='holder')


class LoadPositionTbl(Base, BaseMixin):
    id = primary_key()
    identifier = Column(String(80), ForeignKey('IrradiationPositionTbl.identifier'))
    position = Column(Integer)
    loadName = Column(String(45), ForeignKey('LoadTbl.name'))
    weight = Column(Float)
    note = Column(BLOB)


class MeasuredPositionTbl(Base, BaseMixin):
    id = primary_key()
    position = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)

    is_degas = Column(Boolean)
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))
    loadName = Column(String(45), ForeignKey('LoadTbl.name'))


class VersionTbl(Base, BaseMixin):
    version = Column(String(40), primary_key=True)


# ======================== Sample Prep ========================
class SamplePrepWorkerTbl(Base, BaseMixin):
    name = Column(String(32), primary_key=True)
    fullname = Column(String(45))
    email = Column(String(45))
    phone = Column(String(45))
    comment = Column(String(140))


class SamplePrepSessionTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    comment = Column(String(140))
    worker_name = Column(String(32), ForeignKey('SamplePrepWorkerTbl.name'))
    start_date = Column(DATE, default=func.now())
    end_date = Column(DATE)


class SamplePrepStepTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    sampleID = Column(Integer, ForeignKey('SampleTbl.id'))
    sessionID = Column(Integer, ForeignKey('SamplePrepSessionTbl.id'))
    crush = Column(String(140))
    wash = Column(String(140))
    sieve = Column(String(140))
    frantz = Column(String(140))
    acid = Column(String(140))
    heavy_liquid = Column(String(140))
    pick = Column(String(140))
    status = Column(String(32))
    comment = Column(String(300))
    timestamp = Column(DATETIME, default=func.now())
    added = Column(Boolean)


class SamplePrepImageTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    stepID = Column(Integer, ForeignKey('SamplePrepStepTbl.id'))
    host = Column(String(45))
    path = Column(String(45))
    timestamp = Column(DATETIME, default=func.now())


class RestrictedNameTbl(Base, BaseMixin):
    id = primary_key()
    name = stringcolumn()
    category = stringcolumn()


# ======================== Lab Management ========================
class IRTbl(Base, BaseMixin):
    ir = primary_key(klass=String(32))
    principal_investigatorID = Column(Integer, ForeignKey('PrincipalInvestigatorTbl.id'))
    institution = Column(String(140))
    checkin_date = Column(DATE)
    lab_contact = Column(String(140), ForeignKey('UserTbl.name'))
    comment = Column(BLOB)

    @property
    def principal_investigator_name(self):
        ret = ''
        if self.principal_investigator:
            ret = self.principal_investigator.name
        return ret


# ======================== Analysis Groups ========================
class AnalysisGroupTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(140))
    create_date = Column(TIMESTAMP)
    projectID = Column(Integer, ForeignKey('ProjectTbl.id'))
    user = Column(String(140), ForeignKey('UserTbl.name'))

    sets = relationship('AnalysisGroupSetTbl', backref='group')


class AnalysisGroupSetTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))
    groupID = Column(Integer, ForeignKey('AnalysisGroupTbl.id'))


class MediaTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))
    url = Column(TEXT)

    username = Column(String(140), ForeignKey('UserTbl.name'))
    create_date = Column(TIMESTAMP, default=func.now())


# ============= EOF =============================================
