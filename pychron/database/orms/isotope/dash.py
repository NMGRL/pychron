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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
from sqlalchemy import Column, DateTime, BLOB, String
from sqlalchemy.orm import relationship

# ============= local library imports  ==========================
from pychron.database.core.base_orm import BaseMixin, NameMixin
from util import Base, foreignkey


class dash_TimeTable(Base, BaseMixin):
    start = Column(DateTime)
    end = Column(DateTime)
    devices = relationship('dash_DeviceTable', backref='time_table')


class dash_DeviceTable(Base, NameMixin):
    time_table_id = foreignkey('dash_TimeTable')
    scan_blob = Column(BLOB)
    scan_fmt = Column(String(32))
    scan_meta = Column(BLOB)

# ============= EOF =============================================

