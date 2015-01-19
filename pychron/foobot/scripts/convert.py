from pychron.foobot.scripts.script import FScript


class Convert(FScript):
    def run(self, tokens):
        v = self._get_value(tokens)
        self.console_event = v
        return v

    def _get_value(self, tokens):
        return 100*float(''.join(tokens))


