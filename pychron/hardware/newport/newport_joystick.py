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



# =============enthought library imports=======================
from traits.api import HasTraits, Any, Property, List
from traitsui.api import View, Item, Group, VGroup

# =============standard library imports ========================

# =============local library imports  ==========================
def validate(v):
    '''
    '''
    try:
        v = int(v)
    except:
        v = 0

    return v

class Joystick(HasTraits):
    '''
        G{classtree}
    '''
    parent = Any
    xnegative = Property(fvalidate=validate)
    xpositive = Property(fvalidate=validate)

    ynegative = Property(fvalidate=validate)
    ypositive = Property(fvalidate=validate)

    znegative = Property(fvalidate=validate)
    zpositive = Property(fvalidate=validate)
    high_low_bit = Property
    dio_bits = List

    def _get_high_low_bit(self):
        '''
        '''
        return self.dio_bits[0][2]

    def _set_high_low_bit(self, v):
        '''
            
        '''
        for d in self.dio_bits:
            d[2] = v
        self.enable()

    def _get_xnegative(self):
        '''
        '''
        return self.dio_bits[0][0]
    def _get_ynegative(self):
        '''
        '''
        return self.dio_bits[1][0]
    def _get_znegative(self):
        '''
        '''
        return self.dio_bits[2][0]
    def _get_xpositive(self):
        '''
        '''
        return self.dio_bits[0][1]
    def _get_ypositive(self):
        '''
        '''
        return self.dio_bits[1][1]
    def _get_zpositive(self):
        '''
        '''
        return self.dio_bits[2][1]

    def _set_xnegative(self, v):
        '''
           
        '''
        self.dio_bits[0][0] = v
        self.enable()
    def _set_ynegative(self, v):
        '''
            
        '''
        self.dio_bits[1][0] = v
        self.enable()
    def _set_znegative(self, v):
        '''
            
        '''
        self.dio_bits[2][0] = v
        self.enable()
    def _set_xpositive(self, v):
        '''
            
        '''
        self.dio_bits[0][1] = v
        self.enable()
    def _set_ypositive(self, v):
        '''
            
        '''
        self.dio_bits[1][1] = v
        self.enable()
    def _set_zpositive(self, v):
        '''
            
        '''
        self.dio_bits[2][1] = v
        self.enable()

    def load_parameters(self, f):
        '''
        '''
        lines = [line[:-1] for line in f if (line[0] != chr(13) and line[0] != '#')]

        for i in range(3):
            self.dio_bits.append([int(a) for a in lines[i].split(',')])


    def disable(self):
        '''
        '''
        com = ';'.join([self.parent._build_command_('BQ', xx=a.id, nn=0) for a in self.parent.axes])[:-1]
        self.parent.ask(com)
        com = ';'.join([self.parent._build_command_('TJ', xx=a.id, nn=1) for a in self.parent.axes])[:-1]
        self.parent.ask(com)

    def enable(self):
        '''
        '''
        self.parent.destroy_group()

        self.parent.ask('BO0')
        args = [
               ('BP', None, 'assign dio bits'),
           ('BQ', 1, 'enable dio bits'),
         #  ('SI',100,'set update jog velocity interval (milliseconds)'),
         #  ('SK',[0.5,0], 'set scaling coefficients'),
           ('TJ', 3, 'set trajectory mode to jog')
         ]
#        bits=[[12,13],[14,15],[16,17]]

        coms = []
        for a in self.parent.axes:
            for ai in args:
                nn = ai[1]
                if ai[0] == 'BP':
                    nn = self.dio_bits[a.id - 1]
                coms.append(self.parent._build_command_(ai[0], xx=a.id, nn=nn))

        com = ';'.join(coms)

        self.parent.ask(com)



    def traits_view(self):
        '''
        '''
        dio_group = Group()
        for a in ['x', 'y', 'z']:
            i = VGroup(Item('%snegative' % a), Item('%spositive' % a))
            dio_group.content.append(i)

        dio_group.content.append(Item('high_low_bit'))
        return View(dio_group,
                   resizable=True)
