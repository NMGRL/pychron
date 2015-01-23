# ===============================================================================
# Copyright 2013 Jake Ross
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

from datetime import datetime

from sqlalchemy import Column, Integer, BLOB, Float, DateTime, func
from sqlalchemy.orm import relationship

# ============= local library imports  ==========================
from pychron.database.orms.isotope.util import foreignkey, stringcolumn
from pychron.database.core.base_orm import BaseMixin, NameMixin
from util import Base


class irrad_HolderTable(Base, NameMixin):
    levels = relationship('irrad_LevelTable', backref='holder')
    geometry = Column(BLOB)


class irrad_LevelTable(Base, NameMixin):
    z = Column(Float)
    note = Column(BLOB)

    holder_id = foreignkey('irrad_HolderTable')
    irradiation_id = foreignkey('irrad_IrradiationTable')
    production_id = foreignkey('irrad_ProductionTable')

    positions = relationship('irrad_PositionTable', backref='level')
    create_date = Column(DateTime, default=func.now())

    last_modified = Column(DateTime, onupdate=func.now())


class irrad_PositionTable(Base, BaseMixin):
    labnumber = relationship('gen_LabTable', backref='irradiation_position',
                             uselist=False)
    flux_histories = relationship('flux_HistoryTable', backref='position')

    level_id = foreignkey('irrad_LevelTable')
    position = Column(Integer)
    weight = Column(Float)


class irrad_ProductionTable(Base, NameMixin):
    K4039 = Column(Float)
    K4039_err = Column(Float)
    K3839 = Column(Float)
    K3839_err = Column(Float)
    K3739 = Column(Float)
    K3739_err = Column(Float)

    Ca3937 = Column(Float)
    Ca3937_err = Column(Float)
    Ca3837 = Column(Float)
    Ca3837_err = Column(Float)
    Ca3637 = Column(Float)
    Ca3637_err = Column(Float)

    Cl3638 = Column(Float)
    Cl3638_err = Column(Float)

    Ca_K = Column(Float)
    Ca_K_err = Column(Float)

    Cl_K = Column(Float)
    Cl_K_err = Column(Float)

    note = Column(BLOB)
    last_modified = Column(DateTime, onupdate=func.now())
    # irradiations = relationship('irrad_IrradiationTable', backref='production')
    levels = relationship('irrad_LevelTable', backref='production')


class irrad_ReactorTable(Base, NameMixin):
    note = Column(BLOB)
    address = stringcolumn(180)
    reactor_type = stringcolumn(80)
    irradiations = relationship('irrad_IrradiationTable', backref='reactor')


class irrad_IrradiationTable(Base, NameMixin):
    levels = relationship('irrad_LevelTable', backref='irradiation')
    # irradiation_production_id = foreignkey('irrad_ProductionTable')
    irradiation_chronology_id = foreignkey('irrad_ChronologyTable')
    reactor_id = foreignkey('irrad_ReactorTable')


class irrad_ChronologyTable(Base, BaseMixin):
    chronology = Column(BLOB)
    irradiation = relationship('irrad_IrradiationTable', backref='chronology')

    @property
    def start_date(self):
        """
            return date component of dose.
            dose =(pwr, %Y-%m-%d %H:%M:%S, %Y-%m-%d %H:%M:%S)

        """
        # doses = self.get_doses(tofloat=False)
        # d = datetime.strptime(doses[0][1], '%Y-%m-%d %H:%M:%S')
        # return d.strftime('%m-%d-%Y')
        # d = datetime.strptime(doses[0][1], '%Y-%m-%d %H:%M:%S')
        d = self.get_doses()[0][1]
        return d.strftime('%m-%d-%Y')

    @property
    def duration(self):
        """
            return total irradiation duration in hours
        """
        doses = self.get_doses()
        total_seconds = sum([(di[2] - di[1]).total_seconds() for di in doses])
        return total_seconds / 3600.

    def get_doses(self, todatetime=True):
        doses = self.chronology.split('$')
        # doses = [di.strip().split('%') for di in doses]
        dd = []
        for di in doses:
            pwr = 1.0
            if '|' in di:
                pwr, di = di.split('|')
                pwr = float(pwr)

            s, e = di.strip().split('%')
            dd.append((pwr, s, e))

        if todatetime:
            # def convert(x):
            #     pwr=1.0
            #     if ':' in x:
            #         pwr,x = x.split('|')
            #
            #     return pwr, datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
            convert = lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
            dd = [(p, convert(s), convert(e)) for p, s, e in dd]

        return dd

# ============= EOF =============================================
