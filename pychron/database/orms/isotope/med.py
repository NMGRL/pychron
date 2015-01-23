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
# from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, BLOB, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func

# ============= local library imports  ==========================
from pychron.database.orms.isotope.util import foreignkey, stringcolumn
from pychron.database.core.base_orm import BaseMixin, NameMixin

from util import Base


class med_ImageTable(Base, NameMixin):
    create_date = Column(DateTime, default=func.now())
    image = Column(BLOB)
    extractions = relationship('meas_ExtractionTable', backref='image')


class med_SnapshotTable(Base, BaseMixin):
    path = stringcolumn(200)
    remote_path = stringcolumn(200)
    create_date = Column(DateTime, default=func.now())
    image = Column(BLOB)
    extraction_id = foreignkey('meas_ExtractionTable')


class med_SampleImageTable(Base, NameMixin):
    create_date = Column(DateTime, default=func.now())
    image = Column(BLOB)
    sample_id = foreignkey('gen_SampleTable')
    note = Column(BLOB)
# ============= EOF =============================================
