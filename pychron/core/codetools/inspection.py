# ===============================================================================
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

#============= standard library imports ========================
#============= local library imports  ==========================
import inspect
import traceback

import logging

logger=logging.getLogger('Inspection')

def caller(func):
    def dec(*args, **kw):
        stack = inspect.stack()

        cstack = stack[0]
        rstack = stack[1]

        msg = '{} called by {}. parent call={} {}'.format(func.func_name, rstack[3],
                                                          cstack[0].f_back.f_locals['self'],
                                                          ''.join(map(str.strip, rstack[4])))

        logger.debug(msg)
        return func(*args, **kw)

    return dec

def conditional_caller(func):
    def dec(*args, **kw):
        ret = func(*args, **kw)
        if ret is None:
            stack = inspect.stack()
            # traceback.print_stack()
            cstack = stack[0]
            rstack = stack[1]

            msg = '{} called by {}. parent call={} {}'.format(func.func_name, rstack[3],
                                                              cstack[0].f_back.f_locals['self'],
                                                              ''.join(map(str.strip, rstack[4])))

            logger.debug(msg)
        return ret

    return dec


def pcaller(func):
    def dec(*args, **kw):
        stack = inspect.stack()

        cstack = stack[0]
        rstack = stack[1]

        msg = '{} called by {}. parent call={} {}'.format(func.func_name, rstack[3],
                                                          'aaa',
                                                          # cstack[0].f_back.f_locals['self'],
                                                          ''.join(map(str.strip, rstack[4])))

        print msg
        return func(*args, **kw)

    return dec


def caller_stack(func):
    def dec(*args, **kw):
        stack = inspect.stack()
        traceback.print_stack()
        print '{} called by {}'.format(func.func_name, stack[1][3])
        return func(*args, **kw)

    return dec


#============= EOF =============================================
