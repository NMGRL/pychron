# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= standard library imports ========================
# ============= local library imports  ==========================
import time


def timethis(func, msg=None, log=None, args=None, kwargs=None, decorate='$', rettime=False):
    if args is None:
        args = tuple()
    if kwargs is None:
        kwargs = dict()

    st = time.time()
    r = func(*args, **kwargs)
    et = time.time() - st
    s = '{:0.5f}s'.format(et)

    if msg is None:
        if hasattr(func, 'func_name'):
            msg = func.func_name
        else:
            msg = ''
    # if msg:
    s = '{} {}'.format(msg, s)
    if decorate:
        s = '{} {}'.format(decorate * 20, s)

    if log:
        log(s)
    else:
        print 'timethis', s
    if rettime:
        return et
    return r


# def timer(msg=None):
#     def _timer(func):
#         def dec(*args, **kw):
#             with TimerCTX(msg, func.func_name):
#                 func(*args, **kw)
#         return dec
#     return _timer
def simple_timer(msg=None):
    def _timer(func):
        def dec(*args, **kw):
            with TimerCTX(msg, func.func_name):
                return func(*args, **kw)

        return dec

    return _timer


class TimerCTX(object):
    def __init__(self, msg, funcname):
        self._funcname = funcname
        self._msg = msg

    def __enter__(self):
        self._st = time.time()

    def __exit__(self, *args, **kw):
        dur = time.time() - self._st
        msg = self._msg
        s = '{} {}'.format(self._funcname, dur)
        if msg:
            s = '{} - {}'.format(s, msg)
        print s

# ============= EOF =============================================
