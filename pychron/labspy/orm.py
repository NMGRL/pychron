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
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, BLOB
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship
from traits.api import HasTraits, Button
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================

Base = declarative_base()

stringcolumn = lambda w=80: Column(String(w))


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__


class Version(Base, BaseMixin):
    VersionID = Column(Integer, primary_key=True)


class Device(Base, BaseMixin):
    DeviceID = Column(Integer, primary_key=True)
    Name = stringcolumn()
    processes = relationship('ProcessInfo', backref='device')


class ProcessInfo(Base, BaseMixin):
    ProcessInfoID = Column(Integer, primary_key=True)
    Name = stringcolumn()
    Units = stringcolumn()
    DeviceID = Column(Integer, ForeignKey('Device.DeviceID'))
    measurements = relationship('Measurement', backref='process')


class Measurement(Base, BaseMixin):
    MeasureID = Column(Integer, primary_key=True)
    Value = Column(Float(32))
    ProcessInfoID = Column(Integer, ForeignKey('ProcessInfo.ProcessInfoID'))


class Experiment(Base, BaseMixin):
    ExpID = Column(Integer, primary_key=True)
    Name = stringcolumn()
    Spectrometer = stringcolumn()
    ExtractionDevice = stringcolumn()
    StartTime = Column(DateTime)
    EndTime = Column(DateTime)
    State = stringcolumn()
    LastUpdate = Column(DateTime)

    analyses = relationship('Analysis')


class Analysis(Base, BaseMixin):
    AnalysisID = Column(Integer, primary_key=True)
    Runid = stringcolumn(20)
    Project = stringcolumn()
    Sample = stringcolumn()
    Timestamp = DateTime
    State = stringcolumn(20)

    Position = stringcolumn()
    Cleanup = Column(Float)
    Duration = Column(Float)
    ExtractValue = Column(Float)
    ExtractUnits = stringcolumn()
    Measurement = stringcolumn(100)
    PostMeasurement = stringcolumn(100)
    PostEquilibration = stringcolumn(100)
    Extraction = stringcolumn(100)

    ExpID = Column(Integer, ForeignKey('Experiment.ExpID'))


class Status(Base, BaseMixin):
    StatusID = Column(Integer, primary_key=True)
    ShortMessage = stringcolumn(140)
    Error = stringcolumn(140)
    Message = Column(BLOB)
    LastUpdate = Column(DateTime)

# ============= EOF =============================================



