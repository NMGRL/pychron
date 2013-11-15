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



from sqlalchemy import MetaData, Table, Column, Integer, Float

meta = MetaData()
intercepts = Table('intercepts', meta,
                 Column('id', Integer, primary_key=True),
                 Column('analysis_id', Integer),
                 Column('m40', Float),
                 Column('m39', Float),
                 Column('m38', Float),
                 Column('m37', Float),
                 Column('m36', Float),
                 Column('m40er', Float),
                 Column('m39er', Float),
                 Column('m38er', Float),
                 Column('m37er', Float),
                 Column('m36er', Float),
                 )


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    intercepts.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    intercepts.drop()
