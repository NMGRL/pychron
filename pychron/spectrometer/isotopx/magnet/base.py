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
from traits.api import Float
from pychron.spectrometer.base_magnet import BaseMagnet
from pychron.spectrometer.isotopx import IsotopxMixin


class IsotopxMagnet(BaseMagnet, IsotopxMixin):
    dacmin = Float(0.0)
    dacmax = Float(200.0)

    def read_dac(self):
        pass

    def traits_view(self):
        from traitsui.api import View, Item, VGroup
        v = View(VGroup(Item('mass'), show_border=True, label='Control'))
        return v
        
        # v = View(VGroup(VGroup(
        #                        Item('mass'),
        #                             # editor=RangeEditor(mode='slider', low_name='massmin',
        #                             #                            high_name='massmax',
        #                             #                            format='%0.3f')),
        #                        HGroup(Spring(springy=False,
        #                                      width=48),
        #                               Item('massmin', width=-40), Spring(springy=False,
        #                                                                  width=138),
        #                               Item('massmax', width=-55),
        #
        #                               show_labels=False),
        #                        show_border=True,
        #                        label='Control')))
        #
        # return v
# ============= EOF =============================================
