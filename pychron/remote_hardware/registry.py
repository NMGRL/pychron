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
import weakref
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.strtools import camel_case, to_list

REGISTRY = {}
FUNC_REGISTRY = {}


class Registry(object):
    def __init__(self, name=None, camel_case=False, postprocess=None):
        self.postprocess = postprocess
        self.name = name
        self.camel_case = camel_case

    def __call__(self, func):

        name = self.name
        if name is None:
            name = func.func_name
            if self.camel_case:
                name = camel_case(name)

        if self.postprocess:
            nfunc = lambda *args, **kw: self.postprocess(func(*args, **kw))
            REGISTRY[name] = nfunc
            return nfunc
        else:
            REGISTRY[name] = func
            return func


register = Registry


class RegisteredFunction(object):
    def __init__(self, camel_case=False, returntype=None):
        self.camel_case = camel_case
        self.returntype = returntype

    def __call__(self, func):
        def wrapper(obj, *args, **kw):
            cmd = func.func_name
            if self.camel_case:
                cmd = camel_case(cmd)

            r = obj.ask(cmd)
            if self.returntype:
                try:
                    r = self.returntype(r)
                except BaseException:
                    pass

            return r

        return wrapper


registered_function = RegisteredFunction


class RHHandleMixin(object):
    def registry_commands(self):
        for k, v in REGISTRY.items():
            FUNC_REGISTRY[k] = (v, weakref.ref(self)())


if __name__ == '__main__':

    class Handler(object):
        def __getattr__(self, item):
            if item in FUNC_REGISTRY:
                func, obj = FUNC_REGISTRY[item]
                return lambda manager, *args, **kw: func(obj, *args, **kw)

    class Device(object):
        def __init__(self):
            self.output = 10.3
            for k, v in REGISTRY.items():
                FUNC_REGISTRY[k] = (v, weakref.ref(self)())

        @register(camel_case=True, postprocess=','.join)
        def get_faults(self):
            return ['tank low', 'too hot']

        @register(camel_case=True)
        def get_coolant_out_temperature(self):
            return self.output

        @register()
        def amyfunc(self, a):
            return 'return of myfunction b {}'.format(a)

    class RemoteDevice(object):

        @registered_function(camel_case=True, returntype=to_list)
        def get_faults(self):
            pass

        @registered_function(camel_case=True, returntype=float)
        def get_coolant_out_temperature(self):
            pass

        def ask(self, cmd):
            print 'Asking {}'.format(cmd)
            if cmd == 'GetCoolantOutTemperature':
                return '1'
            elif cmd == 'GetFaults':
                return 'Too Hot,Tank Low'


    d = Device()
    # d2 = Device()
    # d2.output = 100234
    a = Handler()
    # print a.myfunc(None, 'aa')
    # print a.amyfunc(None, 'abaa')
    # print a.GetCoolantOutTemperature(None)
    # print a.GetFaults(None)

    rd = RemoteDevice()
    v = rd.get_coolant_out_temperature()
    print v, type(v)

    v = rd.get_faults()
    print v, type(v)

# ============= EOF =============================================



