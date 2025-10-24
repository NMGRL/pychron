# ===============================================================================
# Copyright 2019 ross
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
import inspect
import os

from pychron.pyscripts.error import PyscriptError


def count_verbose_skip(func):
    def decorator(obj, *args, **kw):
        fname = check_parameters(func, args, kw)

        if obj.is_truncated() or obj.is_canceled() or obj.is_aborted():
            return 0

        if obj.testing_syntax:
            func(obj, calc_time=True, *args, **kw)
            return 0

        obj.debug("{} {} {}".format(fname, args, kw))

        return func(obj, *args, **kw)

    return decorator


def skip(func):
    def decorator(obj, *args, **kw):
        if (
            obj.testing_syntax
            or obj.is_canceled()
            or obj.is_truncated()
            or obj.is_aborted()
        ):
            return
        return func(obj, *args, **kw)

    return decorator


def check_parameters(func, pargs, pkw):
    fname = func.__name__
    if fname.startswith("_m_"):
        fname = fname[3:]

    signature = inspect.signature(func)
    args1 = [
        p.name
        for p in signature.parameters.values()
        if p.kind not in (inspect._VAR_KEYWORD, inspect._VAR_POSITIONAL)
    ]

    defaults = [
        p.default
        for p in signature.parameters.values()
        if p.default is not inspect._empty
    ]
    nd = len(defaults)
    min_args = len(args1) - 1 - nd
    an = len(pargs) + len(pkw)
    if an < min_args:
        raise PyscriptError(
            fname,
            "invalid arguments count for {}, min={}, n={} "
            "args={} kwargs={}".format(fname, min_args, an, pargs, pkw),
        )
    return fname


def verbose_skip(func):
    if os.environ.get("RTD", "False") == "True":
        return func
    else:

        def decorator(obj, *args, **kw):
            fname = check_parameters(func, args, kw)
            if (
                obj.testing_syntax
                or obj.is_canceled()
                or obj.is_truncated()
                or obj.is_aborted()
            ):
                return 0

            obj.debug("func_name={} args={} kw={}".format(fname, args, kw))

            return func(obj, *args, **kw)

        return decorator


class MockFunction:
    def __call__(self, *args, **kw):
        return True


class MockDevice:
    def __getattribute__(self, item):
        return MockFunction()


def device_verbose_skip(func):
    def decorator(obj, *args, **kw):
        fname = check_parameters(func, args, kw)
        if (
            obj.testing_syntax
            or obj.is_canceled()
            or obj.is_truncated()
            or obj.is_aborted()
        ):
            return MockDevice()

        obj.debug("func_name={} args={} kw={}".format(fname, args, kw))

        return func(obj, *args, **kw)

    return decorator


def calculate_duration(func):
    def decorator(obj, *args, **kw):
        if obj.testing_syntax:
            func(obj, calc_time=True, *args, **kw)
            return 0
        return func(obj, *args, **kw)

    return decorator


def makeRegistry():
    registry = {}

    def registrar(func):
        registry[func.__name__] = func.__name__
        return func  # normally a decorator returns a wrapped function,
        # but here we return func unmodified, after registering it

    registrar.commands = registry
    return registrar


def makeNamedRegistry(cmd_register):
    def named_register(name):
        def decorator(func):
            cmd_register.commands[name] = func.__name__
            return func

        return decorator

    return named_register


# ============= EOF =============================================
