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
from sqlalchemy import Column, Integer, BLOB, Float, DateTime
from sqlalchemy.orm import relationship
# ============= local library imports  ==========================

from pychron.database.core.base_orm import BaseMixin
# from pychron.database.core.base_orm import PathMixin, ResultsMixin, ScriptTable
from sqlalchemy.sql.expression import func
from pychron.database.orms.isotope.util import foreignkey

from util import Base


class spec_MassCalHistoryTable(Base, BaseMixin):
    create_date = Column(DateTime, default=func.now())
    spectrometer_id = Column(Integer)

    scans = relationship('spec_MassCalScanTable', backref='history')


class spec_MassCalScanTable(Base, BaseMixin):
    history_id = foreignkey('spec_MassCalHistoryTable')
    blob = Column(BLOB)
    center = Column(Float)
    molecular_weight_id = foreignkey('gen_MolecularWeightTable')


class spec_MFTableTable(Base, BaseMixin):
    spectrometer_id = foreignkey('gen_MassSpectrometerTable')
    blob = Column(BLOB)
    create_date = Column(DateTime, default=func.now())

# ============= EOF =============================================
