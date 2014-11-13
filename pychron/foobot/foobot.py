from pychron.core.ui import set_qt

set_qt()
import re
import shlex
import os
from pyface.timer.do_later import do_later
from traits.trait_types import Instance, String, Event
from traitsui.editors import TextEditor
from traitsui.handler import Controller
from traitsui.item import UItem
from traitsui.view import View
from pychron.core.helpers.filetools import add_extension, to_bool, remove_extension
from pychron.core.helpers.logger_setup import logging_setup
from pychron.loggable import Loggable
from pychron.paths import paths


class InvalidSyntax(BaseException):
    pass


class InvalidFunction(BaseException):
    def __init__(self, name, valid):
        super(InvalidFunction, self).__init__()
        self.valid = valid
        self.name = name


class InvalidExperiment(BaseException):
    def __init__(self, name):
        self.name = name

class InvalidScript(BaseException):
    pass
    # def __init__(self, name):
    #     self.name = name


class FScript(Loggable):
    ctx = None
    console_event = Event

    def __init__(self, ctx, *args, **kw):
        self.ctx = ctx
        super(FScript, self).__init__(*args, **kw)

    def run(self, tokens):
        pass

    def start(self, tokens):
        self.debug('start fscript')
        self._check_tokens(tokens)
        return self.run(tokens)

    def _check_tokens(self, tokens):
        return True


class Run(FScript):
    def _check_tokens(self, tokens):
        valid = ('experiment',)
        try:
            func = tokens[0]
            if not func in valid:
                raise InvalidFunction(func, valid=valid)
        except IndexError:
            raise InvalidFunction('<no function provided>', valid=valid)

    def run(self, tokens):
        self.info('Do "Run" script. tokens={}'.format(tokens))
        self.debug('.... running ...')

        if tokens[0] == 'experiment':
            exp = self._do_experiment(tokens[1:])

        self.info('"Run" finished')
        return True

    def _do_experiment(self, tokens):
        if not tokens:
            name = 'Current Experiment'
        else:
            name = ' '.join(tokens)

        p = os.path.join(paths.experiment_dir, add_extension(name))
        if not os.path.isfile(p):
            raise InvalidExperiment(name)
        return name

    def list_exp_dir(self):
        root = paths.experiment_dir

        for i, di in enumerate((di for di in os.listdir(root) if os.path.isfile(os.path.join(root, di)))):
            self.console_event = {'message':remove_extension(di), 'indent':i}

CTX_REG = re.compile(r'^%\w+')


class Context(object):
    def __init__(self, name):
        self.name = name


class Foobot(Loggable):
    """

    """
    console = String
    message = String#('run experiment foas')

    context = None
    ee = False

    _state = None

    username = 'moo'

    def _message_changed(self, new):
        self._set_message(new)

    def _set_message(self, v):
        if v:
            self.console = '{}\n{}'.format(self.console, self.format_message(v))

            do_later(self.trait_set, message='')
            cmd = self.process_command(v)
            if cmd:
                self._update_console(cmd)

    def format_message(self, msg):
        return '{} >>> {}'.format(self.username, msg)

    def process_command(self, cmd):
        """
            cmd: str

            first token is the script name
        """
        if self._state:
            yes_no = self._get_affirmation(cmd)
            if isinstance(yes_no, bool):
                if yes_no:
                    self._state()
                    self._state = None
                    return

        self.ee = False
        context = self.get_context(cmd)
        if context:
            self.context = Context(context)
        else:

            if self.context and self.context.name == 'mz':
                if cmd == '80085':
                    self.ee = True
                    self._update_console('BOOBs BOOBs BOOBs')
                    return

            script, tokens = self.get_tokens(cmd)
            self.debug('doing script="{}"'.format(script))

            try:
                script_obj = self.script_factory(script)
            except InvalidScript:
                return 'I do not understand the command "{}"'.format(cmd)

            try:
                script_obj.start(tokens)
                return '{} Finished'.format(script)
            except InvalidSyntax:
                return 'I do not understand that syntax. "{}"'.format(cmd)
            except InvalidFunction, e:
                return '"{}" is not a valid function for "{}". valid={}'.format(e.name, script, ','.join(e.valid))
            except InvalidExperiment, e:
                self._state = script_obj.list_exp_dir
                return '"{}" is not a valid experiment. Would you like to list valid experiments?'.format(e.name)

    def get_context(self, cmd):
        m = CTX_REG.match(cmd)
        if m:
            return m.group(0)[1:]

    def get_tokens(self, cmd):
        lexer = shlex.shlex(cmd)
        return lexer.next(), [li for li in lexer]

    def get_script_name(self, cmd):
        script, toks = self.get_tokens(cmd)
        return script

    def script_factory(self, name):
        return self._load_script(name)

    def _get_affirmation(self, cmd):
        token = self.get_tokens(cmd)[0]
        b = to_bool(token)
        return b

    def _load_script(self, script):
        try:
            sobj = globals()[script.capitalize()]
        except KeyError:
            raise InvalidScript

        obj = sobj(self.context)
        obj.on_trait_change(self._update_console, 'console_event')
        return obj

    def _update_console(self, new):
        self.console = '{}\n{}'.format(self.console, self.format_bot_message(new))

    def format_bot_message(self, msg):
        if isinstance(msg, str):
            s = 'foobot >>> {}'.format(msg)
        else:
            s=msg.get('message')
            if msg.get('indent'):
                s = '                  {}'.format(s)
            else:
                s='foobot >>> {}'.format(s)
        return s


class FoobotChat(Controller):
    model = Instance(Foobot, ())

    def traits_view(self):
        v = View(UItem('console',
                       style='custom',
                       editor=TextEditor(read_only=True)),
                 UItem('message', editor=TextEditor(enter_set=True, auto_set=False)),
                 width=500,
                 height=400,
                 resizable=True)
        return v


if __name__ == '__main__':
    logging_setup('foobot')
    f = Foobot()
    fc = FoobotChat(model=f)
    fc.configure_traits()
