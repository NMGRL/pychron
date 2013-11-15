#===============================================================================
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
#===============================================================================



from sqlalchemy import Table, Column, Integer, MetaData


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    inter = Table('intercepts', meta, autoload=True)
    fit40 = Column('fit40', Integer)
    fit39 = Column('fit39', Integer)
    fit38 = Column('fit38', Integer)
    fit37 = Column('fit37', Integer)
    fit36 = Column('fit36', Integer)

    fit40.create(inter)
    fit39.create(inter)
    fit38.create(inter)
    fit37.create(inter)
    fit36.create(inter)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    inter = Table('intercepts', meta, autoload=True)

    inter.c.fit40.drop()
    inter.c.fit39.drop()
    inter.c.fit38.drop()
    inter.c.fit37.drop()
    inter.c.fit36.drop()
