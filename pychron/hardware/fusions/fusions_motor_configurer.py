#===============================================================================
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
#===============================================================================



'''
@author: Jake Ross
@copyright: 2009
@license: Educational Community License 1.0
'''
#=============enthought library imports=======================
from traits.api import HasTraits, List
from traitsui.api import View, Item, Group

#=============standard library imports ========================

#=============local library imports  ==========================
class FusionsMotorConfigurer(HasTraits):
    '''
        G{classtree}
    '''
    motors = List
    def traits_view(self):
        '''
        '''

        motorgroup = Group(layout='tabbed')
        for m in self.motors:
            n = m.name
            self.add_trait(n, m)


            i = Item(n, style='custom', show_label=False)
            motorgroup.content.append(i)



        return View(motorgroup, resizable=True, title='Configure Motors',
                    buttons=['OK', 'Cancel', 'Revert'],

                    )
