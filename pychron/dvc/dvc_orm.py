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
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
# ============= standard library imports ========================
# ============= local library imports  ==========================
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, Integer, String, TIMESTAMP, Float, BLOB, func, Boolean
from pychron.database.records.isotope_record import IsotopeRecordView

Base = declarative_base()


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__


class NameMixin(BaseMixin):
    name = Column(String(80))

    def __repr__(self):
        return '{}<{}>'.format(self.__class__.__name__, self.name)


class AnalysisTbl(Base, BaseMixin):
    idanalysisTbl = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP)
    tag = Column(String(45))
    uuid = Column(String(32))
    analysis_type = Column(String(45))
    aliquot = Column(Integer)
    increment = Column(Integer)

    irradiation_positionID = Column(Integer, ForeignKey('IrradiationPositionTbl.idirradiationpositionTbl'))

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

    @property
    def labnumber(self):
        return self.irradiation_position

    @property
    def analysis_timestamp(self):
        return self.timestamp

    @property
    def rundate(self):
        return self.timestamp

    def record_view(self):
        iv = IsotopeRecordView()
        iv.extract_script_name = self.extractionName
        iv.meas_script_name = self.measurementName

        iv.identifier = self.irradiation_position.identifier
        iv.labnumber = iv.identifier

        for tag in ('aliquot', 'increment', 'tag', 'uuid',
                    'extract_value', 'cleanup', 'duration',
                    'mass_spectrometer',
                    'extract_device',
                    'rundate',
                    'analysis_type'):
            setattr(iv, tag, getattr(self, tag))

        if self.irradiation_position.sample:
            iv.sample = self.irradiation_position.sample.name
            if self.irradiation_position.sample.project:
                iv.project = self.irradiation_position.sample.project.name

        return iv


class ProjectTbl(Base, NameMixin):
    idprojectTbl = Column(Integer, primary_key=True)
    samples = relationship('SampleTbl', backref='project')


class MaterialTbl(Base, NameMixin):
    idmaterialTbl = Column(Integer, primary_key=True)
    samples = relationship('SampleTbl', backref='material')


class SampleTbl(Base, NameMixin):
    idsampleTbl = Column(Integer, primary_key=True)
    materialID = Column(Integer, ForeignKey('MaterialTbl.idmaterialTbl'))
    projectID = Column(Integer, ForeignKey('ProjectTbl.idprojectTbl'))
    positions = relationship('IrradiationPositionTbl', backref='sample')


class ProductionTbl(Base, NameMixin):
    idproductionTbl = Column(Integer, primary_key=True)
    levels = relationship('LevelTbl', backref='production')


class LevelTbl(Base, NameMixin):
    idlevelTbl = Column(Integer, primary_key=True)
    irradiationID = Column(Integer, ForeignKey('IrradiationTbl.idirradiationTbl'))
    productionID = Column(Integer, ForeignKey('ProductionTbl.idproductionTbl'))
    holder = Column(String(45))
    z = Column(Float)

    positions = relationship('IrradiationPositionTbl', backref='level')

    note = Column(BLOB)


class IrradiationTbl(Base, NameMixin):
    idirradiationTbl = Column(Integer, primary_key=True)
    levels = relationship('LevelTbl', backref='irradiation')
    production = Column(String(45))


class IrradiationPositionTbl(Base, BaseMixin):
    idirradiationpositionTbl = Column(Integer, primary_key=True)
    identifier = Column(String(80))
    sampleID = Column(Integer, ForeignKey('SampleTbl.idsampleTbl'))
    levelID = Column(Integer, ForeignKey('LevelTbl.idlevelTbl'))
    position = Column(Integer)
    analyses = relationship('AnalysisTbl', backref='irradiation_position')
    note = Column(BLOB)
    weight = Column(Float)
    j = Column(Float)
    j_err = Column(Float)

    @property
    def irradiation_position(self):
        return self


class MassSpectrometerTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    kind = Column(String(45))


class ExtractDeviceTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)


class UserTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)


class LoadTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    create_date = Column(TIMESTAMP, default=func.now())
    holderName = Column(String(45), ForeignKey('LoadHolderTbl.name'))
    loaded_positions = relationship('LoadPositionTbl', backref='load')
    measured_positions = relationship('MeasuredPositionTbl', backref='load')


class LoadHolderTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    loads = relationship('LoadTbl', backref='holder')


class LoadPositionTbl(Base, BaseMixin):
    idloadpositionTbl = Column(Integer, primary_key=True)
    identifier = Column(String(45), ForeignKey('IrradiationPositionTbl.identifier'))
    position = Column(Integer)
    loadName = Column(String(45), ForeignKey('LoadTbl.name'))
    weight = Column(Float)
    note = Column(BLOB)


class MeasuredPositionTbl(Base, BaseMixin):
    idmeasuredpositionTbl = Column(Integer, primary_key=True)
    position = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)

    is_degas = Column(Boolean)
    analysisID = Column(Integer, ForeignKey('AnalysisTbl.idanalysisTbl'))
    loadName = Column(String(45), ForeignKey('LoadTbl.name'))

# ============= EOF =============================================



