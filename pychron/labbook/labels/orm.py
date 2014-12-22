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
from sqlalchemy import Integer, Column, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
# ============= standard library imports ========================
# ============= local library imports  ==========================
from sqlalchemy.orm import relationship

Base = declarative_base()

association_table = Table('AssociationTable', Base.metadata,
                          Column('path_id', Integer, ForeignKey('PathTable.id')),
                          Column('label_id', String(200), ForeignKey('LabelTable.text')))


class PathTable(Base):
    __tablename__ = 'PathTable'

    id = Column(Integer, primary_key=True)
    relpath = Column(String(200))

    labels = relationship('LabelTable', secondary=association_table, backref='paths')


class LabelTable(Base):
    __tablename__ = 'LabelTable'

    text = Column(String(200), primary_key=True)
    color = Column(String(8))  # store as RRGGBBAA in  hex

    @property
    def cnt(self):
        return len(self.paths)

# ============= EOF =============================================



