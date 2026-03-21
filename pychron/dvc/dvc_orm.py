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

from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    Float,
    func,
    Boolean,
    ForeignKey,
    DATE,
    DATETIME,
    TEXT,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import object_session, deferred
from sqlalchemy.orm import relationship

from pychron.core.helpers.datetime_tools import make_timef
from pychron.core.utils import alphas
from pychron.database.orms import stringcolumn, primary_key
from pychron.experiment.utilities.runid import make_runid
from pychron.pychron_constants import PRECLEANUP, POSTCLEANUP, CRYO_TEMP

Base = declarative_base()


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__


class IDMixin(BaseMixin):
    id = Column(Integer, primary_key=True)


class NameMixin(IDMixin):
    name = stringcolumn(80)

    def __repr__(self):
        return "{}<{}>".format(self.__class__.__name__, self.name)


class RepositoryTbl(Base, BaseMixin):
    name = Column(String(80), primary_key=True)
    principal_investigatorID = Column(
        Integer, ForeignKey("PrincipalInvestigatorTbl.id")
    )
    # timestamp = Column(TIMESTAMP, default=func.now())
    # creator = stringcolumn(80)

    repository_associations = relationship(
        "RepositoryAssociationTbl", backref="repository_item"
    )

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
    repository = Column(String(80), ForeignKey("RepositoryTbl.name"))
    analysisID = Column(Integer, ForeignKey("AnalysisTbl.id"))
    # experiments = relationship('ExperimentTbl')
    # analyses = relationship('AnalysisTbl', backref='experiment_associations')


class AnalysisChangeTbl(Base, BaseMixin):
    idanalysischangeTbl = Column(Integer, primary_key=True)
    # tag = Column(String(40), ForeignKey('TagTbl.name'))
    tag = stringcolumn(40)
    timestamp = Column(TIMESTAMP)
    user = stringcolumn(40)
    analysisID = Column(Integer, ForeignKey("AnalysisTbl.id"))


class AnalysisTbl(Base, IDMixin):
    experiment_type = stringcolumn(32)
    timestamp = Column(DATETIME)
    # tag = stringcolumn(45)
    uuid = stringcolumn(32)
    analysis_type = stringcolumn(45)
    aliquot = Column(Integer)
    increment = Column(Integer)

    irradiation_positionID = Column(Integer, ForeignKey("IrradiationPositionTbl.id"))
    measurementName = stringcolumn(45)
    extractionName = stringcolumn(45)
    postEqName = stringcolumn(45)
    postMeasName = stringcolumn(45)

    mass_spectrometer = Column(String(45), ForeignKey("MassSpectrometerTbl.name"))
    extract_device = stringcolumn(45)
    extract_value = Column(Float)
    extract_units = stringcolumn(45)
    cleanup = Column(Float)

    duration = Column(Float)

    weight = Column(Float)
    comment = stringcolumn(200)
    repository_associations = relationship(
        "RepositoryAssociationTbl", backref="analysis", lazy="joined"
    )
    group_sets = relationship("AnalysisGroupSetTbl", backref="analysis")

    change = relationship(
        "AnalysisChangeTbl", uselist=False, backref="analysis", lazy="joined"
    )
    measured_positions = relationship("MeasuredPositionTbl", backref="analysis")
    media = relationship("MediaTbl", backref="analysis")
    irradiation_position = relationship(
        "IrradiationPositionTbl", backref="analysis", lazy="joined"
    )

    _record_view = None
    group_id = 0
    frozen = False

    delta_time = 0

    review_status = None
    repository_identifier = ""
    is_plateau_step = None

    load_name = ""
    load_holder = ""
    _temporary_tag = None

    pre_cleanup = Column(PRECLEANUP, Float)
    post_cleanup = Column(POSTCLEANUP, Float)
    cryo_temperature = Column(CRYO_TEMP, Float)

    @property
    def step(self):
        print(self.increment, alphas(self.increment))
        return alphas(self.increment)

    @property
    def position(self):
        if self.measured_positions:
            return ",".join(
                ["{}".format(p.position) for p in self.measured_positions if p.position]
            )
        else:
            return ""

    @property
    def meas_script_name(self):
        return self.measurementName

    @property
    def extract_script_name(self):
        return self.extractionName

    @property
    def timestampf(self):
        return make_timef(self.timestamp)

    @property
    def identifier(self):
        return self.irradiation_position.identifier

    @property
    def irradiation_info(self):
        return "{}{} {}".format(
            self.irradiation, self.irradiation_level, self.irradiation_position_position
        )

    @property
    def irradiation(self):
        return self.irradiation_position.level.irradiation.name

    @property
    def irradiation_level(self):
        return self.irradiation_position.level.name

    @property
    def packet(self):
        return self.irradiation_position.packet or ""

    @property
    def project(self):
        try:
            return self.irradiation_position.sample.project.name
        except AttributeError:
            return ""

    @property
    def principal_investigator(self):
        try:
            return self.irradiation_position.sample.project.principal_investigator.name
        except AttributeError:
            return ""

    @property
    def sample(self):
        try:
            return self.irradiation_position.sample.name
        except AttributeError:
            return ""

    @property
    def irradiation_position_position(self):
        return self.irradiation_position.position

    @property
    def material(self):
        try:
            return self.irradiation_position.sample.material.gname
        except AttributeError:
            return ""

    @property
    def tag(self):
        if self._temporary_tag:
            tag = self._temporary_tag
        else:
            tag = self.change.tag
        return tag

    def set_tag(self, t):
        self._temporary_tag = t

    @property
    def analysis_timestamp(self):
        return self.timestamp

    @property
    def rundate(self):
        return self.timestamp

    @property
    def record_id(self):
        return make_runid(
            self.irradiation_position.identifier, self.aliquot, self.increment
        )

    @property
    def repository_identifier(self):
        if self.repository_associations and len(self.repository_associations) == 1:
            return self.repository_associations[0].repository

    @property
    def display_uuid(self):
        u = self.uuid
        if not u:
            u = ""
        return u[:8]

    def get_load_name(self):
        ln = ""
        if self.measured_positions:
            ln = self.measured_positions[0].loadName or ""
        return ln

    def get_load_holder(self):
        lh = ""
        if self.measured_positions:
            load = self.measured_positions[0].load
            if load:
                lh = load.holderName
        return lh

    def bind(self):
        self.load_name = self.get_load_name()
        self.load_holder = self.get_load_holder()

        # force binding of irradiation_position, sample, material, project, pi
        self.irradiation_position
        self.irradiation_level
        self.irradiation
        self.material
        self.project
        self.principal_investigator


# class AnalysisIntensitiesTbl(Base, IDMixin):
#     analysisID = Column(Integer, ForeignKey('AnalysisTbl.id'))
#     value = Column(Float)
#     error = Column(Float)
#     n = Column(Integer)
#     fit = stringcolumn(32)
#     fit_error_type = stringcolumn(32)
#     baseline_value = Column(Float)
#     baseline_error = Column(Float)
#     baseline_n = Column(Integer)
#     baseline_fit = stringcolumn(32)
#     baseline_fit_error_type = stringcolumn(32)
#     blank_value = Column(Float)
#     blank_error = Column(Float)
#
#     # kca_value = Column(Float)
#     # kca_error = Column(Float)
#     # kcl_value = Column(Float)
#     # kcl_error = Column(Float)
#
#     isotope = stringcolumn(32)
#     detector = stringcolumn(32)


class ProjectTbl(Base, NameMixin):
    principal_investigatorID = Column(
        Integer, ForeignKey("PrincipalInvestigatorTbl.id")
    )

    samples = relationship("SampleTbl", backref="project")
    analysis_groups = relationship("AnalysisGroupTbl", backref="project")
    checkin_date = Column(DATE)
    comment = Column(TEXT)
    lab_contact = stringcolumn(80)
    institution = stringcolumn(80)

    @property
    def pname(self):
        return (
            "{} ({})".format(self.name, self.principal_investigator.name)
            if self.principal_investigator
            else self.name
        )

    @property
    def unique_id(self):
        return self.id


class MaterialTbl(Base, NameMixin):
    samples = relationship("SampleTbl", backref="material")
    grainsize = stringcolumn(80)

    @property
    def gname(self):
        return (
            "{} ({})".format(self.name, self.grainsize) if self.grainsize else self.name
        )

    def __repr__(self):
        return "{}<{}>".format(self.__class__.__name__, self.gname)


class SampleTbl(Base, NameMixin):
    materialID = Column(Integer, ForeignKey("MaterialTbl.id"))
    projectID = Column(Integer, ForeignKey("ProjectTbl.id"))
    note = stringcolumn(140)
    igsn = stringcolumn(140)
    lat = Column(Float)
    lon = Column(Float)

    storage_location = deferred(stringcolumn(140))
    lithology = deferred(stringcolumn(140))
    unit = deferred(stringcolumn(80))
    lithology_class = deferred(stringcolumn(140))
    lithology_type = deferred(stringcolumn(140))
    lithology_group = deferred(stringcolumn(140))

    location = deferred(stringcolumn(140))
    approximate_age = deferred(Column(Float))
    elevation = deferred(Column(Float))
    create_date = deferred(Column(DateTime, default=func.now()))
    update_date = deferred(Column(DateTime, onupdate=func.now(), default=func.now()))

    positions = relationship("IrradiationPositionTbl", backref="sample", lazy="joined")
    preps = relationship("SamplePrepStepTbl", backref="sample")


# class ProductionTbl(Base, NameMixin):
#     levels = relationship('LevelTbl', backref='production')


class LevelTbl(Base, NameMixin):
    irradiationID = Column(Integer, ForeignKey("IrradiationTbl.id"))
    # productionID = Column(Integer, ForeignKey('ProductionTbl.id'))
    holder = stringcolumn(45)
    z = Column(Float)

    positions = relationship("IrradiationPositionTbl", backref="level", lazy="joined")

    note = Column(TEXT)

    @property
    def projects(self):
        ps = []
        for p in self.positions:
            try:
                name = p.sample.project.name
                if name != "Irradiation-{}".format(self.irradiation.name):
                    ps.append(p.sample.project.pname)

            except AttributeError:
                pass

        return list(set(ps))


class IrradiationTbl(Base, NameMixin):
    levels = relationship("LevelTbl", backref="irradiation", lazy="joined")
    create_date = Column(TIMESTAMP, default=func.now())


class IrradiationPositionTbl(Base, IDMixin):
    identifier = stringcolumn(80)
    sampleID = Column(Integer, ForeignKey("SampleTbl.id"))
    levelID = Column(Integer, ForeignKey("LevelTbl.id"))
    position = Column(Integer)
    note = Column(TEXT)
    weight = Column(Float)
    j = Column(Float)
    j_err = Column(Float)
    packet = stringcolumn(40)

    analyses = relationship("AnalysisTbl")

    @property
    def analysis_count(self):
        return object_session(self).query(AnalysisTbl).with_parent(self).count()

    @property
    def analyzed(self):
        return bool(self.analysis_count)


class MassSpectrometerTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    kind = stringcolumn(45)
    # active = Column(Bool)
    active = True


class ExtractDeviceTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)


class PrincipalInvestigatorTbl(Base, IDMixin):
    affiliation = stringcolumn(140)
    email = stringcolumn(140)
    last_name = Column(String(140))
    first_initial = Column(String(10))

    projects = relationship("ProjectTbl", backref="principal_investigator")
    repositories = relationship("RepositoryTbl", backref="principal_investigator")
    irs = relationship("IRTbl", backref="principal_investigator")

    @property
    def name(self):
        return (
            "{}, {}".format(self.last_name, self.first_initial)
            if self.first_initial
            else self.last_name
        )

    @property
    def record_view(self):
        from pychron.envisage.browser.record_views import (
            PrincipalInvestigatorRecordView,
        )

        r = PrincipalInvestigatorRecordView(self)
        return r


class UserTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    affiliation = stringcolumn(80)
    category = stringcolumn(80)
    email = stringcolumn(80)

    media = relationship("MediaTbl", backref="user")


class LoadTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    create_date = Column(TIMESTAMP, default=func.now())
    archived = Column(Boolean, default=False)
    username = Column(String(140), ForeignKey("UserTbl.name"))

    holderName = Column(String(45))
    loaded_positions = relationship("LoadPositionTbl", backref="load")
    measured_positions = relationship("MeasuredPositionTbl", backref="load")


class LoadPositionTbl(Base, IDMixin):
    identifier = Column(String(80), ForeignKey("IrradiationPositionTbl.identifier"))
    position = Column(Integer)
    loadName = Column(String(45), ForeignKey("LoadTbl.name"))
    weight = Column(Float)
    note = Column(TEXT)
    nxtals = Column(Integer)


class MeasuredPositionTbl(Base, IDMixin):
    position = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)

    is_degas = Column(Boolean)
    analysisID = Column(Integer, ForeignKey("AnalysisTbl.id"))
    loadName = Column(String(45), ForeignKey("LoadTbl.name"))


class VersionTbl(Base, BaseMixin):
    version = Column(String(40), primary_key=True)


# ======================== Sample Prep ========================
class SamplePrepWorkerTbl(Base, BaseMixin):
    name = Column(String(32), primary_key=True)
    fullname = Column(String(45))
    email = Column(String(45))
    phone = Column(String(45))
    comment = Column(String(140))


class SamplePrepSessionTbl(Base, IDMixin):
    name = Column(String(32))
    comment = Column(String(140))
    worker_name = Column(String(32), ForeignKey("SamplePrepWorkerTbl.name"))
    start_date = Column(DATE, default=func.now())
    end_date = Column(DATE)


class SamplePrepStepTbl(Base, IDMixin):
    sampleID = Column(Integer, ForeignKey("SampleTbl.id"))
    sessionID = Column(Integer, ForeignKey("SamplePrepSessionTbl.id"))
    crush = Column(String(140))
    wash = Column(String(140))
    sieve = Column(String(140))
    frantz = Column(String(140))
    acid = Column(String(140))
    heavy_liquid = Column(String(140))
    pick = Column(String(140))
    mount = stringcolumn(140)
    gold_table = stringcolumn(140)
    us_wand = stringcolumn(140)
    eds = stringcolumn(140)
    cl = stringcolumn(140)
    bse = stringcolumn(140)
    se = stringcolumn(140)

    status = Column(String(32))
    comment = Column(String(300))

    timestamp = Column(DATETIME, default=func.now())
    added = Column(Boolean)

    images = relationship("SamplePrepImageTbl", backref="step")


class SamplePrepImageTbl(Base, IDMixin):
    stepID = Column(Integer, ForeignKey("SamplePrepStepTbl.id"))
    host = stringcolumn(45)
    path = stringcolumn(45)
    timestamp = Column(DATETIME, default=func.now())
    note = Column(TEXT)


class SamplePrepChoicesTbl(Base, IDMixin):
    tag = stringcolumn(140)
    value = stringcolumn(140)


class RestrictedNameTbl(Base, IDMixin):
    name = stringcolumn()
    category = stringcolumn()


# ======================== Lab Management ========================
class IRTbl(Base, BaseMixin):
    ir = primary_key(klass=String(32))
    principal_investigatorID = Column(
        Integer, ForeignKey("PrincipalInvestigatorTbl.id")
    )
    institution = Column(String(140))
    checkin_date = Column(DATE)
    lab_contact = Column(String(140), ForeignKey("UserTbl.name"))
    comment = Column(TEXT)

    @property
    def principal_investigator_name(self):
        ret = ""
        if self.principal_investigator:
            ret = self.principal_investigator.name
        return ret


# ======================== Analysis Groups ========================
class AnalysisGroupTbl(Base, IDMixin):
    name = stringcolumn(140)
    create_date = Column(TIMESTAMP, default=func.now())
    projectID = Column(Integer, ForeignKey("ProjectTbl.id"))
    user = Column(String(140), ForeignKey("UserTbl.name"))

    sets = relationship("AnalysisGroupSetTbl", backref="group")


class AnalysisGroupSetTbl(Base, IDMixin):
    analysisID = Column(Integer, ForeignKey("AnalysisTbl.id"))
    groupID = Column(Integer, ForeignKey("AnalysisGroupTbl.id"))


class MediaTbl(Base, IDMixin):
    analysisID = Column(Integer, ForeignKey("AnalysisTbl.id"))
    url = Column(TEXT)

    username = Column(String(140), ForeignKey("UserTbl.name"))
    create_date = Column(TIMESTAMP, default=func.now())


# ======================= Current ================================
class CurrentTbl(Base, IDMixin):
    value = Column(Float(32))
    error = Column(Float(32))

    unitsID = Column(Integer, ForeignKey("UnitsTbl.id"))
    parameterID = Column(Integer, ForeignKey("ParameterTbl.id"))
    analysisID = Column(Integer, ForeignKey("AnalysisTbl.id"))

    parameter = relationship("ParameterTbl", uselist=False)
    analysis = relationship("AnalysisTbl", uselist=False, backref="current")
    units = relationship("UnitsTbl", uselist=False)


class ParameterTbl(Base, IDMixin):
    name = stringcolumn(40)


class UnitsTbl(Base, IDMixin):
    name = stringcolumn(40)


# ============= EOF =============================================
