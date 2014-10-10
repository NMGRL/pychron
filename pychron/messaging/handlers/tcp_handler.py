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
from messaging_handler import MessagingHandler

class TCPHandler(MessagingHandler):
    def get_packet(self):
        """
        """
        size = self.server.datasize
        data = self.request.recv(size).strip()

        return data

    def send_packet(self, response):
        """
        """
        self._send_packet(response, self.request.send)

    #     if response is None:
    #         response = 'error'
    #
    #     totalsent = 0
    #     mlen = len(response)
    #     s = '{}\n'.format(response)
    #
    #     sock=self.request
    #     while totalsent < mlen:
    #         sent = sock.send(s[totalsent:])
    #         totalsent += sent


#============= EOF ====================================
