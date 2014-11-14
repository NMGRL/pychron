from pychron.core.ui import set_qt
from pychron.foobot.exceptions import InvalidScript, InvalidSyntax, InvalidFunction, InvalidExperiment

set_qt()
import re
import shlex
from pyface.timer.do_later import do_later
from traits.trait_types import Instance, String
from traitsui.editors import TextEditor
from traitsui.handler import Controller
from traitsui.item import UItem
from traitsui.view import View
from pychron.core.helpers.filetools import to_bool
from pychron.core.helpers.logger_setup import logging_setup
from pychron.loggable import Loggable


CTX_REG = re.compile(r'^%\w+')


class Context(object):
    def __init__(self, name):
        self.name = name


class Foobot(Loggable):
    """

    """
    console = String
    message = String  # ('run experiment foas')

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
            if isinstance(cmd, str):
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
                ret = script_obj.start(tokens)
                return ret  # '{} Finished'.format(script)
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
        name = script.capitalize()
        try:
            mod = __import__('pychron.foobot.scripts.{}'.format(script), fromlist=[name])
            sobj = getattr(mod, name)
        except BaseException:
            raise InvalidScript

        obj = sobj(self.context)
        obj.on_trait_change(self._update_console, 'console_event')
        return obj

    def _update_console(self, new):
        self.console = '{}\n{}'.format(self.console, self.format_bot_message(new))

    def format_bot_message(self, msg):
        if not isinstance(msg, dict):
            s = 'foobot >>> {}'.format(msg)
        else:
            s = msg.get('message')
            if msg.get('indent'):
                s = '                  {}'.format(s)
            else:
                s = 'foobot >>> {}'.format(s)
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
