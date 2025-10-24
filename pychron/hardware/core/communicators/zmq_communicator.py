# ===============================================================================
# Copyright 2023 ross
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
import zmq

from pychron.hardware.core.communicators.communicator import Communicator


class ZmqCommunicator(Communicator):
    def open(self, *args, **kw):
        context = zmq.Context()
        sock = context.socket(zmq.REQ)
        sock.connect(f"tcp://{self.address}")

        self.handle = sock

    def ask(self, msg, verbose=True, *args, **kw):
        self.handle.send_json(msg)
        resp = self.handle.recv_json()
        if verbose:
            self.debug(f"{msg} => {resp}")

        return resp


# ============= EOF =============================================
