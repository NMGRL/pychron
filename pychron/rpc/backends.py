#===============================================================================
# Copyright 2012 Jake Ross
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
from threading import Thread
import socket
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

#============= enthought library imports =======================
#============= standard library imports ========================
try:
    import Pyro4 as pyro
except ImportError:
    pass

import subprocess
import xmlrpclib
#============= local library imports  ==========================


class RPCBackend():
    name = None

    manager = None
    _handle = None

    def _get_handle(self):
        if self._handle is None:
            self._handle = self._handle_factory()
        return self._handle

    def _handle_factory(self):
        pass

    handle = property(fget=_get_handle)

    def start_server(self):
        t = Thread(target=self._serve)
        t.setDaemon(True)
        t.start()

    def _serve(self):
        pass

class PyroBackend(RPCBackend):
    def _handle_factory(self):
        return  pyro.Proxy('PYRONAME:{}'.format(self.name))

    def _serve(self):
        try:
            ns = pyro.locateNS()
        except Exception:
            # start the name server
            func = lambda:subprocess.call(['python', '-m', 'Pyro4.naming'])
            t = Thread(target=func)
            t.start()
            i = 0
            while i < 3:
                try:
                    ns = pyro.locateNS()
                    break
                except:
                    pass

        daemon = pyro.Daemon()
        uri = daemon.register(self.manager)
        ns.register(self.manager.name, uri)
        daemon.requestLoop()

class XMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    pass

# @todo:  add security to xmlrpc
class XMLBackend(RPCBackend):
    port = None
    host = None
    log_requests = False

    def _handle_factory(self):

        obj = xmlrpclib.ServerProxy('http://{}:{}'.format(self.host,
                                                           self.port),
                              allow_none=True)
        socket.setdefaulttimeout(2)
        return obj

    def _serve(self):
        host = socket.gethostbyname(socket.gethostname())
        addr = (host, self.port)

        server = SimpleXMLRPCServer(addr, XMLRPCRequestHandler,
                                                   allow_none=True,
                                                   logRequests=self.log_requests
                                                   )

        server.register_introspection_functions()
        server.register_instance(self.manager)
        server.serve_forever()

#============= EOF =============================================
