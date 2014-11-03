# ===============================================================================
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
    ForeignKey, BLOB, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func

#============= local library imports  ==========================
from pychron.database.core.base_orm import BaseMixin
from util import Base


class loading_LoadTable(Base):
    @declared_attr
    def __tablename__(self):
        return self.__name__

    name = Column(String(80), primary_key=True)
    create_date = Column(DateTime, default=func.now())
    holder = Column(String(80), ForeignKey('gen_LoadHolderTable.name'))

    measured_positions = relationship('meas_PositionTable')
    loaded_positions = relationship('loading_PositionsTable')

    archived = Column(Boolean, default=False)


class loading_PositionsTable(Base, BaseMixin):
    load_identifier = Column(String(80), ForeignKey('loading_LoadTable.name'))
    lab_identifier = Column(Integer, ForeignKey('gen_LabTable.id'))
    position = Column(Integer)
    weight = Column(Float)
    note = Column(BLOB)


#============= EOF =============================================
