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

# ============= enthought library imports =======================
from pychron.globals import globalv

# ============= standard library imports ========================

# ============= local library imports  ==========================
class MessagingServer(object):
    '''
    '''
    parent = None
    allow_reuse_address = True

    def get_response(self, *args, **kw):
        if globalv.use_ipc:
            func = self.parent.repeater

        else:
            func = self.parent.processor

        return func.get_response(*args, **kw)

    def increment_packets_received(self):
        '''
        '''
        # called by handler everytime a packet is received
        self.parent.packets_received += 1

    def increment_packets_sent(self):
        '''
        '''
        self.parent.packets_sent += 1

    def increment_repeater_fails(self):
        '''
        '''
        self.parent.repeater_fails += 1

    def info(self, *args, **kw):
        '''

        '''
        self.parent.info(*args, **kw)

    def warning(self, *args, **kw):
        '''
        '''
        self.parent.warning(*args, **kw)
# ============= views ===================================

# ============= EOF ====================================
