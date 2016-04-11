# ===============================================================================
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
# ===============================================================================

# =============enthought library imports=======================

# =============standard library imports ========================
from sqlalchemy import Column, Integer, String, \
     ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# =============local library imports  ==========================
from pychron.database.core.base_orm import BaseMixin, ResultsMixin, PathMixin

Base = declarative_base()

class DeviceTable(Base, BaseMixin):
    name = Column(String(80))
    klass = Column(String(80))
    scans = relationship('ScanTable', backref='device')

class ScanPathTable(Base, PathMixin):
    scan_id = Column(Integer, ForeignKey('ScanTable.id'))

class ScanTable(Base, ResultsMixin):
    device_id = Column(Integer, ForeignKey('DeviceTable.id'))
    scan_timestamp = Column(DateTime, default=func.now())

# ============= EOF =============================================

