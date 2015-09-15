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
# ============= local library imports  ==========================
from traits.has_traits import MetaHasTraits

from pychron.core.helpers.logger_setup import new_logger
from pychron.core.helpers.strtools import camel_case

REGISTRY = {}
FUNC_REGISTRY = {}

logger = new_logger('DeviceFunctionRegistry')


class DeviceFunctionRegistry(object):
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

        logger.debug('register function {} as {}'.format(func.func_name, name))
        REGISTRY[name] = (func.func_name, self.postprocess)
        return func


register = DeviceFunctionRegistry


class RegisteredFunction(object):
    def __init__(self, cmd=None, camel_case=False, returntype=None):
        self.cmd = cmd
        self.camel_case = camel_case
        self.returntype = returntype

    def __call__(self, func):
        def wrapper(obj, *args, **kw):
            cmd = self.cmd
            if cmd is None:
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


def make_wrapper(func, postprocess):
    def wrapper(obj, manager, *args, **kw):
        """
        handler signature is self, manager, args, sender
        """

        ret = func(*args[1:], **kw)
        if postprocess:
            ret = postprocess(ret)
        return ret

    return wrapper


class MetaHandler(MetaHasTraits):
    def __call__(cls, *args, **kw):
        for k, v in FUNC_REGISTRY.items():
            setattr(cls, k, make_wrapper(*v))

        return MetaHasTraits.__call__(cls, *args, **kw)


def tx_register_functions(obj):
    for k, (fname, p) in REGISTRY.items():

        if hasattr(obj, fname):
            if fname not in FUNC_REGISTRY:
                func = getattr(obj, fname)
                if func is not None:
                    FUNC_REGISTRY[k] = (func, p)
                    logger.debug('Function register {} {}:{}'.format(obj.name, k, fname))

# if __name__ == '__main__':
#     class Handler(object):
#         __metaclass__ = MetaHandler
#
#     class Device2(RHMixin):
#         def __init__(self):
#             self.coolant = -1234
#             self.register_functions()
#
#         @register()
#         def get_coolant(self):
#             return self.coolant
#
#     class Device(RHMixin):
#         def __init__(self):
#             self.output = 101.43
#             self.register_functions()
#
#         @register(camel_case=True)
#         def get_coolant_out_temperature(self):
#             return self.output
#
#         @register(camel_case=True, postprocess=','.join)
#         def get_faults(self):
#             return ['foo', 'bar']
#
#     class Device3(RHMixin):
#         def __init__(self):
#             self.register_functions()
#
#         @register('MyFunc')
#         def foobar(self):
#             return 'asdf'
#
#
#     d = Device()
#     d2 = Device2()
#     d3 = Device3()
#     # print d.get_coolant_out_temperature()
#     h = Handler()
#     print 'handler get coolant out temp', h.GetCoolantOutTemperature(None)
#     print 'handler get faults', h.GetFaults(None)
#     # print h.get_coolant_out_temperature(None)
#     # print h.get_faults(None)
#     print 'handler get coolant', h.get_coolant(None)
#     print 'handler foobar', h.MyFunc(None)
#     print
#
#     class RemoteDevice(object):
#         @registered_function(camel_case=True, returntype=to_list)
#         def get_faults(self):
#             pass
#
#         @registered_function(camel_case=True, returntype=float)
#         def get_coolant_out_temperature(self):
#             pass
#
#         def ask(self, cmd):
#             print 'Asking {}'.format(cmd)
#             if cmd == 'GetCoolantOutTemperature':
#                 return '1'
#             elif cmd == 'GetFaults':
#                 return 'Too Hot,Tank Low'
#
#     rd = RemoteDevice()
#     v = rd.get_coolant_out_temperature()
#     print 'remote device coolant', v, type(v)
#
#     v = rd.get_faults()
#     print 'remote device faults', v, type(v)
# ============= EOF =============================================
