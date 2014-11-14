import os
from pyface.timer.do_later import do_later

from pychron.core.helpers.filetools import add_extension, remove_extension
from pychron.foobot.exceptions import InvalidFunction, InvalidExperiment
from pychron.foobot.scripts.script import FScript
from pychron.paths import paths

EXP_ID= 'pychron.experiment.task'

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
            name, path = self._get_experiment(tokens[1:])
            if self.application:
                def func():
                    task = self.application.get_task(EXP_ID)
                    if task:
                        if task.open(path):
                            self.console_event='Running experiment "{}"'.format(name)
                            task.execute()
                    else:
                        self.warning('no experiment task available')
                do_later(func)
            else:
                self.debug('no application')

        self.info('"Run" finished')
        return True

    def _get_experiment(self, tokens):
        if not tokens:
            name = 'Current Experiment'
        else:
            name = ' '.join(tokens)

        p = os.path.join(paths.experiment_dir, add_extension(name))
        if not os.path.isfile(p):
            raise InvalidExperiment(name)
        return name,p

    def list_exp_dir(self):
        root = paths.experiment_dir

        for i, di in enumerate((di for di in os.listdir(root) if os.path.isfile(os.path.join(root, di)))):
            self.console_event = {'message':remove_extension(di), 'indent':i}

