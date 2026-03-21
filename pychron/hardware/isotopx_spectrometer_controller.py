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
from traits.api import Str, HasTraits
from apptools.preferences.preference_binding import bind_preference

# ============= standard library imports ========================
from threading import RLock, Lock
from queue import Queue
import time

# ============= local library imports  ==========================

from pychron.hardware.core.core_device import CoreDevice

# import ctypes, _thread
# class mRLock(_thread.RLock):
#
#     offsetof_rlock_count = 32 # on 64-bit system
#
#     @property
#     def count(self):
#         rlock_count_b = ctypes.string_at(id(self)+self.offsetof_rlock_count, 8)
#         return int.from_bytes(rlock_count_b, 'little', signed=False)
#


class NGXController(CoreDevice):
    username = Str("")
    password = Str("")
    lock = None
    canceled = False
    triggered = False
    protect_detector = False

    def select_read(self, *args, **kw):
        return self.communicator.select_read(*args, **kw)

    def ask(self, cmd, *args, **kw):
        resp = super(NGXController, self).ask(cmd, *args, **kw)
        if any(
            (cmd.startswith(t) for t in ("GetValveStatus", "OpenValve", "CloseValve"))
        ):
            if resp and resp.strip() not in ("E00", "OPEN", "CLOSED"):
                # if resp.strip()=='E04':
                #     time.sleep(3)
                #     return "OPEN\r\n"
                # self.event_buf.push(resp)
                self.debug("retrying")
                time.sleep(0.5)
                return self.ask(cmd, *args, **kw)

        return resp

    # def read(self, *args, **kw):
    #    if self.event_buffer.empty():
    #        resp = super(NGXController, self).read(*args, **kw)
    #    else:
    #        resp = self.event_buffer.get()
    #    return resp

    def set_acquisition_buffer(self, flag):
        flag = "1" if flag else "0"
        self.debug(f"set acquisition buffer {flag}")
        self.ask(f"SAB {flag}")

    def stop_acquisition(self):
        self.triggered = False
        self.debug("stop acquisition")
        self.ask("StopAcq")
        self.canceled = True
        time.sleep(0.25)
        # self.debug(self.communicator.readline())

    def set(self, *args, **kw):
        return HasTraits.set(self, *args, **kw)

    def initialize(self, *args, **kw):
        ret = super(NGXController, self).initialize(*args, **kw)

        self.communicator.strip = False
        # trying a new locking mechanism see ngx.trigger for more details

        self.lock = Lock()
        # self.lock = mRLock()
        #   self.event_buffer = Queue()

        if ret:
            resp = self.communicator.readline()
            self.debug("*********** initial response from NGX: {}".format(resp))
            bind_preference(self, "username", "pychron.spectrometer.ngx.username")
            bind_preference(self, "password", "pychron.spectrometer.ngx.password")

            if resp:
                self.info("NGX-{}".format(resp))
                self.ask("Login {},{}".format(self.username, self.password))
            return True


# ============= EOF =============================================
