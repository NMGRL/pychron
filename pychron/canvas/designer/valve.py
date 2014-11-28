# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import HasTraits, Bool, String, Float, Property
from traitsui.api import View, Item, HGroup

#============= standard library imports ========================

#============= local library imports  ==========================
class Valve(HasTraits):
    '''
    '''
    pos = Property(depends_on='_x,_y')
    _x = Float(enter_set=True, auto_set=False)
    _y = Float(enter_set=True, auto_set=False)
    name = String
    state = Bool
    identify = Bool
    selected = Bool
    soft_lock = Bool

    def _get_pos(self):
        '''
        '''
        return self._x, self._y

    def _set_pos(self, pos):
        '''
        '''
        self._x = float(pos[0])
        self._y = float(pos[1])

    def traits_view(self):
        '''
        '''
        return View('name', 'identify',
                     HGroup(Item('_x', format_str='%0.2f'), Item('_y', format_str='%0.2f')),
                    buttons=['OK', 'Cancel']
                                 )
#============= views ===================================
#============= EOF ====================================
