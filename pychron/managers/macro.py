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



#============= enthought library imports =======================
from traits.api import HasTraits, Float
from traitsui.api import View, Item

#============= standard library imports ========================

#============= local library imports  ==========================

#============= views ===================================
#============= EOF ====================================

class Macro(HasTraits):
    '''
        G{classtree}
    '''
    _recording = False
    delay = Float(enter_set=True, auto_set=False)
    def __init__(self, *args, **kw):
        '''
            @type *args: C{str}
            @param *args:

            @type **kw: C{str}
            @param **kw:
        '''
        super(Macro, self).__init__(*args, **kw)

        self._records = []
    def start(self):
        '''
        '''
        self._recording = True
    def record_action(self, action):
        '''
            @type action: C{str}
            @param action:
        '''
        if self._recording:
            self._records.append(action)
    def stop(self):
        '''
        '''
        self._recording = False
#    def _delay_changed(self):
#        print self.delay
#
#        self.record_action(('delay',self.delay))
    def traits_view(self):
        '''
        '''
        v = View(Item('delay',
                    ),
                kind='livemodal'
                )
        return v
_Macro_ = Macro()
def start_recording():
    '''
    '''
    _Macro_.start()
def stop_recording():
    '''
    '''
    _Macro_.stop()
def play_macro():
    '''
    '''
    return _Macro_._records
def recordable(target):
    def wrapper(*args, **kw):

        _Macro_.record_action((args, kw))
        return target(*args, **kw)


    return wrapper
