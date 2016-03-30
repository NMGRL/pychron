# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.error import ReactorNotRunning
# ============= local library imports  ==========================


class TxServer:
    factory = None
    _has_endpoints = False

    def bootstrap(self):
        if self._has_endpoints:
            self.start()

    def add_endpoint(self, port, factory):
        self._has_endpoints = True

        endpoint = TCP4ServerEndpoint(reactor, port)
        endpoint.listen(factory)

    def start(self):
        from threading import Thread
        t = Thread(target=reactor.run, args=(False,))
        t.setDaemon(True)
        t.start()

    def stop(self):
        try:
            reactor.stop()
        except ReactorNotRunning:
            pass

    kill = stop


if __name__ == '__main__':
    from pychron.tx.factories import ValveFactory

    endpoint = TCP4ServerEndpoint(reactor, 8007)
    endpoint.listen(ValveFactory())
    reactor.run()
# ============= EOF =============================================
