# ===============================================================================
# Copyright 2014 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traitsui.api import View, Controller, VGroup, UItem, HGroup, Heading

#============= standard library imports ========================
#============= local library imports  ==========================

class DateSelector(Controller):
    def traits_view(self):
        v = View(VGroup(VGroup(HGroup(Heading('Lower Bound'), UItem('use_low_post')),
                               UItem('low_post', style='custom', enabled_when='use_low_post')),
                        VGroup(HGroup(Heading('Upper Bound'), UItem('use_high_post')),
                               UItem('high_post', style='custom', enabled_when='use_high_post')),
                        VGroup(HGroup(Heading('Named Range'), UItem('use_named_date_range')),
                               UItem('named_date_range', enabled_when='use_named_date_range'))),
                 buttons=['OK', 'Cancel'],
                 resizable=True,
                 kind='livemodal')
        return v


#============= EOF =============================================

