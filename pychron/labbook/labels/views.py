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
# ===============================================================================
from pychron.core.ui import set_qt

set_qt()
# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Color
from traitsui.api import View, UItem, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================


class NewLabelView(HasTraits):
    text = Str
    color = Color

    @property
    def color_str(self):
        f = lambda x: '{:X}'.format(x).zfill(2)
        color = self.color
        args = map(f, (color.red(), color.green(), color.blue(), color.alpha()))
        return ''.join(args)

    def traits_view(self):
        v = View(VGroup(UItem('text'),
                        UItem('color')),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 width=500, height=500,
                 resizable=True,
                 title='New Label')
        return v


if __name__ == '__main__':
    nv = NewLabelView()
    nv.configure_traits()
    print nv.color_str
# ============= EOF =============================================



