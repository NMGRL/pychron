# ===============================================================================
# Copyright 2018 ross
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
from traits.api import HasTraits, Instance, Str


class BaseResult(HasTraits):
    analysis = Instance('pychron.processing.analyses.analysis.Analysis')
    isotope = Str

    @property
    def record_id(self):
        r = ''
        if self.analysis:
            r = self.analysis.record_id
        return r

    @property
    def identifier(self):
        r = ''
        if self.analysis:
            r = self.analysis.identifier
        return r

    @property
    def display_uuid(self):
        r = ''
        if self.analysis:
            r = self.analysis.display_uuid
        return r
# ============= EOF =============================================
