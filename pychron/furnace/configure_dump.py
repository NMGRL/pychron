# ===============================================================================
# Copyright 2016 ross
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
from traitsui.api import Controller, View, Item
class ConfigureDump(Controller):
    def traits_view(self):
        v = View(Item('dump_funnel_safety_override', tooltip='Override safety check that the funnel must be down to '
                                                             'actuate magnets'),
                 title='Configure Dump',
                 resizable=True,
                 buttons=['OK','Cancel'],
                 kind='livemodal')
        return v
# ============= EOF =============================================
