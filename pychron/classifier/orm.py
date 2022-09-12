# ===============================================================================
# Copyright 2022 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ========== Argon Intelligence =================================
from sqlalchemy import Integer, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from pychron.dvc.dvc_orm import Base, IDMixin


class ArgonIntelligenceTbl(Base, IDMixin):
    klass = Column("klass", Integer, ForeignKey("ArgonIntelligenceClassTbl.klass"))
    analysisID = Column(Integer, ForeignKey("AnalysisTbl.id"))
    isotope = Column(String(40))

    analysis = relationship("AnalysisTbl")

class ArgonIntelligenceClassTbl(Base):
    __tablename__ = "ArgonIntelligenceClassTbl"
    klass = Column("klass", Integer, primary_key=True)
    name = Column(String(140))
    description = Column(Text)


# ============= EOF =============================================
