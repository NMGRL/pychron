# ===============================================================================
# Copyright 2017 ross
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
from traits.api import HasTraits, Bool
from traitsui.api import View

from pychron.pipeline.nodes.base import BaseNode


class ReportOptions(HasTraits):
    blank_unknowns_enabled = Bool
    airs_enabled = Bool
    cocktails_enabled = Bool
    blank_unknowns_enabled = Bool

    def traits_view(self):
        v = View()
        return v




class ReportNode(BaseNode):
    options_klass = ReportOptions
    def run(self, state):
        print 'asdfasdf'

# ============= EOF =============================================
