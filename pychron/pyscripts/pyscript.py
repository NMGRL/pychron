# ===============================================================================
# Copyright 2012 Jake Ross
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
import hashlib
import os
import sys
import time
import traceback
from queue import Empty, LifoQueue
from threading import Event, Thread, Lock

import yaml
from traits.api import Str, Any, Bool, Int, Dict

from pychron.core.yaml import yload
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pyscripts.contexts import EXPObject
from pychron.pyscripts.decorators import (
    makeRegistry,
    makeNamedRegistry,
    verbose_skip,
    calculate_duration,
    count_verbose_skip,
    skip,
)
from pychron.pyscripts.error import (
    PyscriptError,
    IntervalError,
    GosubError,
    KlassError,
    MainError,
)

BLOCK_LOCK = Lock()


class IntervalContext(object):
    def __init__(self, obj, dur):
        self.obj = obj
        self.dur = dur

    def __enter__(self):
        self.obj.begin_interval(duration=self.dur)

    def __exit__(self, *args):
        self.obj.complete_interval()


command_register = makeRegistry()
named_register = makeNamedRegistry(command_register)

"""
@todo: cancel script if action fails. eg fatal comm. error
"""


class PyScript(Loggable):
    # text = Property
    syntax_checked = Bool

    manager = Any
    parent_script = Any

    root = Str
    # filename = Str
    info_color = Str
    display_state = Str
    execution_error = Str
    exception_trace = Str
    text = Str

    testing_syntax = Bool(False)
    cancel_flag = Bool
    hash_key = None

    _ctx = None
    _exp_obj = None

    # _text = Str

    _interval_stack = None

    _aborted = False
    _cancel = False
    _completed = False
    _truncate = False

    _syntax_error = None
    _gosub_script = None
    _wait_control = None

    _estimated_duration = 0
    _estimated_durations = Dict
    _graph_calc = False

    trace_line = Int
    interpolation_path = Str

    _interpolation_context = None

    def is_aborted(self):
        return self._aborted

    def is_canceled(self):
        return self._cancel

    def is_truncated(self):
        return self._truncate

    def finish(self):
        self._finish()

    def console_info(self, *args, **kw):
        self._m_info(*args, **kw)

    def calculate_estimated_duration(self, ctx=None, force=False):
        """
        maintain a dictionary of previous calculated durations.
        key=hash(ctx), value=duration

        """

        if ctx is None:
            ctx = self._ctx

        def calc_dur():
            self.debug("calculate duration")
            self.setup_context(**ctx)
            # self.syntax_checked = False
            # self.debug('calculate_estimated duration. syntax requires testing')
            self.test()
            # self.debug('pyscript estimated duration= {}'.format(self._estimated_duration))

        # self.debug('calculate estimated duration force={}, syntax_checked={}'.format(force, self.syntax_checked))
        if force or not self.syntax_checked or not ctx:
            calc_dur()

        return self.get_estimated_duration()

    def traceit(self, frame, event, arg):
        if event == "line":
            co = frame.f_code
            if co.co_filename == self.filename:
                lineno = frame.f_lineno
                self.trace_line = lineno

        return self.traceit

    def execute(
        self,
        new_thread=False,
        bootstrap=True,
        delay_start=0,
        on_completion=None,
        trace=False,
        argv=None,
        test=True,
    ):
        if bootstrap:
            self.bootstrap()

        if not self.syntax_checked and test:
            self.test()

        def _ex_():
            self._execute(trace=trace, argv=argv)
            self.finish()
            if on_completion:
                on_completion()

            return self._completed

        if delay_start:
            self.sleep(delay_start)

        if new_thread:
            t = Thread(target=_ex_)
            t.start()
            return t
        else:
            return _ex_()

    def test(self, argv=None):
        if not self.syntax_checked:
            self.debug("testing...")
            self._estimated_duration = 0
            self.syntax_checked = True
            self.testing_syntax = True
            self._syntax_error = True

            self.setup_context()

            r = self._execute(argv=argv)
            if r is not None:
                self.console_info("invalid syntax")
                ee = PyscriptError(self.filename, r)
                print("invalid pyscript", self.text)
                print("error", r)
                raise ee

            elif not self._interval_stack.empty():
                raise IntervalError()

            else:
                self.console_info("syntax checking passed")
                self._syntax_error = False

            self.testing_syntax = False

    def execute_snippet(self, snippet=None, trace=False, argv=None):
        safe_dict = self.get_context()
        if snippet is None:
            if trace:
                snippet = self.filename
            else:
                snippet = self.text

        if trace:
            sys.settrace(self.traceit)
            import imp

            try:
                script = imp.load_source("script", snippet)
            except Exception as e:
                return e
            script.__dict__.update(safe_dict)
            try:
                script.main(*argv)
            except TypeError:
                script.main()
            except AttributeError as e:
                self.debug("{} {}".format(e, traceback.format_exc()))
                return MainError

        else:
            try:
                code = compile(snippet, "<string>", "exec")
            except BaseException as e:
                exc = self.debug_exception()
                self.exception_trace = exc
                return e

            try:
                exec(code, safe_dict)
                func = safe_dict["main"]
            except KeyError as e:
                exc = self.debug_exception()
                self.exception_trace = exc
                return MainError()

            try:
                if argv is None:
                    argv = tuple()

                st = time.time()
                func(*argv)
                self.debug(
                    "executed snippet estimated_duration={}, duration={}".format(
                        self._estimated_duration, time.time() - st
                    )
                )
            except Exception as e:
                exc = self.debug_exception()
                self.exception_trace = exc
                return exc

    def syntax_ok(self, warn=True):
        try:
            self.test()
        except PyscriptError as e:
            if warn:
                self.warning_dialog(traceback.format_exc())
            return False

        return True

    def check_for_modifications(self):
        old = self.toblob()
        with open(self.filename, "r") as f:
            new = f.read()

        return old != new

    def toblob(self):
        return self.text

    def get_estimated_duration(self):
        return round(self._estimated_duration)

    def set_default_context(self):
        pass

    def setup_context(self, **kw):
        if self._ctx is None:
            self._ctx = dict()
        if self._exp_obj is None:
            self._exp_obj = EXPObject()

        kw["testing_syntax"] = self.testing_syntax
        self._exp_obj.update(kw)
        self._ctx["ex"] = self._exp_obj

        # for backwards compatiblity add kw to main context
        self._ctx.update(**kw)
        self._setup_docstr_context()

    def get_context(self):
        ctx = dict()
        for k in self.get_commands():
            if isinstance(k, tuple):
                ka, kb = k
                name, func = ka, getattr(self, kb)
            else:
                name, func = k, getattr(self, k)

            ctx[name] = func

        exp_ctx = {}
        for v in self.get_variables() + self.load_interpolation_context():
            ctx[v] = getattr(self, v)
            exp_ctx[v] = getattr(self, v)

        if self._exp_obj:
            self._exp_obj.update(exp_ctx)
            ctx["ex"] = self._exp_obj

        if self._ctx:
            ctx.update(self._ctx)

        # use a cmd object for visual clarity when writing pyscripts ie ```cmd.sleep``` instead of ```sleep```
        # cmd=CMDObject()
        # cmd.update(ctx)
        # ctx['cmd']=cmd

        return ctx

    def get_variables(self):
        return []

    def get_commands(self):
        cmds = self.get_command_register() + list(command_register.commands.items())
        return cmds

    def get_command_register(self):
        return []

    def truncate(self, style=None):
        if style is None:
            self._truncate = True

        if self._gosub_script is not None:
            self._gosub_script.truncate(style=style)

    @command_register
    def abort(self):
        self._aborted = True
        if self._gosub_script is not None:
            if not self._gosub_script.is_aborted():
                self._gosub_script.abort()

        if self.parent_script:
            if not self.parent_script.is_aborted():
                self.parent_script.abort()

        if self._wait_control:
            self._wait_control.stop()
        self._abort_hook()

    @command_register
    def cancel(self, **kw):
        self._cancel = True
        if self._gosub_script is not None:
            if not self._gosub_script.is_canceled():
                self._gosub_script.cancel(**kw)

        if self.parent_script:
            if not self.parent_script.is_canceled():
                self.parent_script.cancel(**kw)

        if self._wait_control:
            self._wait_control.stop()

        self._cancel_hook(**kw)

    def bootstrap(self, load=True, **kw):
        self._interval_stack = LifoQueue()

        if self.root and self.name and load:
            with open(self.filename, "r") as f:
                self.text = f.read()

            return True

    # ===============================================================================
    # interpolation
    # ===============================================================================
    def load_interpolation_context(self):
        ctx = self._get_interpolation_context()
        return list(ctx.keys())

    # ==============================================================================
    # commands
    # ==============================================================================
    @command_register
    def safe_while(self, func, timeout=60, period=1, calc_time=False):
        if self.testing_syntax or calc_time:
            return

        if isinstance(func, callable):
            st = time.time()
            while 1:
                ret = func()
                if ret:
                    break

                if timeout and time.time() - st > timeout:
                    break

                time.sleep(period)

    @calculate_duration
    @command_register
    def gosub(self, name=None, root=None, klass=None, argv=None, calc_time=False, **kw):
        if not name.endswith(".py"):
            name += ".py"

        if root is None:
            d = None
            if "/" in name:
                d = "/"
            elif ":" in name:
                d = ":"

            if d:
                dirs = name.split(d)
                name = dirs[0]
                for di in dirs[1:]:
                    name = os.path.join(name, di)

            root = self.root

        root, name = self._find_root(root, name)

        if klass is None:
            klass = self.__class__
            klassname = str(self.__class__)
        else:
            klassname = klass
            pkg = "pychron.pyscripts.api"
            mod = __import__(pkg, fromlist=[klass])
            klass = getattr(mod, klass)

        if not klass:
            raise KlassError(klassname)

        s = klass(
            root=root,
            name=name,
            manager=self.manager,
            application=self.application,
            parent_script=self,
            # syntax_checked=self.syntax_checked,
            _ctx=self._ctx,
            **kw
        )

        if calc_time:
            s.bootstrap()
            s.calculate_estimated_duration(force=True)
            self._estimated_duration += s.get_estimated_duration()
            return

        if self.testing_syntax:
            s.bootstrap()
            err = s.test(argv=argv)
            if err:
                raise PyscriptError(self.name, err)

        else:
            if not self._cancel:
                self.console_info("doing GOSUB")
                self._gosub_script = s
                s.execute(argv=argv)
                self._gosub_script = None
                if not self._cancel:
                    self.console_info("gosub finished")
                return s

    @verbose_skip
    @command_register
    def exit(self):
        self.console_info("doing EXIT")
        self.cancel()

    @command_register
    def interval(self, dur):
        return IntervalContext(self, dur)

    @command_register
    def complete_interval(self):
        if self._cancel:
            return

        try:
            f, n = self._interval_stack.get(timeout=0.01)
        except Empty:
            raise IntervalError()

        if self.testing_syntax:
            return

        self.console_info("COMPLETE INTERVAL waiting for {} to complete".format(n))
        # wait until flag is set
        while not f.isSet():
            if self._cancel:
                break
            self._sleep(0.5)

        if not self._cancel:
            f.clear()

        self._interval_stack.task_done()

    @calculate_duration
    @command_register
    def begin_interval(self, duration, name=None, calc_time=False):
        duration = float(duration)
        if calc_time:
            self._estimated_duration += duration

        if self._cancel:
            return

        def wait(dur, flag, n):
            self._sleep(dur)
            if not self._cancel:
                self.console_info("{} finished".format(n))
                flag.set()

        t, f = None, None
        if name is None:
            name = "Interval {}".format(self._interval_stack.qsize() + 1)

        if not self.testing_syntax:
            f = Event()
            self.console_info("BEGIN INTERVAL {} waiting for {}".format(name, duration))
            t = Thread(name=name, target=wait, args=(duration, f, name))

        self._interval_stack.put((f, name))
        # only start the thread after item pushed onto stack
        if t:
            t.start()

    @count_verbose_skip
    @command_register
    def delay(self, duration=0, message=None, calc_time=False):
        self.sleep(duration, message, calc_time=calc_time)

    @count_verbose_skip
    @command_register
    def sleep(self, duration=0, message=None, calc_time=False):
        duration = round(duration, 1)
        # dont add to duration if within an interval
        if calc_time:
            if not self._interval_stack.qsize() % 2:
                self._estimated_duration += duration
                # if self.parent_script is not None:
                # self.parent_script._estimated_duration += self._estimated_duration
            self._estimated_duration += duration

        if self.testing_syntax or self._cancel:
            return

        self.console_info("SLEEP {}".format(duration))
        if globalv.experiment_debug:
            self.debug("using debug sleep {}".format(duration))

        self._sleep(duration, message=message)

    @skip
    @named_register("info")
    def _m_info(self, message=None):
        message = str(message)
        self.info(message)

        try:
            if self.manager:
                if self.info_color:
                    self.manager.info(message, color=self.info_color, log=False)
                else:
                    print(self.manager)
                    self.manager.info(message, log=False)

        except AttributeError as e:
            self.debug("m_info {}".format(e))

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _find_root(self, root, name):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            while root != paths.scripts_dir:
                root = os.path.dirname(root)
                p = os.path.join(root, name)
                if os.path.isfile(p):
                    break

                for d in os.listdir(root):
                    d = os.path.join(root, d)
                    if os.path.isdir(d):
                        p = os.path.join(d, name)
                        if os.path.isfile(p):
                            break
                if os.path.isfile(p):
                    break
            else:
                raise GosubError(name)
        return os.path.dirname(p), os.path.basename(p)

    def _cancel_flag_changed(self, v):
        if v:
            from pyface.confirmation_dialog import confirm

            result = confirm(
                None,
                "Are you sure you want to cancel {}".format(self.logger_name),
                title="Cancel Script",
            )
            if result != 5104:
                self.cancel()
            else:
                self.cancel_flag = False

    # ===============================================================================
    # private
    # ===============================================================================
    def _execute(self, **kw):
        self._cancel = False
        self._completed = False
        self._truncate = False
        self.exception_trace = ""
        self.execution_error = ""

        error = self.execute_snippet(**kw)
        if error:
            self.warning("_execute: {}".format(str(error)))
            self.execution_error = str(error)
            return error

        if self.testing_syntax:
            return

        if self._cancel:
            self.console_info("{} canceled".format(self.name))
        elif self._aborted:
            self.console_info("{} aborted".format(self.name))
            self._completed = True
        else:
            self.console_info("{} completed successfully".format(self.name))
            self._completed = True

    def _get_application(self):
        app = self.application
        if app is None:
            if self.manager:
                app = self.manager.application

        if app is None:
            self.debug(
                "no application available. self.manager = {}".format(self.manager)
            )
        return app

    def _manager_action(self, func, *args, **kw):
        result = self._manager_actions([func], *args, **kw)
        if result:
            return result[0]

    def _manager_actions(
        self, func, name=None, protocol=None, protocols=None, *args, **kw
    ):
        man = self.manager

        app = self._get_application()
        if app is None:
            return

        if protocol:
            app_args = (protocol,)
            if name is not None:
                app_args = (protocol, 'name=="{}"'.format(name))

            man = app.get_service(*app_args)
        elif protocols:
            for p in protocols:
                if name:
                    man = app.get_service(p, 'name=="{}"'.format(name))
                else:
                    man = app.get_service(p, 'name=="{}"'.format(name))
                if man:
                    break

        # self.debug('manager action {}'.format(man))
        if man is not None:
            if not isinstance(func, list):
                func = [(func, args, kw)]

            rs = []
            for params in func:
                if len(params) == 1:
                    f, a, k = params[0], (), {}
                elif len(params) == 2:
                    f, a = params
                    k = None
                else:
                    f, a, k = params

                r = None
                self.debug(
                    "man={}, func={}, hasattr={}".format(man, f, hasattr(man, f))
                )
                if hasattr(man, f):
                    r = getattr(man, f)(*a, **k)
                    self.debug("result={}".format(r))

                rs.append(r)
            return rs
            # return [getattr(man, f)(*a, **k) for f, a, k in func]
        elif name:
            msg = ",".join([f for f, _, _ in func])
            self.warning('could not find manager name="{}" func="{}"'.format(name, msg))

    # ==============================================================================
    # Sleep/ Wait
    # ==============================================================================
    def _sleep(self, v, message=None, paused=False):
        v = float(v)
        self._estimated_duration += v
        if v > 1 or paused:
            self._block(v, message=message, dialog=True, paused=paused)
        else:
            time.sleep(v)

    def _setup_wait_control(self):
        from pychron.core.wait.wait_control import WaitControl

        wd = self._wait_control
        if self.manager:
            if hasattr(self.manager, "get_wait_control"):
                wd = self.manager.get_wait_control()

        if wd is None:
            wd = WaitControl()

        self._wait_control = wd
        if self.manager:
            try:
                if wd not in self.manager.wait_group.controls:
                    self.manager.wait_group.controls.append(wd)
                self.manager.wait_group.active_control = wd
            except AttributeError:
                pass

        return wd

    def _block(self, timeout, message=None, dialog=False, paused=False):
        self.debug("block started")
        st = time.time()
        if dialog:
            if message is None:
                message = ""

            """
                use lock to synchronize wait control creation
                this is necessary so that the created wait control has a chance to start
                before the next control asks if the active control is running.

                block lock should be global to all pyscripts
            """
            with BLOCK_LOCK:
                # with self._block_lock:
                wd = self._setup_wait_control()

            msg = "WaitControl setup for {:03d}  {}".format(int(timeout), message)

            self.debug(msg)

            wd.start(duration=timeout, message=msg, paused=paused)
            # wd.join()

            if self.manager:
                try:
                    self.manager.wait_group.pop(wd)
                except AttributeError:
                    pass

            if wd.is_canceled():
                self.cancel()
                self.console_info(
                    "canceling script after {:0.3f} s".format(time.time() - st)
                )
            elif wd.is_continued():
                self.console_info(
                    "continuing script after {:0.3f} s".format(time.time() - st)
                )
                if self.manager and hasattr(self.manager, "continued"):
                    self.manager.continued()

        else:
            while time.time() - st < timeout:
                if self._cancel:
                    break
                time.sleep(0.05)

        self.debug("block finished. duration {}".format(time.time() - st))

    def _setup_docstr_context(self):
        pass

    def _get_interpolation_context(self):
        if self._interpolation_context is None:
            self._interpolation_context = self._load_interpolation_file()
        return self._interpolation_context

    def _load_interpolation_file(self):
        d = {}
        if self.interpolation_path:
            if os.path.isfile(self.interpolation_path):
                try:
                    d = yload(self.interpolation_path)
                except yaml.YAMLError as e:
                    self.debug(e)
            else:
                self.debug("not a file. {}".format(self.interpolation_path))
        else:
            self.debug("no interpolation path defined")

        return d

    def _tracer(self, frame, event, arg):
        if event == "line":
            print(frame.f_code.co_filename, frame.f_lineno)

        return self._tracer

    def _generate_ctx_hash(self, ctx):
        """
        generate a sha1 hash from self.__class__, duration, cleanup and len(position)

        need to add __class__ to the hash because the durations of a MeasurementScript
        and a ExtractionScript will be different for the same context
        """
        sha1 = hashlib.sha1()

        pos = ctx.get("position")
        if pos:
            pos = len(pos)
        for v in (self.__class__, ctx.get("duration"), ctx.get("cleanup"), pos):
            sha1.update(str(v))
        h = sha1.hexdigest()
        return h

    # def _update_cached_duration(self, h, d):
    #     global __CACHED_DURATIONS__
    #     if len(__CACHED_DURATIONS__) > 100:
    #         self.debug('clearing global cached durations dict')
    #         __CACHED_DURATIONS__ = {}
    #
    #     __CACHED_DURATIONS__[h] = d
    #
    # def _get_cached_duration(self, h):
    #     return __CACHED_DURATIONS__[h]

    def _cancel_hook(self, **kw):
        pass

    def _abort_hook(self):
        pass

    def _finish(self):
        pass

    # ===============================================================================
    # properties
    # ===============================================================================
    def _get_property(self, key, default=None):
        ctx = self.get_context()
        return ctx.get(key, default)

    @property
    def filename(self):
        return os.path.join(self.root, self.name)

    @property
    def state(self):
        # states
        # 0=running
        # 1=canceled
        # 2=completed
        if self._cancel:
            return "1"

        if self._completed:
            return "2"

        return "0"

    # def _get_text(self):
    #     return self._text
    #
    # def _set_text(self, t):
    #     self._text = t

    def __str__(self):
        return "{}, 0x{:x} name: {}".format(type(self), id(self), self.name)

    def __getattr__(self, item):
        ctx = self._get_interpolation_context()
        v = ctx.get(item, None)
        if v is None:
            raise AttributeError

        return v


# ============= EOF =============================================
