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

#========== standard library imports ==========
import time

#========== local library imports =============
from gp_actuator import GPActuator
from pychron.core.helpers.filetools import to_bool



class PychronGPActuator(GPActuator):
    '''
        
    '''
#    id_query = '*TST?'

#    def id_response(self, response):
#        if response.strip() == '0':
#            return True

#    def initialize(self, *args, **kw):
#        '''
#        '''
#        self._communicator._terminator = chr(10)
#
#        #clear and record any accumulated errors
#        errs = self._get_errors()
#        if errs:
#            self.warning('\n'.join(errs))
#        return True

#    def _get_errors(self):
#        #maximum of 10 errors so no reason to use a while loop
#
#        errors = []
#        for _i in range(10):
#            error = self._get_error()
#            if error is None:
#                break
#            else:
#                errors.append(error)
#        return errors
#
#    def _get_error(self):
#        error = None
#        cmd = 'SYST:ERR?'
#        if not self.simulation:
#            s = self.ask(cmd)
#            if s is not None:
#                if s != '+0,"No error"':
#                    error = s
#
#        return error

    def _get_valve_name(self, obj):
        if isinstance(obj, (str, int)):
            addr = obj
        else:
            addr = obj.name.split('-')[1]
        return addr

    def get_lock_state(self, obj):
        cmd = 'GetValveLockState {}'.format(self._get_valve_name(obj))
        resp = self.ask(cmd)
        if resp is not None:
            resp = resp.strip()
            boolfunc = lambda x:True if x in ['True', 'true', 'T', 't'] else False
            return boolfunc(resp)
#        return bool(random.randint(0, 1))

#    def get_lock_state(self, obj):
# #        boolfunc = lambda x:True if x in ['True', 'true', 'T', 't'] else False
#        cmd = 'GetValveLockStates'
#        resp = self.ask(cmd)
#
#        if resp is not None:
#            d = dict()
#            if ',' in resp:
#                d = dict([(r[:-1], bool(r[-1:])) for r in resp.split(',')])
#            else:
#                d = dict([(resp[i:i + 2][0], bool(int(resp[i:i + 2][1]))) for i in xrange(0, len(resp), 2)])
#            try:
#                resp = d[self._get_valve_name(obj)]
#            except KeyError, e:
#                print e
#                return False
#
#        return resp
    def get_owners_word(self, verbose=False):
        cmd = 'GetValveOwners'
        resp = self.ask(cmd, verbose=verbose)
        return resp

    def get_state_word(self, verbose=False):
        cmd = 'GetValveStates'
        resp = self.ask(cmd, verbose=verbose)
        return resp

    def get_lock_word(self, verbose=False):
        cmd = 'GetValveLockStates'
        resp = self.ask(cmd, verbose=verbose)
        return resp


    def get_channel_state(self, obj):
        '''
        Query the hardware for the channel state
         
        '''
        # returns one if channel close  0 for open
#        boolfunc = lambda x:True if x in ['True', 'true', 'T', 't'] else False
        cmd = 'GetValveState {}'.format(self._get_valve_name(obj))
        resp = self.ask(cmd)
        if resp is not None:
            resp = to_bool(resp.strip())

        return resp

    def close_channel(self, obj, excl=False):
        '''
        Close the channel
      
        '''
        cmd = 'Close {}'.format(self._get_valve_name(obj))
        resp = self.ask(cmd)
        if resp:
            if resp.lower().strip() == 'ok':
                time.sleep(0.05)
                resp = self.get_channel_state(obj) == False
        return resp

    def open_channel(self, obj):
        '''
        Open the channel
   
        '''
        cmd = 'Open {}'.format(self._get_valve_name(obj))
        resp = self.ask(cmd)
        if resp:
            if resp.lower().strip() == 'ok':
                time.sleep(0.05)
                resp = self.get_channel_state(obj) == True
#        cmd = 'ROUT:OPEN (@{})'.format(self._get_valve_name(obj))
#        self.tell(cmd)
#        if self.simulation:
#            return True
        return resp

#============= EOF =====================================
