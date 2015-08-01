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


# ============= local library imports  ==========================


class TxServer:
    port = 8000
    factory = None

    def bootstrap(self):
        self.start()

    def add_endpoint(self, port, factory):
        endpoint = TCP4ServerEndpoint(reactor, port)
        endpoint.listen(factory)

    def start(self):
        from threading import Thread
        Thread(target=reactor.run, args=(False,)).start()

    def stop(self):
        reactor.stop()

    kill = stop


if __name__ == '__main__':
    from pychron.tx.factories import ValveFactory

    endpoint = TCP4ServerEndpoint(reactor, 8007)
    endpoint.listen(ValveFactory())
    reactor.run()
# ============= EOF =============================================
