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
from traits.api import Bool, Property
# from traitsui.api import View, Item, Group, HGroup, VGroup

#============= standard library imports ========================
import time
#============= local library imports  ==========================
from base_mks_gauge import BaseMKSGauge

class IonGauge(BaseMKSGauge):
    '''
        G{classtree}
    '''
    _degas = Bool(False)
    degas = Property(depends_on='_degas')
    def _get_degas(self):
        '''
        '''
        return self._degas
    def _set_degas(self, v):
        '''
            @type v: C{str}
            @param v:
        '''
        self._degas = v
        self.set_transducer_degas()

#    def initialize(self, *args, **kw):
#        '''
#        '''
#        super(IonGauge, self).initialize(*args, **kw)
        # check filament status
#        filon = self.get_transducer_filament_state()
#        i = 0

#        while not filon:
#
#            self.logger.info('======current filament state %s===', filon)
#            filon = self._parse_response('filament', self.set_filament_state(True))
#
#
#            i += 1
#            if i > 5 or self.simulation:
#                filon = False
#                break
#            time.sleep(0.1)
#
#        if not filon:
#            self.logger.warning('****** failed to turn on filament ******')
#            self.error = 2
#            #reset error flag
#            self.error = 0
#
#        self.state = filon

    # @on_trait_change('degas')

    def set_transducer_degas(self):
        '''
        '''

        q = self._build_command(self.address, 'degas', self._degas)
        self.ask(q)

        import threading
        def degas_shutdown():
            start_time = time.time()
            # 30 min
            timeout = 30 * 60.0
            # time.sleep(timeout)

            # probably should have some loop to check state
            # instead of just sleeping
            # interm just check _degas
            while self._degas:
                time.sleep(1)
                elapse_time = (time.time() - start_time)
                if elapse_time >= timeout:
                    break

            self.logger.info('====== degas shutdown after %0.2f min======' % elapse_time / 60.)
            self._degas = False

        if self._degas:
            t = threading.Thread(target=degas_shutdown)
            t.start()

    def get_transducer_filament_state(self, **kw):
        '''
        '''

        if not self.simulation:
            t = 'filament'
            q = self._build_query(self.address, t)
            state = self._parse_response(t, self.ask(q, **kw))

        else:
            state = False
        return state

    def set_filament_state(self, onoff):
        '''
            @type of: C{str}
            @param of:
        '''
        # turn filament on
        if onoff:
            self.delay_after_power_on = True

#            #dont do anything if already on
#            if self.get_transducer_filament_state():
#                self.logger.info('======  filament already on ======')
#                return

        q = self._build_command(self.address, 'power', onoff)
        return self.ask(q)

    def set_state(self):
        '''
        '''

        self.set_filament_state(self.state)
#============= views ===================================

#============= EOF ====================================
