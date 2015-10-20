# ===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.helpers.color_generators import colornames
from pychron.core.ui import set_qt

set_qt()
# ============= enthought library imports =======================
from traits.api import HasTraits, List, Bool, Int, Color, Range
from traitsui.api import View, Item, HGroup, VGroup, UItem, ListEditor, InstanceEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
class Fill(HasTraits):
    use_filled_line = Bool
    color = Color
    alpha = Range(0.0, 100.0)
    group_id = Int

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('use_filled_line'),
                               Item('color', enabled_when='use_filled_line')),
                        Item('alpha', label='Opacity'),
                        show_border=True,
                        label='Group {}'.format(self.group_id + 1)))

        return v

    def simple_view(self):
        v = View(VGroup(HGroup(UItem('use_filled_line'),
                               Item('color', enabled_when='use_filled_line')),
                        Item('alpha')))
        return v


class FillGroupEditor(HasTraits):
    fill_groups = List

    def traits_view(self):
        v = View(UItem('fill_groups',
                       style='custom',
                       editor=ListEditor(mutable=False,
                                         style='custom',
                                         editor=InstanceEditor())),
                 buttons=['OK', 'Cancel', 'Revert'],
                 kind='livemodal', resizable=True,
                 height=700,
                 title='Ideogram Fills'
                 )
        return v


if __name__ == '__main__':
    eg = FillGroupEditor()
    eg.fill_groups =[Fill(group_id=i,
                          alpha=100,
                          color=colornames[i+1]) for i in range(10)]

    #[Fill(group_id=0), Fill(group_id=1), Fill(group_id=2)]
    eg.configure_traits()
# ============= EOF =============================================

