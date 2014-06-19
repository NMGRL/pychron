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
from traits.api import HasTraits, Date
from traitsui.api import View, UItem, HGroup, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================

class DateRangeSelector(HasTraits):
    lpost = Date
    hpost = Date

    def traits_view(self):
        l = VGroup(UItem('lpost', style='custom'), label='Low', show_border=True)
        h = VGroup(UItem('hpost', style='custom'), label='High', show_border=True)
        v = View(HGroup(l, h),
                 title='Select Date Range',
                 buttons=['OK', 'Cancel'])
        return v

#============= EOF =============================================

