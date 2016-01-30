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
# from traits.api import HasTraits, on_trait_change, Str, Int, Float, Button
# from traitsui.api import View, Item, Group, HGroup, VGroup
import time
from threading import Thread

# from collections import Counter
import random
from pychron.loggable import Loggable
# ============= standard library imports ========================

# ============= local library imports  ==========================


class Message(object):
    request = None
    response = None

    def __init__(self, request, response):
        self.request = request
        self.response = response


class Context(object):
    messages = None
    times = None
    kind = None
    window = None
    min_period = 2

    def __init__(self, kind, *args, **kw):
        self.kind = kind

        self.messages = []

        self.times = []

        self.window = 30
        self.triggered = True

    def add(self, request, response):

        self.messages.append(Message(request, response))
        self.times.append(time.time())

        self.messages = self.messages[-self.window:]
        self.times = self.times[-self.window:]

    def get_frequency(self, request=None, response=None):
        '''
        '''
        times = [t for m, t in zip(self.messages, self.times)
                 if (m.response == response or response is None)
                    and (m.request == request or request is None)]
        if len(times) < 2:
            return 0
        return len(times) / (self.times[-1] - self.times[0])

    def get_response(self):
        t = time.time()
        if self.triggered or t - self.times[-1] >= self.min_period:
            '''
                make it ok to do the query
            '''
            self.triggered = False
            return True
        else:
            '''
                if less than the min period has elapse since last call 
                simple return the last response
            '''
            return self.messages[-1].response

TRIGGERS = dict(SetValveState='GetValveState')


class ContextFilter(Loggable):
    _contexts_ = None

    def __init__(self, *args, **kw):
        super(ContextFilter, self).__init__(*args, **kw)
        self._contexts_ = dict()

    def add_message(self, kind, request, response):
        ctx = self._contexts_
        if kind in ctx:

            ctx[kind].add(request, response)
        else:
            c = Context(kind)
            c.add(request, response)
            ctx[kind] = c

        if kind in TRIGGERS:
            te = TRIGGERS[kind]
            if te in ctx:
                ctx[te].triggered = True

    def get_response(self, handler, data, filter_=False):

        if filter_:
            kind, request = handler.parse(data)

            resp = True
            freqa = 0
            freqr = 0
            resp_kind = 'Stored'
            if kind in self._contexts_:
                ctx = self._contexts_[kind]
                resp = ctx.get_response()
                freqa = ctx.get_frequency(request=request)
                freqr = ctx.get_frequency(request=request, response=resp)

            if resp == True:
                resp_kind = 'Actual'
                resp = handler.handle(data)

            self.info('kind={}, req={},res={} ({}), freqa={}, freqr={} '.format(kind, request,
                                                                                resp_kind, resp,
                                                                                freqa, freqr))
            self.add_message(kind, request, resp)
        else:
            resp = handler.handle(data)

        return resp


class Sender(Thread):
    _serve = True

    def run(self):
        cnt = 0
        while self._serve:
            if cnt % 2:
                k = 'GetValveState'
                request = 'A'
                response = 'True' if random.randint(0, 4) else 'False'
                self.filter.add_message(k, request, response)

            else:
                k = 'SetValveState'
                request = 'A'
                response = 'True'
                self.filter.add_message(k, request, response)

            time.sleep(0.05)
            cnt += 1


def main():
    cf = ContextFilter()
    sender = Sender()
    sender.filter = cf

    sender.start()
    time.sleep(2)
    sender._serve = False
    print cf._contexts_['GetValveState'].get_frequency(request='A', response='True')
    print cf._contexts_['GetValveState'].get_frequency(request='B', response='True')
    print cf._contexts_['GetValveState'].get_frequency(response='False')


if __name__ == '__main__':
    main()


# ============= EOF =============================================
