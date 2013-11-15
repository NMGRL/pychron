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

#============= standard library imports ========================

#============= local library imports  ==========================
from SocketServer import BaseRequestHandler
from pychron.remote_hardware.errors.error import ErrorCode

class MessagingHandler(BaseRequestHandler):
    _verbose = False
    def handle(self):
        '''
        '''
        data = self.get_packet()

        if data is not None:
            if self._verbose:
                self.server.info('Received: %s' % data.strip())

            try:
                addr = self.client_address[0]
            except IndexError:
                addr = self.client_address

            response = self.server.get_response(self.server.processor_type, data, addr)

            if response is not None:
                self.send_packet(response)

            if 'ERROR 6' in response:
                self.server.increment_repeater_fails()
#
            if self._verbose:
                self.server.info('Sent: %s' % response.strip())

            self.server.parent.cur_rpacket = data
            self.server.parent.cur_spacket = response

            self.server.increment_packets_received()
            self.server.increment_packets_sent()

    def get_packet(self):
        '''
        '''
        pass

    def send_packet(self):
        '''
        '''
        pass
#============= EOF ====================================
