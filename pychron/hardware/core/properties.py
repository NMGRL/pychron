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


class Processor(object):
    def __init__(self, func):
        self._func = func

    def __call__(self, *args, **kw):
        return self._func(*args, **kw)


class MappingProcessor(Processor):
    def __init__(self, values):
        self.values = values


class MapProcessor(MappingProcessor):
    def __call__(self, value):
        return self.values.get(value, None)


class ReverseMapProcessor(MappingProcessor):
    def __call__(self, value):
        return next((k for k, v in self.values.iteritems() if v == value), None)


class DeviceProperty(object):
    def __init__(self, getprocs=None, values=None, fget=None, fset=None, frandom=None, read_once=False, *args, **kw):

        self.fget = fget
        self.fset = fset
        self.frandom = frandom
        self._value = None
        self.read_once = read_once
        self.get_processors = []
        self.set_processors = []

        self.build(values, getprocs)

    def build(self, values=None, getprocs=None):
        if values:
            self.get_processors.append(MapProcessor(values))
        if getprocs:
            if not isinstance(getprocs, (list, tuple)):
                getprocs = (getprocs, )

            for g in getprocs:
                self.get_processors.append(Processor(g))

    def getter(self, func):
        self.fget = func
        return self

    def setter(self, func):
        self.fset = func
        return self

    def get(self, instance):
        if instance.simulation:
            func = self.frandom
            if func is None:
                func = instance.get_random_value
            return func()

        value = self.get_cache(instance)
        if self.read_once and value is not None:
            return value

        try:
            value = self.fget(instance)
        except BaseException, e:
            instance.critical(e)
            raise e

        # try:
        # value = float(value)
        # except (TypeError, ValueError), e:
        # instance.critical(e)
        # raise e

        try:
            value = self.post_get(value, instance)
        except BaseException, e:
            instance.critical(e)

        self.set_cache(instance, value)
        return value

    def post_get(self, value, instance):
        for processor in reversed(self.get_processors):
            value = processor(value)
        return value

    def get_cache(self, instance):
        return self._value

    def set_cache(self, instance, value):
        self._value = value

    def __call__(self, func):
        if self.fget is None:
            return self.getter(func)

        return self.setter(func)

    def __get__(self, instance, owner):
        return self.get(instance)


if __name__ == '__main__':
    class A(object):
        simulation = False

        @DeviceProperty(values={'1': 'on', '0': 'off'})
        def voltage_onoff(self):
            return '1'

        @DeviceProperty(float)
        def ambtemp(self):
            return '10.34'

        def critical(self, msg):
            print msg

    a = A()
    print 'voltage_onoff {} type={}'.format(a.voltage_onoff, type(a.voltage_onoff))
    print 'ambtemp {} type={}'.format(a.ambtemp, type(a.ambtemp))

    # print a.voltage_in, type(a.voltage_in)
# ============= EOF =============================================



