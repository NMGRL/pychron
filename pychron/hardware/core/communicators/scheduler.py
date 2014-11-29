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
from traits.api import Float

# ============= standard library imports ========================
from threading import Lock

# ============= local library imports  ==========================
from pychron.loggable import Loggable

# SINGLE_ITEM_BUF = True
# SINGLE_ITEM_BUF=False
class CommunicationScheduler(Loggable):
    '''
    
        
        this class should be used when working with multiple rs485 devices on the same port. 
        
        it uses a simple lock and sleep cycle to avoid collision on the data lines
        
        when setting up the devices use device.set_scheduler to set the shared scheduler
        
    '''

#    collision_delay = Float(125)
    collision_delay = Float(50)

    def __init__(self, *args, **kw):
        super(CommunicationScheduler, self).__init__(*args, **kw)
        self._lock = Lock()
#        self._condition = Condition()
#        self._command_queue = Queue()
#        self._buffer = Queue()
#
#        consumer = Consumer(self._command_queue,
#                            self._buffer,
# #                            self._condition,
#                            self.collision_delay)
#        consumer.start()

    def schedule(self, func, args=None, kwargs=None):
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

#        while SINGLE_ITEM_BUF and not self._buffer.empty():
#            time.sleep(0.0001)
#
#        self._command_queue.put((func, args, kwargs))
#
#        try:
#            r = self._buffer.get(timeout=0.5)
#        except Empty:
#            r = None

        with self._lock:
            r = func(*args, **kwargs)

        return r


# class Consumer(Thread):
#
#    def __init__(self, q, b, cd):
#        Thread.__init__(self)
#        self._q = q
#        self._buf = b
# #        self.logger = add_console(name='consumer')
# #        self.cond = cond
#        self.cd = cd
#
#    def run(self):
#        while 1:
# #            self.cond.acquire()
#            while self._q.empty():
#                time.sleep(0.0001)
# #                self.cond.wait(timeout=0.05)
# #            st = time.time()
#            func, args, kwargs = self._q.get()
#
#            while SINGLE_ITEM_BUF and not self._buf.empty():
#                time.sleep(0.0001)
#
#            r = func(*args, **kwargs)
# #            self.logger.info(r)
#            self._buf.put(r)
# #            self.cond.release()
#
# #            time.sleep(self.cd/1000.)
# #            time.sleep(max(0.0001, self.cd / 1000. - (time.time() - st) - 0.001))


# ============= EOF ====================================
