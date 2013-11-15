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
from SocketServer import ThreadingTCPServer
import socket
from threading import Thread
import select
#============= local library imports  ==========================
from messaging_server import MessagingServer
from pychron.messaging.handlers.tcp_handler import TCPHandler

# class TCPServer(_TCPServer, MessagingServer):
class TCPServer(ThreadingTCPServer, MessagingServer):
    '''
    '''

    def __init__(self, parent, processor_type, datasize, *args, **kw):
        '''

        '''

        self.parent = parent
        self.repeater = parent.repeater

        self.datasize = datasize
        self.processor_type = processor_type

        self.connected = True

        try:
            args += (TCPHandler,)
            super(TCPServer, self).__init__(*args, **kw)
        except socket.error, e:
            self.warning(e)
            self.connected = False

    def close_links(self):
        self._running = False

    def add_link(self, name, connection_str):
        addr, port, ptype = connection_str.split(':')
        port = int(port)
        self._running = True
        self.info('start link {}:{}'.format(addr, port))
        def listen():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#            try:

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((addr, port))
#            except:
#                return
            sock.listen(2)
            # running = True
            _input = [sock]
            while self._running:
                inputready, _outputready, _exceptready = select.select(_input, [], [], 0.25)
                for s in inputready:
                    if s == sock:
                        # handle the sock socket
                        client, _address = sock.accept()
                        _input.append(client)
                    else:
                        # handle all other sockets
                        data = None
                        try:
                            data = s.recv(1024)
                        except socket.error:
                            pass

                        if data:
                            data = data.strip()
                            self.increment_packets_received()
                            self.parent.info('Link {} Received: {}'.format(name, data))
                            self.parent.cur_rpacket = data

                            result = self.repeater.get_response(ptype, data)
                            if 'Error' in result:
                                self.increment_repeater_fails()
                            else:
                                self.repeater.led.state = 2

                            self.parent.cur_spacket = result
                            s.send(result + '\n')
                            self.parent.info('Link {} Sent: {}'.format(name, result))

                            self.increment_packets_sent()
                        else:
                            s.close()
                            _input.remove(s)
            sock.close()

        # start a listener thread
        t = Thread(target=listen)
        t.start()

#============= EOF ====================================
