import random

from pychron.foobot.scripts.script import FScript


class Hello(FScript):
    def run(self, tokens):
        self.console_event = random.choice(('Hi', 'Howdy', 'Hello', 'Hiya', 'Hola', 'Shalom'))

Hi = Hello
Howdy = Hello
Hiya = Hello
Hola = Hello
Shalom = Hello
