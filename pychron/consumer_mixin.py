# ===============================================================================
# Copyright 2013 Jake Ross
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
# ============= local library imports  ==========================

# from pychron.core.ui.thread import Thread
import time
from Queue import Queue, Empty
from threading import Thread


class ConsumerMixin:
    _consumer_queue = None
    _should_consume = False
    _consume_func = None
    _main = False
    _buftime = 0
    _consumer = None
    _timeout = 0
    _delay = 0

    def __init__(self, func=None, buftime=None, auto_start=True, main=False, timeout=None, delay=1):
        super(ConsumerMixin, self).__init__()

        self.setup_consumer(func, buftime, auto_start, main, timeout, delay)

    def setup_consumer(self, func=None, buftime=None, auto_start=True, main=False, timeout=None, delay=1):
        self._delay = delay  # ms
        self._consume_func = func
        self._main = main
        self._buftime = buftime  # ms
        self._consumer_queue = Queue()
        self._consumer = Thread(target=self._consume,
                                args=(timeout,),
                                name='consumer')
        self._timeout = timeout
        self._should_consume = True
        if auto_start:
            self._consumer.setDaemon(1)
            self._consumer.start()

    def queue_size(self):
        qs = 0
        if self._consumer_queue:
            qs = self._consumer_queue.qsize()
        return qs

    def is_empty(self):
        if self._consumer_queue:
            return self._consumer_queue.empty()

    def start(self):
        self._should_consume = True
        if not self._consumer:
            self._consumer = Thread(target=self._consume,
                                    args=(self._timeout,),
                                    name='consumer')
        if not self._consumer.isAlive():
            self._consumer.setDaemon(1)
            self._consumer.start()

    def stop(self):
        if self._consumer:
            self._should_consume = False
        self._consumer = None

    start_consuming = start
    stop_consuming = stop

    def add_consumable(self, v, timeout=None):
        if not self._consumer_queue:
            self.setup_consumer(timeout=timeout)

        self._consumer_queue.put(v)

    def _consume(self, timeout):
        bt = self._buftime
        if bt:
            bt *= 1e-3

            def get_func():
                q = self._consumer_queue
                v = None
                while 1:
                    try:
                        v = q.get(timeout=bt)
                    except Empty:
                        break
                return v
        else:
            def get_func():
                try:
                    if self._consumer_queue is None:
                        print self
                    return self._consumer_queue.get(timeout=1)
                except Empty:
                    return

        cfunc = self._consume_func

        st = time.time()
        d = self._delay * 1e-3
        while self._should_consume:
            if d:
                time.sleep(d)
            if timeout:
                if time.time() - st > timeout:
                    self._should_consume = False
                    self._consumer_queue = None
                    print 'consumer time out'
                    break

            try:
                v = get_func()
                if v is not None:
                    if cfunc:
                        if self._main:
                            from pychron.core.ui.gui import invoke_in_main_thread

                            invoke_in_main_thread(cfunc, v)
                        else:
                            cfunc(v)
                    elif isinstance(v, tuple):
                        if len(v) == 3:
                            func, args, kw = v
                        else:
                            func, args = v
                            kw = {}

                        if not isinstance(args, tuple):
                            args = (args,)

                        if self._main:
                            from pychron.core.ui.gui import invoke_in_main_thread

                            invoke_in_main_thread(func, *args, **kw)
                        else:
                            func(*args)
            except Exception, e:
                import traceback

                traceback.print_exc()


class consumable(object):
    _func = None
    _consumer = None
    _main = False

    def __init__(self, func=None, main=False):
        self._func = func
        self._main = main

    def __enter__(self):
        self._consumer = c = ConsumerMixin(auto_start=False)
        c.setup_consumer(func=self._func, main=self._main)
        return c

    def __exit__(self, *args, **kw):
        self._consumer.stop()

        self._consumer._consumer_queue = None
        self._consumer._consume_func = None

        self._consumer = None
        self._func = None

# ============= EOF =============================================
