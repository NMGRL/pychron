# ===============================================================================
# Copyright 2014 Jake Ross
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
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from traits.api import HasTraits, Button
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
Base = declarative_base()

stringcolumn = lambda w=80: Column(String(w))


class DeviceTable(Base):
    __tablename__ = 'deviceTbl'
    id = Column(Integer, primary_key=True)
    name = stringcolumn()
    processes = relationship('processvalueTbl', backref='device')


class ProcessValueTable(Base):
    __tablename__ = 'processvalueTbl'
    name = stringcolumn()
    units = stringcolumn()
    device_id = Column(Integer, ForeignKey('deviceTbl.id'))


class MeasurementTable(Base):
    __tablename__ = 'measurementTbl'
    value = Column(Float(32))
    processvalue_id = Column(Integer, ForeignKey('processvalueTbl.id'))


class ExperimentTable(Base):
    __tablename__ = 'experimentTbl'
    id = Column(Integer, primary_key=True)
    analyses = relationship('analysisTbl')


class AnalysisTable(Base):
    __tablename__ = 'analysisTbl'
    id = Column(Integer, primary_key=True)
    runid = stringcolumn(20)
    project = stringcolumn(80)
    sample = stringcolumn(80)
    timestamp = DateTime
    state = stringcolumn(20)

    position = stringcolumn(80)
    cleanup = Column(Float)
    duration = Column(Float)
    extract_value = Column(Float)
    extract_units = stringcolumn()
    measurement = stringcolumn(100)
    post_measurement = stringcolumn(100)
    post_equilibration = stringcolumn(100)
    extraction = stringcolumn(100)

    experiment_id = Column(Integer, ForeignKey('experimentTbl.id'))


class StatusTable(Base):
    __tablename__ = 'statusTbl'
    id = Column(Integer, primary_key=True)

# ============= EOF =============================================



