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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition

from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_persister import DVCPersister
from pychron.dvc.tasks.actions import WorkOfflineAction, UseOfflineDatabase
from pychron.dvc.tasks.dvc_preferences import DVCPreferencesPane, \
    DVCDBConnectionPreferencesPane, DVCExperimentPreferencesPane
from pychron.dvc.tasks.repo_task import ExperimentRepoTask
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.git.hosts import IGitHost


class DVCPlugin(BaseTaskPlugin):
    name = 'DVC'
    _fetched = False

    def start(self):
        super(DVCPlugin, self).start()

        dvc = self.application.get_service(DVC)
        if not self._fetched:
            dvc.initialize()

        service = self.application.get_service(IGitHost)
        if not service:
            self.information_dialog('No GitHost Plugin enabled. (Enable GitHub or GitLab to share your changes)')

    def stop(self):
        # dvc = self.application.get_service(DVC)
        # prog = open_progress(n=2)
        # prog.change_message('Pushing changes to meta repository')
        # dvc.meta_repo.cmd('push', '-u','origin','master')

        dvc = self.application.get_service(DVC)
        with dvc.session_ctx(use_parent_session=False):
            names = dvc.get_usernames()
            self.debug('dumping usernames {}'.format(names))
            if names:
                from pychron.envisage.user_login import dump_user_file
                dump_user_file(names)

    def test_database(self):
        ret, err = True, ''
        dvc = self.application.get_service(DVC)
        db = dvc.db
        connected = db.connect(warn=False)
        if not connected:
            ret = False
            err = db.connection_error
        return ret, err

    def test_dvc_fetch_meta(self):
        ret, err = False, ''
        dvc = self.application.get_service(DVC)
        dvc.open_meta_repo()
        dvc.meta_pull()
        ret = self._fetched = True

        return ret, err

    def _service_offers_default(self):
        # p = {'dvc': self.dvc_factory()}
        # self.debug('DDDDD {}'.format(p))
        so = self.service_offer_factory(protocol=DVCPersister,
                                        factory=DVCPersister,
                                        properties={'dvc': self.dvc_factory()})

        so2 = self.service_offer_factory(protocol=DVC,
                                         factory=self.dvc_factory)

        return [so, so2]

    def dvc_factory(self):
        d = DVC(application=self.application)
        # d.initialize()

        return d

    def _repo_factory(self):
        dvc = self.application.get_service(DVC)
        r = ExperimentRepoTask(dvc=dvc)
        return r

    def _preferences_default(self):
        return self._preferences_factory('dvc')

    def _preferences_panes_default(self):
        return [DVCPreferencesPane, DVCDBConnectionPreferencesPane, DVCExperimentPreferencesPane]

    # def _tasks_default(self):
    #     ts = [TaskFactory(id='pychron.canvas_designer',
    #                       name='Canvas Designer',
    #                       factory=self._task_factory,
    #                       accelerator='Ctrl+Shift+D',
    #     )]
    #     return ts
    def _tasks_default(self):
        return [TaskFactory(id='pychron.experiment_repo.task',
                            name='Experiment Repositories',
                            factory=self._repo_factory)]
        # def start(self):
        # add = not os.path.isfile(paths.meta_db)
        #
        # db = DVCDatabase()
        #     repo = MetaRepo()
        #
        #     if add:
        #         repo.add(db.path, commit=False)
        #         repo.commit('added {}'.format(db.path))

    def _task_extensions_default(self):
        actions = [SchemaAddition(factory=WorkOfflineAction,
                                  path='MenuBar/tools.menu'),
                   SchemaAddition(factory=UseOfflineDatabase,
                                  path='MenuBar/tools.menu')]

        return [TaskExtension(actions=actions), ]

# ============= EOF =============================================
