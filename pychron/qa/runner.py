# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
import os
import yaml

# ============= local library imports  ==========================
from pychron.dvc.dvc import DVC
from pychron.loggable import Loggable
from pychron.qa.state import QAState


class QARunner(Loggable):

    def run(self):
        config_obj = self._load_tests()
        if not config_obj:
            return

        self._setup_dvc(config_obj['dvc'])
        state = self._load_state(config_obj['metadata'])

        for test in config_obj['tests']:
            self._do_test(state, test)

    def _setup_dvc(self, dvc_obj):
        self.dvc = dvc = DVC(bind=False)
        dvc.db.trait_set(**dvc_obj['connection'])
        dvc.trait_set(**dvc_obj['traits'])

        paths.dvc_dir = dvc_obj['root']
        paths.experiment_dataset_dir = os.path.join(paths.dvc_dir, 'experiments')

        dvc.initialize()

    def _load_state(self, metadata):
        state = QAState()

        dvc = self.dvc
        with dvc.session_ctx():
            records = dvc.db.get_analyses_uuid(metadata['uuids'])
            records = [r.record_view for r in records]
            ans = dvc.make_analyses(records)
            state.unknowns = ans

        return state

    def _load_tests(self):
        p = os.path.join(paths.root_dir, 'qa_env', 'config.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                return yaml.load(rfile)
        else:
            self.warning_dialog('No tests. Config file at "{}" required'.format(p))

    def _do_test(self, state, test):
        self.info('doing test {}'.format(test))
        qatest = self._get_test(test)

    def _get_test(self, test):
        mod = __import__('pychron.qa.test', fromlist=[test])
        return getattr(mod, test)()


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import paths

    paths.build('_dev')
    logging_setup('qa')

    qar = QARunner()
    qar.run()

# ============= EOF =============================================
