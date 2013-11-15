#===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================

import time
#============= standard library imports ========================
#============= local library imports  ==========================


# def limit_frequency(func):
#    def decorator(self, obj, *args, **kw):
#        fn = func.func_code
#        key = '{}._prev_time'.format(fn)
#        prev_time = self.__dict__.get(key, None)
#        if prev_time and time.time() - prev_time < 0.1:
#            return
#
#        self.__dict__[key] = time.time()
#        return func(self, obj, *args, **kw)
#
#    return decorator



# class FrequencyLimiter(object):
#     def __init__(self, func):
#         self._f = func
#         self._prev_time = None
#
#     def __call__(self, *args, **kw):
#         prev_time = self._prev_time
#         if prev_time and time.time() - prev_time < 0.25:
#             return
#
#         prev_time = time.time()
#         return self._f(*args, **kw)

# class Limiter(object):
#     def limiter(self,):
#         prev_time = None
#
#         def limit_frequency(func):
#             def decorator(self, obj, *args, **kw):
# #                 global prev_time
#                 if prev_time and time.time() - prev_time < 0.25:
#                     return
#
#                 prev_time = time.time(func(self, obj, *args, **kw)
#             return decorator
#
#         limit_frequency.prev_time = None
#         return limit_frequency
#
# lm = Limiter()
# limit_frequency = lm.limiter()
# #
#         self.__dict__[key] = time.time()
#         return func(self, obj, *args, **kw)
# #
#     return decorator

#============= EOF =============================================
