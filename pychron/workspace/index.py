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
#============= standard library imports ========================
#============= local library imports  ==========================
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from pychron.database.core.database_adapter import DatabaseAdapter


Base = declarative_base()


class NoSchemaError(BaseException):
    pass


class WorkspaceIndex(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__

    id = Column(Integer, primary_key=True)
    repo = Column(String(200))


class AnalysisIndex(WorkspaceIndex, Base):

    identifier = Column(String(80))
    aliquot = Column(Integer)
    increment = Column(Integer)
    cleanup = Column(Float)
    duration = Column(Float)
    extract_value = Column(Float)
    uuid = Column(String(36))

    measurement_script = Column(String(80))
    extraction_script = Column(String(80))

    mass_spectrometer = Column(String(80))
    extract_device = Column(String(80))


class IndexAdapter(DatabaseAdapter):
    schema = AnalysisIndex
    kind = 'sqlite'

    def add(self, **kw):
        if self.schema is None:
            raise NoSchemaError()

        with self.session_ctx():
            obj = self.schema(**kw)
            self._add_item(obj)



#============= EOF =============================================




