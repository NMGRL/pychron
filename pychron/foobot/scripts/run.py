import os

from pychron.core.helpers.filetools import add_extension, remove_extension
from pychron.foobot.exceptions import InvalidFunction, InvalidExperiment
from pychron.foobot.scripts.script import FScript
from pychron.paths import paths


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

