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
'''
    http://code.activestate.com/recipes/391367-deprecated/
'''

import inspect
import warnings


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    message = None
    def newFunc(*args, **kwargs):
        caller = inspect.getframeinfo(inspect.currentframe().f_back)[2]
        warnings.warn("Call to deprecated function {}. From {}. {}".format(func.__name__,
                                                                           caller,
                                                                           message),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def deprecated_message(message):
    def decorator(func):
        """This is a decorator which can be used to mark functions
        as deprecated. It will result in a warning being emmitted
        when the function is used."""
        def newFunc(*args, **kwargs):
            caller = inspect.getframeinfo(inspect.currentframe().f_back)[2]
            warnings.warn("Call to deprecated function {}. From {}. {}".format(func.__name__,
                                                                               caller,
                                                                               message),
                          category=DeprecationWarning)
            return func(*args, **kwargs)
        newFunc.__name__ = func.__name__
        newFunc.__doc__ = func.__doc__
        newFunc.__dict__.update(func.__dict__)
        return newFunc

    return decorator


def deprecate_klass():
    def decorate(cls):
        for attr in cls.__dict__:  # there's propably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, deprecated(getattr(cls, attr)))
        return cls
    return decorate

# ============= EOF =============================================
