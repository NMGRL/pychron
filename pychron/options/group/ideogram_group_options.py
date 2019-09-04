# ===============================================================================
# Copyright 2015 Jake Ross
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

from enable.markers import MarkerTrait
# ============= enthought library imports =======================
from traits.api import Range
from traitsui.api import View, UItem, Item, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.options.group.base_group_options import BaseGroupOptions


class IdeogramGroupOptions(BaseGroupOptions):
    marker_size = Range(0.0, 10.0, 1.0, mode='spinner')
    marker = MarkerTrait

    def marker_non_default(self):
        return self.marker != 'square'

    def marker_size_non_default(self):
        return self.marker_size != 1

    def traits_view(self):
        fill_grp = BorderVGroup(HGroup(UItem('use_fill'),
                                       UItem('color')),
                                Item('alpha', label='Opacity'),
                                label='Fill')

        line_grp = BorderVGroup(UItem('line_color'),
                                Item('line_width',
                                     label='Width'),
                                label='Line')

        mgrp = BorderHGroup(UItem('marker'),
                            UItem('marker_size'),
                            label='Marker')

        g = BorderVGroup(Item('bind_colors', label='Bind Colors',
                              tooltip='Bind the Fill and Line colors, i.e changing the Fill color changes'
                                      'the line color and vice versa'),
                         HGroup(fill_grp, line_grp, mgrp),
                         label='Group {}'.format(self.group_id + 1))
        v = View(g)
        return v

# ============= EOF =============================================
