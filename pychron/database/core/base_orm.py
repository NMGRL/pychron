# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================

# ============= standard library imports ========================
from sqlalchemy import Column, Integer, String, BLOB, DateTime
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func

# ============= local library imports  ==========================
from pychron.database.core.util import foreignkey

Base = declarative_base()


class MigrateVersionTable(Base):
    __tablename__ = 'migrate_version'
    repository_id = Column(String(40), primary_key=True)
    version = Column(Integer)


class AlembicVersionTable(Base):
    __tablename__ = 'alembic_version'
    version_num = Column(String(32), primary_key=True)


class BaseMixin(object):
    def __init__(self, *args, **kw):
        super(BaseMixin, self).__init__(*args, **kw)

    @declared_attr
    def __tablename__(self):
        return self.__name__

    id = Column(Integer, primary_key=True)


class UserMixin(BaseMixin):
    @declared_attr
    def user_id(self):
        return foreignkey('gen_UserTable')


class NameMixin(BaseMixin):
    name = Column(String(80))


class ResultsMixin(BaseMixin):
    timestamp = Column(DateTime, default=func.current_timestamp())

    @declared_attr
    def path(self):
        name = self.__name__.replace('Table', 'PathTable')
        return relationship(name, uselist=False)


class RIDMixin(ResultsMixin):
    rid = Column(String(80))


class PathMixin(BaseMixin):
    root = Column(String(200))
    filename = Column(String(80))


class ScriptTable(BaseMixin):
    script_name = Column(String(80))
    script_blob = Column(BLOB)
    hash = Column(String(32))


# ============= EOF =============================================
