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
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

# =============local library imports  ==========================
from pychron.database.core.base_orm import RIDMixin, PathMixin
Base = declarative_base()


class PowerTable(Base, RIDMixin):
    pass

class PowerPathTable(Base, PathMixin):
    power_id = Column(Integer, ForeignKey('PowerTable.id'))

# ===============================================================================
# brightness
# ===============================================================================
# class BrightnessTable(Base, ResultsMixin):
#    pass


# class BrightnessPathTable(Base, PathMixin):
#    brightness_id = Column(Integer, ForeignKey('BrightnessTable.id'))


# ============= EOF =============================================

