#===============================================================================
# Copyright 2014 Jake Ross
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
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter

Base = declarative_base()


class AnalysisTable(Base):
    __tablename__ = 'activity_analysistable'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(20))
    aliquot = Column(Integer)
    step = Column(String(10))
    increment = Column(Integer)
    analysis_timestamp = Column(DateTime)
    analysis_type = Column(String(20))
    mass_spectrometer = Column(String(20))
    extract_device = Column(String(20))


class SysLoggerDatabaseAdapter(DatabaseAdapter):
    test_func = None

    def add_analysis(self, an):
        with self.session_ctx() as sess:
            kw = dict()
            for attr in ('identifier', 'aliquot', 'step', 'increment',
                         ('analysis_timestamp', 'rundate'), 'analysis_type',
                         'mass_spectrometer', 'extract_device'):
                if isinstance(attr, tuple):
                    dest, src = attr
                else:
                    dest, src = attr, attr

                kw[dest] = getattr(an, src)

            obj = AnalysisTable(**kw)
            self._add_item(obj)

#============= EOF =============================================

