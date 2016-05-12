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
from sqlalchemy import Column, Integer, String, TIMESTAMP, Float, BLOB, func, Boolean, ForeignKey, DATE
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship

# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import make_timef
from pychron.database.records.isotope_record import DVCIsotopeRecordView
from pychron.experiment.utilities.identifier import make_runid
from pychron.pychron_constants import OMIT_KEYS

Base = declarative_base()


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__


class NameMixin(BaseMixin):
    name = Column(String(80))

    def __repr__(self):
        return '{}<{}>'.format(self.__class__.__name__, self.name)


class InterpretedAgeTbl(Base, BaseMixin):
    idinterpretedagetbl = Column(Integer, primary_key=True)
    age_kind = Column(String(32))
    kca_kind = Column(String(32))

    age = Column(Float)
    age_err = Column(Float)
    display_age_units = Column(String(2))

    kca = Column(Float)
    kca_err = Column(Float)
    mswd = Column(Float)

    age_error_kind = Column(String(80))
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
    tag = Column(String(80))

    analysis = relationship('AnalysisTbl', uselist=False)


class RepositoryTbl(Base, BaseMixin):
    name = Column(String(80), primary_key=True)
    principal_investigator = Column(String(140), ForeignKey('PrincipalInvestigatorTbl.name'))
    # timestamp = Column(TIMESTAMP, default=func.now())
    # creator = Column(String(80))

    repository_associations = relationship('RepositoryAssociationTbl', backref='repository_item')

    @property
    def record_view(self):
        from pychron.envisage.browser.record_views import RepositoryRecordView

        v = RepositoryRecordView()
        v.name = self.name
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
    tag = Column(String(40))
    timestamp = Column(TIMESTAMP)
    user = Column(String(40))
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))


class AnalysisTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP)
    # tag = Column(String(45))
    uuid = Column(String(32))
    analysis_type = Column(String(45))
    aliquot = Column(Integer)
    increment = Column(Integer)

    irradiation_positionID = Column(Integer, ForeignKey('IrradiationPositionTbl.id'))

    measurementName = Column(String(45))
    extractionName = Column(String(45))
    postEqName = Column(String(45))
    postMeasName = Column(String(45))

    mass_spectrometer = Column(String(45), ForeignKey('MassSpectrometerTbl.name'))
    extract_device = Column(String(45))
    extract_value = Column(Float)
    extract_units = Column(String(45))
    cleanup = Column(Float)
    duration = Column(Float)

    weight = Column(Float)
    comment = Column(String(80))
    repository_associations = relationship('RepositoryAssociationTbl', backref='analysis')
    change = relationship('AnalysisChangeTbl', uselist=False, backref='analysis')
    measured_position = relationship('MeasuredPositionTbl', uselist=False, backref='analysis')

    _record_view = None

    @property
    def irradiation(self):
        return self.irradiation_position.level.irradiation.name

    @property
    def irradiation_level(self):
        return self.irradiation_position.level.name

    #
    @property
    def irradiation_position_position(self):
        return self.irradiation_position.position

    @property
    def tag_dict(self):
        return {k: getattr(self.change.tag_item, k) for k in ('name',) + OMIT_KEYS}

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
        # iv = self._record_view
        # if not iv:
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
        iv = DVCIsotopeRecordView()
        iv.extract_script_name = self.extractionName
        iv.meas_script_name = self.measurementName

        irradpos = self.irradiation_position
        iv.identifier = irradpos.identifier
        iv.irradiation = irradpos.level.irradiation.name
        iv.irradiation_level = irradpos.level.name
        iv.irradiation_position_position = irradpos.position

        iv.labnumber = iv.identifier
        # iv.repository_ids = es = [e.repository for e in self.repository_associations]
        # if len(es) == 1:
        #     iv.repository_identifier = es[0]
        iv.repository_identifier = repo
        iv.use_repository_suffix = use_suffix

        for tag in ('aliquot', 'increment', 'uuid',
                    'extract_value', 'cleanup', 'duration',
                    'mass_spectrometer',
                    'extract_device',
                    'rundate',
                    'analysis_type', 'comment'):
            setattr(iv, tag, getattr(self, tag))

        if irradpos.sample:
            iv.sample = irradpos.sample.name
            if irradpos.sample.project:
                iv.project = irradpos.sample.project.name

        iv.timestampf = make_timef(self.timestamp)
        iv.tag = self.change.tag
        iv.init()
        return iv

        # self._record_view = iv

        # return iv


class ProjectTbl(Base, NameMixin):
    id = Column(Integer, primary_key=True)
    principal_investigator = Column(String(140), ForeignKey('PrincipalInvestigatorTbl.name'))

    samples = relationship('SampleTbl', backref='project')


class MaterialTbl(Base, NameMixin):
    id = Column(Integer, primary_key=True)
    samples = relationship('SampleTbl', backref='material')
    grainsize = Column(String(80))


class SampleTbl(Base, NameMixin):
    id = Column(Integer, primary_key=True)
    materialID = Column(Integer, ForeignKey('MaterialTbl.id'))
    projectID = Column(Integer, ForeignKey('ProjectTbl.id'))
    positions = relationship('IrradiationPositionTbl', backref='sample')


class ProductionTbl(Base, NameMixin):
    id = Column(Integer, primary_key=True)
    levels = relationship('LevelTbl', backref='production')


class LevelTbl(Base, NameMixin):
    id = Column(Integer, primary_key=True)
    irradiationID = Column(Integer, ForeignKey('IrradiationTbl.id'))
    productionID = Column(Integer, ForeignKey('ProductionTbl.id'))
    holder = Column(String(45))
    z = Column(Float)

    positions = relationship('IrradiationPositionTbl', backref='level')

    note = Column(BLOB)


class IrradiationTbl(Base, NameMixin):
    id = Column(Integer, primary_key=True)
    levels = relationship('LevelTbl', backref='irradiation')


class IrradiationPositionTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    identifier = Column(String(80))
    sampleID = Column(Integer, ForeignKey('SampleTbl.id'))
    levelID = Column(Integer, ForeignKey('LevelTbl.id'))
    position = Column(Integer)
    note = Column(BLOB)
    weight = Column(Float)
    j = Column(Float)
    j_err = Column(Float)

    analyses = relationship('AnalysisTbl', backref='irradiation_position')

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
    kind = Column(String(45))


class ExtractDeviceTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)


class PrincipalInvestigatorTbl(Base, BaseMixin):
    name = Column(String(140), primary_key=True)
    affiliation = Column(String(140))
    email = Column(String(140))

    @property
    def record_view(self):
        from pychron.envisage.browser.record_views import PrincipalInvestigatorRecordView
        r = PrincipalInvestigatorRecordView(self)
        return r


class UserTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    affiliation = Column(String(80))
    category = Column(String(80))
    email = Column(String(80))


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
    id = Column(Integer, primary_key=True)
    identifier = Column(String(80), ForeignKey('IrradiationPositionTbl.identifier'))
    position = Column(Integer)
    loadName = Column(String(45), ForeignKey('LoadTbl.name'))
    weight = Column(Float)
    note = Column(BLOB)


class MeasuredPositionTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
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
    timestamp = Column(TIMESTAMP, default=func.now())
    added = Column(Boolean)


class SamplePrepImageTbl(Base, BaseMixin):
    id = Column(Integer, primary_key=True)
    stepID = Column(Integer, ForeignKey('SamplePrepStepTbl.id'))
    host = Column(String(45))
    path = Column(String(45))

# ============= EOF =============================================
