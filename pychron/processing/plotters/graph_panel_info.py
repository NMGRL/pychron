# ===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
from traits.api import HasTraits, Int, Str, Property
from traitsui.api import View, Item, HGroup, VGroup, EnumEditor
#============= standard library imports ========================
#============= local library imports  ==========================
EInt = lambda x: Int(x, enter_set=True, auto_set=False)

class GraphPanelInfo(HasTraits):
    nrows = EInt(1)  # Int(1, enter_set=True, auto_set=False)
    ncols = EInt(2)  # Int(2, enter_set=True, auto_set=False)
    fixed = Str('cols')
    padding_left = EInt(40)
    padding_right = EInt(5)
    padding_top = EInt(40)
    padding_bottom = EInt(40)

    padding = Property
    def _get_padding(self):
        return [self.padding_left, self.padding_right, self.padding_top, self.padding_bottom]

    def traits_view(self):
        v = View(HGroup(
                        VGroup(
                               Item('ncols'),
                               Item('nrows'),
                               ),
                        Item('fixed',
                             show_label=False,
                             style='custom',
                             editor=EnumEditor(values=['cols', 'rows'],
                                               cols=1,
                                               )
                             ),
                        VGroup(
                               Item('padding_left', label='Left'),
                               Item('padding_right', label='Right'),
                               Item('padding_top', label='Top'),
                               Item('padding_bottom', label='Bottom'),
                               )
                        )
                 )
        return v
# ============= EOF =============================================
