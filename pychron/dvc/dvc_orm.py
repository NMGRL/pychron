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
from sqlalchemy import Column, Integer, String, TIMESTAMP, Float, BLOB

Base = declarative_base()


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__


class NameMixin(BaseMixin):
    name = Column(String(80))


class AnalysisTbl(Base, BaseMixin):
    idanalysisTbl = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP)
    tag = Column(String(45))
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


class LevelTbl(Base, NameMixin):
    idlevelTbl = Column(Integer, primary_key=True)
    irradiationID = Column(Integer, ForeignKey('IrradiationTbl.idirradiationTbl'))
    holder = Column(String(45))
    z = Column(Float)

    positions = relationship('IrradiationPositionTbl', backref='level')

    note = Column(BLOB)


class IrradiationTbl(Base, NameMixin):
    idirradiationTbl = Column(Integer, primary_key=True)
    levels = relationship('LevelTbl', backref='irradiation')
    production = Column(String(45))


class IrradiationPositionTbl(Base, BaseMixin):
    idirradiationpositionTbl = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(80))
    sampleID = Column(Integer, ForeignKey('SampleTbl.idsampleTbl'))
    levelID = Column(Integer, ForeignKey('LevelTbl.idlevelTbl'))
    position = Column(Integer)
    analyses = relationship('AnalysisTbl', backref='irradiation_position')
    note = Column(BLOB)
    weight = Column(Float)
    j = Column(Float)
    j_err = Column(Float)

class MassSpectrometerTbl(Base, BaseMixin):
    name = Column(String(45), primary_key=True)
    kind = Column(String(45))


# ============= EOF =============================================



