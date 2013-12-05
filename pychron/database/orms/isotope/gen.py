#===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
#============= standard library imports ========================
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, Integer, String, \
    ForeignKey, BLOB, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Table
#============= local library imports  ==========================

from pychron.database.core.base_orm import BaseMixin, NameMixin
# from pychron.database.core.base_orm import PathMixin, ResultsMixin, ScriptTable
from sqlalchemy.sql.expression import func
from pychron.database.orms.isotope.util import foreignkey, stringcolumn

from util import Base


class gen_LoadHolderTable(Base):
    @declared_attr
    def __tablename__(self):
        return self.__name__

    name = Column(String(80), primary_key=True)
    geometry = Column(BLOB)

    loads = relationship('loading_LoadTable', backref='holder_')


class gen_AnalysisTypeTable(Base, NameMixin):
    measurements = relationship('meas_MeasurementTable', backref='analysis_type')


class gen_DetectorTable(Base, NameMixin):
    kind = stringcolumn()
    isotopes = relationship('meas_IsotopeTable', backref='detector')
    deflections = relationship('meas_SpectrometerDeflectionsTable', backref='detector')
    intercalibrations = relationship('proc_DetectorIntercalibrationTable', backref='detector')
    detector_parameters = relationship('proc_DetectorParamTable', backref='detector')


class gen_ExtractionDeviceTable(Base, NameMixin):
    extractions = relationship('meas_ExtractionTable',
                               backref='extraction_device')
    kind = stringcolumn()
    make = stringcolumn()
    model = stringcolumn()


class gen_ImportTable(Base, BaseMixin):
    date = Column(DateTime, default=func.now())
    user = stringcolumn()
    source = stringcolumn()
    source_host = stringcolumn()
    analyses = relationship('meas_AnalysisTable')


class gen_LabTable(Base, BaseMixin):
    identifier = stringcolumn()
    #    aliquot = Column(Integer)
    sample_id = foreignkey('gen_SampleTable')

    irradiation_id = foreignkey('irrad_PositionTable')
    selected_flux_id = foreignkey('flux_HistoryTable')
    #selected_interpreted_age_id = foreignkey('proc_InterpretedAgeHistoryTable')
    note = stringcolumn(140)

    analyses = relationship('meas_AnalysisTable',
                            backref='labnumber')


class gen_MassSpectrometerTable(Base, NameMixin):
#    experiments = relationship('ExperimentTable', backref='mass_spectrometer')
    measurements = relationship('meas_MeasurementTable', backref='mass_spectrometer')
    sensitivities = relationship('gen_SensitivityTable', backref='mass_spectrometer')


class gen_MaterialTable(Base, NameMixin):
    samples = relationship('gen_SampleTable', backref='material')


class gen_MolecularWeightTable(Base, NameMixin):
    isotopes = relationship('meas_IsotopeTable', backref='molecular_weight')
    mass = Column(Float)


association_table = Table('association', Base.metadata,
                          Column('project_id', Integer, ForeignKey('gen_ProjectTable.id')),
                          Column('user_id', Integer, ForeignKey('gen_UserTable.id')),
)


class gen_ProjectTable(Base, NameMixin):
    samples = relationship('gen_SampleTable', backref='project')
    figures = relationship('proc_FigureTable', backref='project')
    users = relationship('gen_UserTable', secondary=association_table)


class gen_SampleTable(Base, NameMixin):
    material_id = foreignkey('gen_MaterialTable')
    project_id = foreignkey('gen_ProjectTable')
    labnumbers = relationship('gen_LabTable', backref='sample')


class gen_SensitivityTable(Base, BaseMixin):
    mass_spectrometer_id = foreignkey('gen_MassSpectrometerTable')
    sensitivity = Column(Float(32))
    create_date = Column(DateTime, default=func.now())
    user = stringcolumn()
    note = Column(BLOB)

    extractions = relationship('meas_ExtractionTable', backref='sensitivity')


class gen_UserTable(Base, NameMixin):
    analyses = relationship('meas_AnalysisTable', backref='user')
    #    project_id = foreignkey('gen_ProjectTable')
    projects = relationship('gen_ProjectTable', secondary=association_table)

    password = stringcolumn(80)
    salt = stringcolumn(80)

    #===========================================================================
    # permissions
    #===========================================================================
    max_allowable_runs = Column(Integer, default=25)
    can_edit_scripts = Column(Boolean, default=False)

#============= EOF =============================================
