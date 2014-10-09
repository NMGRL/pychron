#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Any, Bool, Property, Int, Dict
from pyface.confirmation_dialog import confirm

#============= standard library imports ========================
from threading import Event, Thread, Lock
from Queue import Empty, LifoQueue
import hashlib
import time
import os
import inspect
import traceback
import yaml
import sys
import weakref
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.loggable import Loggable
from pychron.globals import globalv
from pychron.pyscripts.error import PyscriptError, IntervalError, GosubError, \
    KlassError, MainError


class CTXObject(object):
    def update(self, ctx):
        self.__dict__.update(**ctx)


class EXPObject(CTXObject):
    pass


class CMDObject(CTXObject):
    pass


class IntervalContext(object):
    def __init__(self, obj, dur):
        self.obj = obj
        self.dur = dur

    def __enter__(self):
        self.obj.begin_interval(duration=self.dur)

    def __exit__(self, *args):
        self.obj.complete_interval()


def verbose_skip(func):
    def decorator(obj, *args, **kw):

        fname = func.__name__
        #        print fname, obj.testing_syntax, obj._cancel
        if fname.startswith('_m_'):
            fname = fname[3:]

        args1, _, _, defaults = inspect.getargspec(func)

        nd = sum([1 for di in defaults if di is not None]) if defaults else 0

        min_args = len(args1) - 1 - nd
        an = len(args) + len(kw)
        if an < min_args:
            raise PyscriptError(obj.name, 'invalid arguments count for {}, args={} kwargs={}'.format(fname,
                                                                                                     args, kw))
            #        if obj.testing_syntax or obj._cancel:
        #            return
        if obj.testing_syntax or obj._cancel or obj._truncate:
            return

        obj.debug('{} {} {}'.format(fname, args, kw))

        return func(obj, *args, **kw)

    return decorator


def skip(func):
    def decorator(obj, *args, **kw):
        if obj.testing_syntax or obj._cancel or obj._truncate:
            return
        return func(obj, *args, **kw)

    return decorator


def count_verbose_skip(func):
    def decorator(obj, *args, **kw):
        if obj._truncate or obj._cancel:
            return

        fname = func.__name__
        #        print fname, obj.testing_syntax, obj._cancel
        if fname.startswith('_m_'):
            fname = fname[3:]

        args1, _, _, defaults = inspect.getargspec(func)

        nd = sum([1 for di in defaults if di is not None]) if defaults else 0

        min_args = len(args1) - 1 - nd
        an = len(args) + len(kw)
        if an < min_args:
            raise PyscriptError('invalid arguments count for {}, args={} kwargs={}'.format(fname,
                                                                                           args, kw))
            #        if obj._cancel:
        if obj.testing_syntax:
        #             print func.func_name, obj._estimated_duration
            func(obj, calc_time=True, *args, **kw)
            #             print func.func_name, obj._estimated_duration
            return

        obj.debug('{} {} {}'.format(fname, args, kw))

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


command_register = makeRegistry()
named_register = makeNamedRegistry(command_register)

'''
@todo: cancel script if action fails. eg fatal comm. error
'''


class PyScript(Loggable):
    text = Property
    syntax_checked = Bool

    manager = Any
    parent_script = Any

    root = Str
    # filename = Str
    info_color = Str

    testing_syntax = Bool(False)
    cancel_flag = Bool
    hash_key = None

    _ctx = None
    _exp_obj = None

    _text = Str

    _interval_stack = None

    _cancel = Bool(False)
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

    def __init__(self, *args, **kw):
        super(PyScript, self).__init__(*args, **kw)
        self._block_lock = Lock()

    def canceled(self):
        return self._cancel

    def finished(self):
        self._finished()

    def console_info(self, *args, **kw):
        self._m_info(*args, **kw)

    def calculate_estimated_duration(self, ctx=None, force=False):
        """
            maintain a dictionary of previous calculated durations.
            key=hash(ctx), value=duration

        """

        def calc_dur():
            self.setup_context(**ctx)
            self.syntax_checked = False
            self.debug('calculate_estimated duration. syntax requires testing')
            self.test()
            self.debug('estimated duration= {}'.format(self._estimated_duration))

        if not ctx:
            calc_dur()
            return self.get_estimated_duration()

        h = hashlib.sha1(repr(sorted(ctx.items()))).hexdigest()
        if force or not self.syntax_checked:
            calc_dur()
        else:
            try:
                d = self._estimated_durations[h]
                self._estimated_duration = d
            except KeyError:
                calc_dur()

        d = self.get_estimated_duration()
        self._estimated_durations[h] = d
        return d

    def traceit(self, frame, event, arg):
        if event == "line":
            co = frame.f_code
            if co.co_filename == self.filename:
                lineno = frame.f_lineno
                self.trace_line = lineno

        return self.traceit

    def execute(self, new_thread=False, bootstrap=True,
                trace=False,
                finished_callback=None, 
                argv=None):
        if bootstrap:
            self.bootstrap()

        if not self.syntax_checked:
            self.test()

        def _ex_():
            self._execute(trace=trace, argv=argv)
            if finished_callback:
                finished_callback()

            self.finished()
            return self._completed

        if new_thread:
            t = Thread(target=_ex_)
            t.start()
            return t
        else:
            return _ex_()

    def test(self, argv=None):
        if not self.syntax_checked:
            self.setup_context()

            self.debug('testing...')
            self._estimated_duration = 0
            self.syntax_checked = True
            self.testing_syntax = True
            self._syntax_error = True

            r = self._execute(argv=argv)
            if r is not None:
                self.info('invalid syntax')
                ee = PyscriptError(self.filename, r)
                raise ee

            elif not self._interval_stack.empty():
                raise IntervalError()

            else:
                self.info('syntax checking passed')
                self._syntax_error = False

            self.testing_syntax = False

    def compile_snippet(self, snippet):
        try:
            code = compile(snippet, '<string>', 'exec')
        except Exception, e:
            self.debug(traceback.format_exc())
            return e
        else:
            return code

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
                script = imp.load_source('script', snippet)
            except Exception, e:
                return e
            script.__dict__.update(safe_dict)
            try:
                script.main(*argv)
            except TypeError:
                script.main()
            except AttributeError, e:
                self.debug('{} {}'.format(e, traceback.format_exc()))
                return MainError

        else:
        #         sys.settrace(self._tracer)
            code_or_err = self.compile_snippet(snippet)
            if not isinstance(code_or_err, Exception):
                try:
                    exec code_or_err in safe_dict
                    func = safe_dict['main']
                except KeyError, e:
                    print e, safe_dict.keys()
                    self.debug('{} {}'.format(e, traceback.format_exc()))
                    return MainError()

                try:
                    if argv is None:
                        argv = tuple()
                    func(*argv)
                except Exception, e:
                    return traceback.format_exc()
            else:
                return code_or_err

    def syntax_ok(self, warn=True):
        try:
            self.test()
        except PyscriptError, e:
            if warn:
                self.warning_dialog(traceback.format_exc())
            return False

        return True
        # return not self._syntax_error

    def check_for_modifications(self):
        old = self.toblob()
        with open(self.filename, 'r') as f:
            new = f.read()

        return old != new

    def toblob(self):
        return self.text

    def get_estimated_duration(self):
        return self._estimated_duration

    def set_default_context(self):
        pass

    def setup_context(self, **kw):
        if self._ctx is None:
            self._ctx = dict()
        if self._exp_obj is None:
            self._exp_obj = EXPObject()
        # self._ctx.update(kw)

        self._exp_obj.update(kw)
        # self._exp_obj.__dict__.update(**kw)
        self._ctx['ex'] = self._exp_obj

        #for backwards compatiblity add kw to main context
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
            ctx['ex'] = self._exp_obj

        if self._ctx:
            ctx.update(self._ctx)

        #use a cmd object for visual clarity when writing pyscripts ie ```cmd.sleep``` instead of ```sleep```
        # cmd=CMDObject()
        # cmd.update(ctx)
        # ctx['cmd']=cmd

        return ctx

    def get_variables(self):
        return []

    def get_commands(self):
        return self.get_command_register() + \
               command_register.commands.items()

    def get_command_register(self):
        return []

    def truncate(self, style=None):
        if style is None:
            self._truncate = True

        if self._gosub_script is not None:
            self._gosub_script.truncate(style=style)

    def cancel(self, **kw):
        self._cancel = True
        if self._gosub_script is not None:
            if not self._gosub_script._cancel:
                self._gosub_script.cancel(**kw)

        if self.parent_script:
            if not self.parent_script._cancel:
                self.parent_script.cancel(**kw)

        if self._wait_control:
            self._wait_control.stop()

        self._cancel_hook(**kw)

    def bootstrap(self, load=True, **kw):
        self._interval_stack = LifoQueue()

        if self.root and self.name and load:
            with open(self.filename, 'r') as f:
                self.text = f.read()

            return True

    #===============================================================================
    # interpolation
    #===============================================================================
    def load_interpolation_context(self):
        ctx = self._get_interpolation_context()
        return ctx.keys()
    #==============================================================================
    # commands
    #==============================================================================
    @command_register
    def gosub(self, name=None, root=None, klass=None, argv=None, **kw):

        if not name.endswith('.py'):
            name += '.py'

        if root is None:
            d = None
            if '/' in name:
                d = '/'
            elif ':' in name:
                d = ':'

            if d:
                # name = name.split(d)[-1]
                dirs = name.split(d)
                name = dirs[0]
                for di in dirs[1:]:
                    name = os.path.join(name, di)

            root = self.root

        # p = os.path.join(root, name)
        # if not os.path.isfile(p):
        #     while root!=paths.scripts_dir:
        #         root=os.path.dirname(root)
        #         p = os.path.join(root, name)
        #         if os.path.isfile(p):
        #             break
        #     else:
        #         raise GosubError(p)
        root, name = self._find_root(root, name)

        if klass is None:
            klass = self.__class__
        else:
            klassname = klass
            pkg = 'pychron.pyscripts.api'
            mod = __import__(pkg, fromlist=[klass])
            klass = getattr(mod, klass)

        if not klass:
            raise KlassError(klassname)

        s = klass(root=root,
                  name=name,
                  manager=self.manager,
                  parent_script=weakref.ref(self)(),
                  syntax_checked=self.syntax_checked,
                  _ctx=self._ctx,
                  **kw)

        if self.testing_syntax:
            s.bootstrap()
            err = s.test(argv=argv)
            if err:
                raise PyscriptError(self.name, err)

        else:
            if not self._cancel:
                self.info('doing GOSUB')
                self._gosub_script = s
                s.execute(argv=argv)
                self._gosub_script = None
                if not self._cancel:
                    self.info('gosub finished')

    @verbose_skip
    @command_register
    def exit(self):
        self.info('doing EXIT')
        self.cancel()

    @command_register
    def interval(self, dur):
        return IntervalContext(self, dur)

    @command_register
    def complete_interval(self):
        try:
            _, f, n = self._interval_stack.get(timeout=0.01)
        except Empty:
            raise IntervalError()

        if self.testing_syntax:
            return

        if self._cancel:
            return

        self.info('COMPLETE INTERVAL waiting for {} to complete'.format(n))
        # wait until flag is set
        while not f.isSet():
            if self._cancel:
                break
            self._sleep(0.5)

        if not self._cancel:
            f.clear()

    @command_register
    def begin_interval(self, duration, name=None):

        self._estimated_duration += duration

        if self._cancel:
            return

        def wait(dur, flag, n):
            self._sleep(dur)
            if not self._cancel:
                self.info('{} finished'.format(n))
                flag.set()

        duration = float(duration)

        t, f = None, None
        if name is None:
            name = 'Interval {}'.format(self._interval_stack.qsize() + 1)

        if not self.testing_syntax:
            f = Event()
            self.info('BEGIN INTERVAL {} waiting for {}'.format(name, duration))
            t = Thread(name=name,
                       target=wait, args=(duration, f, name))
            t.start()

        self._interval_stack.put((t, f, name))

    @command_register
    def delay(self, duration=0, message=None):
        self.sleep(duration, message)

    @command_register
    def sleep(self, duration=0, message=None):
        #dont add to duration if within an interval
        if not self._interval_stack.qsize() % 2:
            self._estimated_duration += duration
            if self.parent_script is not None:
                self.parent_script._estimated_duration += self._estimated_duration

        if self.testing_syntax or self._cancel:
            return

        self.info('SLEEP {}'.format(duration))
        if globalv.experiment_debug:
            self.debug('using debug sleep {}'.format(duration))

        self._sleep(duration, message=message)

    @skip
    @named_register('info')
    def _m_info(self, message=None):
        message = str(message)
        self.info(message)

        try:
            if self.manager:
                if self.info_color:
                    self.manager.info(message, color=self.info_color, log=False)
                else:
                    self.manager.info(message, log=False)

        except AttributeError, e:
            self.debug('m_info {}'.format(e))

    #===============================================================================
    # handlers
    #===============================================================================
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
            result = confirm(None,
                             'Are you sure you want to cancel {}'.format(self.logger_name),
                             title='Cancel Script')
            #            result = confirmation(None, 'Are you sure you want to cancel {}'.format(self.logger_name))
            if result != 5104:
                self.cancel()
            else:
                self.cancel_flag = False

    #===============================================================================
    # private
    #===============================================================================
    def _execute(self, **kw):

        self._cancel = False
        self._completed = False
        self._truncate = False

        error = self.execute_snippet(**kw)
        if error:
            self.warning('_execute: {}'.format(str(error)))
            return error

        if self.testing_syntax:
            return

        if self._cancel:
            self.info('{} canceled'.format(self.name))
        else:
            self.info('{} completed successfully'.format(self.name))
            self._completed = True

    def _get_application(self):
        app = self.application
        if app is None:
            if self.manager:
                app = self.manager.application
        return app

    def _manager_action(self, func, name=None, protocol=None, *args, **kw):
        man = self.manager
        # if protocol is not None and man is not None:
        #     app = man.application
        # else:
        #     app = self.application
        if protocol:
            app = self._get_application()
            if app is not None:
                app_args = (protocol,)
                if name is not None:
                    app_args = (protocol, 'name=="{}"'.format(name))

                man = app.get_service(*app_args)

        if man is not None:
            if not isinstance(func, list):
                func = [(func, args, kw)]
            rs = []
            for f, a, k in func:

                r = None
                if hasattr(man, f):
                    r = getattr(man, f)(*a, **k)
                rs.append(r)
            return rs
            # return [getattr(man, f)(*a, **k) for f, a, k in func]
        elif name:
            self.warning('could not find manager name="{}" func="{}"'.format(name,
                                                                             ','.join([f for f, _, _ in func])))

    def _cancel_hook(self, **kw):
        pass

    def _finished(self):
        pass

    #==============================================================================
    # Sleep/ Wait
    #==============================================================================
    def _sleep(self, v, message=None):
        v = float(v)

        if v > 1:
            self._block(v, message=message, dialog=True)
        else:
            time.sleep(v)

    def _setup_wait_control(self, timeout, message):
        from pychron.wait.wait_control import WaitControl

        if self.manager:
            wd = self.manager.get_wait_control()
        else:
            wd = self._wait_control

        if wd is None:
            wd = WaitControl()

        self._wait_control = wd
        if self.manager:
            self.manager.wait_group.active_control = wd
        msg = 'Waiting for {:0.1f}  {}'.format(timeout, message)
        self.debug(msg)
        wd.trait_set(message=msg, wtime=timeout)
        wd.start(block=False, wtime=timeout)

        return wd

    def _block(self, timeout, message=None, dialog=False):
        self.debug('block started')
        st = time.time()
        if dialog:
            if message is None:
                message = ''

            """
                use lock to synchronize wait control creation
                this is necessary so that the created wait control has a chance to start
                before the next control asks if the active control is running.

            """
            with self._block_lock:
                wd = self._setup_wait_control(timeout, message)

            wd.join()

            if self.manager:
                self.manager.wait_group.pop(wd)

            if wd.is_canceled():
                self.cancel()
            elif wd.is_continued():
                self.info('continuing script after {:0.3f} s'.format(time.time() - st))
                if self.manager:
                    self.manager.continued()

        else:
            while time.time() - st < timeout:
                if self._cancel:
                    break
                time.sleep(0.05)

        self.debug('block finished. duration {}'.format(time.time() - st))

    #===============================================================================
    # properties
    #===============================================================================
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
            return '1'

        if self._completed:
            return '2'

        return '0'

    def _get_text(self):
        return self._text

    def _set_text(self, t):
        self._text = t

    def _setup_docstr_context(self):
        pass

    _interpolation_context = None

    def _get_interpolation_context(self):
        if self._interpolation_context is None:
            self._interpolation_context = self._load_interpolation_file()
        return self._interpolation_context

    def _load_interpolation_file(self):
        d = {}
        if self.interpolation_path:
            if os.path.isfile(self.interpolation_path):
                try:
                    with open(self.interpolation_path, 'r') as fp:
                        d = yaml.load(fp)
                except yaml.YAMLError, e:
                    self.debug(e)
            else:
                self.debug('not a file. {}'.format(self.interpolation_path))
        else:
            self.debug('no interpolation path defined')

        return d

    def _tracer(self, frame, event, arg):
        if event == 'line':
            print frame.f_code.co_filename, frame.f_lineno

        return self._tracer

    def __str__(self):
        return self.name

    def __getattr__(self, item):
        ctx = self._get_interpolation_context()
        v = ctx.get(item, None)
        if v is None:
            raise AttributeError

        return v

if __name__ == '__main__':
    class DummyManager(Loggable):
        def open_valve(self, *args, **kw):
            self.info('open valve')

        def close_valve(self, *args, **kw):
            self.info('close valve')

    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('pscript')
    #    execute_script(t)
    # from pychron.paths import paths

    ps = PyScript(root=os.path.join(paths.scripts_dir, 'pyscripts'),
                 path='test.py',
                 _manager=DummyManager())

    ps.execute()
#============= EOF =============================================
