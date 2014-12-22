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
from sqlalchemy import Column, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func
# ============= local library imports  ==========================
from pychron.database.core.base_orm import BaseMixin, NameMixin
from pychron.database.orms.isotope.util import foreignkey, stringcolumn

from util import Base


class flux_FluxTable(Base, BaseMixin):
    j = Column(Float)
    j_err = Column(Float)
    history_id = foreignkey('flux_HistoryTable')


class flux_MonitorTable(Base, NameMixin):
    decay_constant = Column(Float)
    decay_constant_err = Column(Float)
    age = Column(Float)
    age_err = Column(Float)
    sample_id = foreignkey('gen_SampleTable')


class flux_HistoryTable(Base, BaseMixin):
    irradiation_position_id = foreignkey('irrad_PositionTable')
    create_date = Column(DateTime, default=func.now())
    source = stringcolumn(140)

    selected = relationship('gen_LabTable',
                            backref='selected_flux_history',
                            uselist=False)
    flux = relationship('flux_FluxTable',
                        backref='history',
                        uselist=False)

# ============= EOF =============================================
