# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================


# =============enthought library imports=======================

# =============standard library imports ========================

import os

from sqlalchemy import Column, Integer, Float, String, \
    ForeignKey, DateTime, Date, BLOB, Enum, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, relationship
from sqlalchemy.sql.expression import func

# =============local library imports  ==========================
from pychron.database.orms.isotope.util import doublecolumn

Base = declarative_base()

DBVERSION = float(os.environ.get('MassSpecDBVersion', 16.3))


class AnalysesChangeableItemsTable(Base):
    __tablename__ = 'AnalysesChangeableItemsTable'
    ChangeableItemsID = Column(Integer, primary_key=True)
    # AnalysisID = Column(Integer, ForeignKey('AnalysesTable.AnalysisID'))
    DataReductionSessionID = Column(Integer, ForeignKey('DataReductionSessionTable.DataReductionSessionID'))
    History = Column(String, default='')
    StatusReason = Column(Integer, default=0)
    StatusLevel = Column(Integer, default=0)
    SignalNormalizationFactor = Column(Float, default=1)
    PreferencesSetID = Column(Integer, ForeignKey('PreferencesTable.PreferencesSetID'))
    Comment = Column(String(255))
    analyses = relationship('AnalysesTable', backref='changeable')


class AnalysisPositionTable(Base):
    __tablename__ = 'AnalysisPositionTable'
    PositionID = Column(Integer, primary_key=True)
    AnalysisID = Column(Integer, ForeignKey('AnalysesTable.AnalysisID'))
    PositionOrder = Column(Integer, default=1)
    Hole = Column(Integer)
    X = Column(Float(32), default=0)
    Y = Column(Float(32))


class AnalysesTable(Base):
    __tablename__ = 'AnalysesTable'
    AnalysisID = Column(Integer, primary_key=True)
    RID = Column(String(40))

    IrradPosition = Column(Integer, ForeignKey('IrradiationPositionTable.IrradPosition'))
    Aliquot = Column(String(10))
    Aliquot_pychron = Column(Integer)

    Increment = Column(String(20))
    SpecParametersID = Column(Integer, default=0)
    RunScriptID = Column(Integer, ForeignKey('RunScriptTable.RunScriptID'))

    HeatingItemName = Column(String(80))
    FinalSetPwr = Column(Float, default=0)
    PwrAchieved = Column(Float, default=0)
    PwrAchievedSD = Column(Float, default=0)
    PwrAchieved_Max = Column(Float, default=0)
    TotDurHeating = Column(Integer)
    TotDurHeatingAtReqPwr = Column(Integer)

    FirstStageDly = Column(Integer)
    SecondStageDly = Column(Integer)

    DetInterCalibID = Column(Integer, default=0)
    AssociatedProjectID = Column(Integer, default=0)
    TrapCurrent = Column(Float, default=0)
    ManifoldOpt = Column(Integer, default=0)
    OriginalImportID = Column(String(1), default=0)
    RedundantSampleID = Column(Integer, ForeignKey('SampleTable.SampleID'))
    if DBVERSION >= 16.3:
        RedundantUserID = Column(Integer, ForeignKey('UserTable.UserID'))

    SampleLoadingID = Column(Integer, ForeignKey('SampleLoadingTable.SampleLoadingID'))
    ChangeableItemsID = Column(Integer, ForeignKey('AnalysesChangeableItemsTable.ChangeableItemsID'), default=0)

    LastSaved = Column(DateTime)
    RunDateTime = Column(DateTime)
    LoginSessionID = Column(Integer, ForeignKey('LoginSessionTable.LoginSessionID'))
    SpecRunType = Column(Integer)

    if DBVERSION >= 16.3:
        SignalRefIsot = Column(String(length=30))
    else:
        ReferenceDetectorLabel = Column(String(40))

    RefDetID = Column(Integer, ForeignKey('DetectorTable.DetectorID'))

    PipettedIsotopes = Column(BLOB)

    isotopes = relation('IsotopeTable', backref='AnalysesTable')
    araranalyses = relation('ArArAnalysisTable')
    #    araranalyses = relation('ArArAnalysisTable', backref='AnalysesTable')
    # changeable = relationship('AnalysesChangeableItemsTable',
    #                           backref='AnalysesTable',
    #                           uselist=False)
    positions = relationship('AnalysisPositionTable')
    runscript = relationship('RunScriptTable', uselist=False)


class ArArAnalysisTable(Base):
    """
    WARNING
    the totals are not raw values and have been blank, discrimination and decay corrected already
    """
    __tablename__ = 'ArArAnalysisTable'
    #    AnalysisID = Column(Integer, primary_key=True)
    AnalysisID = Column(Integer, ForeignKey('AnalysesTable.AnalysisID'))
    DataReductionSessionID = Column(Integer)
    JVal = doublecolumn()  # Column(Float, default=0)
    JEr = doublecolumn()  # Column(Float, default=0)
    Tot40 = doublecolumn()
    Tot39 = doublecolumn()
    Tot38 = doublecolumn()
    Tot37 = doublecolumn()
    Tot36 = doublecolumn()

    Tot40Er = doublecolumn()
    Tot39Er = doublecolumn()
    Tot38Er = doublecolumn()
    Tot37Er = doublecolumn()
    Tot36Er = doublecolumn()

    Age = doublecolumn(primary_key=True)
    ErrAge = doublecolumn()
    ErrAgeWOErInJ = doublecolumn()
    PctRad = doublecolumn()
    PctRadEr = doublecolumn()


class BaselinesChangeableItemsTable(Base):
    __tablename__ = 'BaselinesChangeableItemsTable'
    BslnID = Column(Integer, primary_key=True)
    #    BslnID = Column(Integer, index=True)
    #    BslnID = ForeignKey('baselinestable.BslnID')
    #    BslnID = Column(Integer, ForeignKey('baselinestable.BslnID'), primary_key=True)
    Fit = Column(Integer, ForeignKey('FitTypeTable.Fit'))
    DataReductionSessionID = Column(Integer)
    InfoBlob = Column(BLOB)
    PDPBlob = Column(BLOB)


class BaselinesTable(Base):
    __tablename__ = 'BaselinesTable'
    BslnID = Column(Integer, primary_key=True)
    Label = Column(String(40))
    NumCnts = Column(Integer)
    PeakTimeBlob = Column(BLOB, nullable=True)
    isotope = relationship('IsotopeTable', backref='baseline', uselist=False)


# changeable_item = relationship('baselineschangeableitemstable', uselist=False)

class DatabaseVersionTable(Base):
    __tablename__ = 'DatabaseVersionTable'
    Version = Column(Float, primary_key=True)


class DataReductionSessionTable(Base):
    __tablename__ = 'DataReductionSessionTable'
    DataReductionSessionID = Column(Integer, primary_key=True)
    SessionDate = Column(DateTime)
    # changeable_items = relationship('AnalysesChangeableItemsTable')


class DetectorTable(Base):
    __tablename__ = 'DetectorTable'
    DetectorID = Column(Integer, primary_key=True)
    DetectorTypeID = Column(Integer, ForeignKey('DetectorTypeTable.DetectorTypeID'))
    EMV = Column(Float, default=0)
    Gain = Column(Float, default=0)
    Disc = Column(Float, default=1)
    DiscEr = Column(Float, default=0)
    ICFactor = Column(Float, default=1)
    ICFactorEr = Column(Float, default=0)
    ICFactorSource = Column(Integer, default=1)
    IonCounterDeadtimeSec = Column(Float, default=0)

    isotopes = relationship('IsotopeTable', backref='detector')
    if DBVERSION >= 16.3:
        analyses = relationship('AnalysesTable', backref='reference_detector')
    else:
        Label = Column(String(40))


class DetectorTypeTable(Base):
    __tablename__ = 'DetectorTypeTable'
    DetectorTypeID = Column(Integer, primary_key=True)
    Label = Column(String(40))
    ResistorValue = Column(Float, default=None)
    ScaleFactor = Column(Float, default=None)

    detectors = relationship('DetectorTable', backref='detector_type')


class IrradiationPositionTable(Base):
    __tablename__ = 'IrradiationPositionTable'

    IrradPosition = Column(Integer, primary_key=True)
    IrradiationLevel = Column(String(40))
    HoleNumber = Column(Integer)
    Material = Column(String(40), ForeignKey('MaterialTable.Material'))
    SampleID = Column(Integer, ForeignKey('SampleTable.SampleID'))

    StandardID = Column(Integer, default=0)
    Size = Column(String(40), default='NULL')
    Weight = Column(Float, default=0)
    Note = Column(String(255), nullable=True)
    LabActivation = Column(Date, default=func.now())
    J = Column(Float, nullable=True)
    JEr = Column(Float, nullable=True)

    analyses = relationship('AnalysesTable', backref='irradiation_position')


class IrradiationLevelTable(Base):
    __tablename__ = 'IrradiationLevelTable'
    IrradBaseID = Column(String(80), index=True, unique=False, primary_key=True)
    Level = Column(String(80), index=True, unique=False, primary_key=True)

    SampleHolder = Column(String(40))
    ProductionRatiosID = Column(Integer, ForeignKey('IrradiationProductionTable.ProductionRatiosID'))
    ExperimentType = Column(Integer, default=1)


class IrradiationProductionTable(Base):
    __tablename__ = 'IrradiationProductionTable'
    ProductionRatiosID = Column(Integer, primary_key=True)
    K4039 = Column(Float)
    K4039Er = Column(Float)
    K3839 = Column(Float)
    K3839Er = Column(Float)
    K3739 = Column(Float)
    K3739Er = Column(Float)

    Ca3937 = Column(Float)
    Ca3937Er = Column(Float)
    Ca3837 = Column(Float)
    Ca3837Er = Column(Float)
    Ca3637 = Column(Float)
    Ca3637Er = Column(Float)

    P36Cl38Cl = Column(Float)
    P36Cl38ClEr = Column(Float)
    CaOverKMultiplier = Column(Float)
    CaOverKMultiplierEr = Column(Float)
    ClOverKMultiplier = Column(Float)
    ClOverKMultiplierEr = Column(Float)

    Label = Column(String(80))
    levels = relationship('IrradiationLevelTable', backref='production')

    @property
    def Cl3638(self):
        return self.P36Cl38Cl


class IrradiationChronologyTable(Base):
    __tablename__ = 'IrradiationChronologyTable'
    IrradBaseID = Column(String(80), primary_key=True)
    StartTime = Column(DateTime, primary_key=True)
    EndTime = Column(DateTime, primary_key=True)


class IsotopeResultsTable(Base):
    """
    iso = intercept - bkgrd
    """
    __tablename__ = 'IsotopeResultsTable'
    Counter = Column(Integer, primary_key=True)
    LastSaved = Column(DateTime)
    IsotopeID = Column(Integer, ForeignKey('IsotopeTable.IsotopeID'))
    DataReductionSessionID = Column(Integer)
    InterceptEr = Column(Float)
    Intercept = Column(Float)
    Iso = Column(Float)
    IsoEr = Column(Float)
    CalibMolesPerSignalAtUnitGain = Column(Float)
    CalibMolesPerSignalAtUnitGainEr = Column(Float)
    SensCalibMoles = Column(Float)
    SensCalibMolesEr = Column(Float)
    VolumeCalibFactor = Column(Float)
    VolumeCalibFactorEr = Column(Float)
    VolumeCalibratedValue = Column(Float)
    VolumeCalibratedValueEr = Column(Float)
    Bkgd = Column(Float)
    BkgdEr = Column(Float)
    BkgdDetTypeID = Column(Integer)
    PkHtChangePct = Column(Float)
    #    Fit = Column(Integer)
    Fit = Column(Integer, ForeignKey('FitTypeTable.Fit'))

    GOF = Column(Float)
    # PeakScaleFactor = Column(Float)


class IsotopeTable(Base):
    __tablename__ = 'IsotopeTable'
    IsotopeID = Column(Integer, primary_key=True)
    if DBVERSION >= 16.3:
        TypeID = Column(Integer, default=1)
    AnalysisID = Column(Integer, ForeignKey('AnalysesTable.AnalysisID'))
    DetectorID = Column(Integer, ForeignKey('DetectorTable.DetectorID'))
    BkgdDetectorID = Column(Integer, nullable=True)
    Label = Column(String(40))
    NumCnts = Column(Integer)
    NCyc = Column(Integer, nullable=True)
    # CycleStartIndexList
    # CycleStartIndexblob
    BslnID = Column(Integer, ForeignKey('BaselinesTable.BslnID'))
    RatNumerator = Column(Integer, nullable=True)
    RatDenominator = Column(Integer, nullable=True)
    HallProbeAtStartOfRun = Column(Float, nullable=True)
    HallProbeAtEndOfRun = Column(Float, nullable=True)

    #    peak_time_series = relation('PeakTimeTable', uselist=False)
    peak_time_series = relation('PeakTimeTable')

    results = relationship('IsotopeResultsTable', backref='isotope')


class FittypeTable(Base):
    __tablename__ = 'FitTypeTable'
    Fit = Column(Integer, primary_key=True)
    Label = Column(String(40))
    results = relationship('IsotopeResultsTable', backref='fit')


# baseline_results = relationship('baselineschangeableitemstable', backref='fit',
# #                          uselist=False
#                          )


class LoginSessionTable(Base):
    __tablename__ = 'LoginSessionTable'
    LoginSessionID = Column(Integer, primary_key=True)
    SpecSysN = Column(Integer, ForeignKey('MachineTable.SpecSysN'))
    analyses = relationship('AnalysesTable', backref='login_session')
    UserID = Column(Integer, default=1)
    SessionStart = Column(DateTime, default=func.now())


class MachineTable(Base):
    __tablename__ = 'MachineTable'
    SpecSysN = Column(Integer, primary_key=True)
    Label = Column(String(80))

    logins = relationship('LoginSessionTable', backref='machine')


class MaterialTable(Base):
    __tablename__ = 'MaterialTable'
    ID = Column(Integer, primary_key=True)
    Material = Column(String(40))

    irradpositions = relation('IrradiationPositionTable')


class MolecularWeightTable(Base):
    __tablename__ = 'MolarWeightTable'
    ID = Column(Integer, primary_key=True)
    Species = Column(String(40))
    AtomicWeight = Column(Float)


class PDPTable(Base):
    __tablename__ = 'PDPTable'
    IsotopeID = Column(Integer, primary_key=True)
    LastSaved = Column(TIMESTAMP)
    PDPBlob = Column(BLOB)


class PeakTimeTable(Base):
    __tablename__ = 'PeakTimeTable'
    Counter = Column(Integer, primary_key=True)
    PeakTimeBlob = Column(BLOB)
    IsotopeID = Column(Integer, ForeignKey('IsotopeTable.IsotopeID'))
    PeakNeverBslnCorBlob = Column(BLOB)


class PreferencesTable(Base):
    __tablename__ = 'PreferencesTable'
    PreferencesSetID = Column(Integer, primary_key=True)
    DelOutliersAfterFit = Column(Enum)
    NFilterIter = Column(Integer)
    OutlierSigmaFactor = Column(Float)
    changeable_items = relationship('AnalysesChangeableItemsTable', backref='preferences_set')


class ProjectTable(Base):
    __tablename__ = 'ProjectTable'
    ProjectID = Column(Integer, primary_key=True)
    Project = Column(String(40))
    samples = relationship('SampleTable', backref='project')
    PrincipalInvestigator = Column(String(80))


class RunScriptTable(Base):
    __tablename__ = 'RunScriptTable'
    RunScriptID = Column(Integer, primary_key=True)
    Label = Column(String(40))
    TheText = Column(BLOB)
    Note = Column(BLOB, default='')


class SampleTable(Base):
    __tablename__ = 'SampleTable'
    SampleID = Column(Integer, primary_key=True)
    Sample = Column(String(40))

    # Project = Column(String(40))  # , ForeignKey('ProjectTable.Project'))
    #    Project = relation('ProjectTable', backref = 'SampleTable')
    ProjectID = Column(Integer, ForeignKey('ProjectTable.ProjectID'))
    Note = Column(String(40), default='NULL')
    AlternateUserID = Column(String(40), default='NULL')
    CollectionDateTime = Column(DateTime, default=func.now())
    # Coordinates = Column(BLOB, default='NULL')
    Latitude = Column(String(40), default='NULL')
    Longitude = Column(String(40), default='NULL')
    Salinity = Column(Float, default=0)
    Temperature = Column(Float, default=0)

    irradpositions = relationship('IrradiationPositionTable', backref='sample')
    analyses = relation('AnalysesTable', backref='sample')


class SampleLoadingTable(Base):
    __tablename__ = 'SampleLoadingTable'
    SampleLoadingID = Column(Integer, primary_key=True)
    SampleHolder = Column(String(40))
    SpecSysN = Column(Integer)
    LoadingDate = Column(DateTime, default=func.now())

    analyses = relationship('AnalysesTable', backref='sample_loading')


class UserTable(Base):
    __tablename__ = 'UserTable'
    UserID = Column(Integer, primary_key=True)
    UserName = Column(String(length=60))
