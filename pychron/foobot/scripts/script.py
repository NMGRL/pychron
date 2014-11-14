from traits.trait_types import Event

from pychron.loggable import Loggable


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

