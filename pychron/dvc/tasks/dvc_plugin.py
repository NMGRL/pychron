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
from pychron.dvc.tasks.actions import PullAnalysesAction
from pychron.dvc.tasks.preferences import DVCPreferencesPane, DVCDBConnectionPreferencesPane
from pychron.dvc.tasks.repo_task import ExperimentRepoTask
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class DVCPlugin(BaseTaskPlugin):
    _fetched = False

    def start(self):
        super(DVCPlugin, self).start()

        dvc = self.application.get_service(DVC)
        if not self._fetched:
            dvc.meta_repo.pull()

    # def stop(self):
    #     dvc = self.application.get_service(DVC)
    #     prog = open_progress(n=2)
    #     prog.change_message('Pushing changes to meta repository')
    #     dvc.meta_repo.cmd('push', '-u','origin','master')

    def test_dvc_fetch_meta(self):
        dvc = self.application.get_service(DVC)
        # dvc.fetch_meta()
        dvc.meta_repo.pull()
        self._fetched = True

    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=DVCPersister,
                                        factory=DVCPersister,
                                        properties={'dvc': self.dvc_factory()}
                                        )
        # so1 = self.service_offer_factory(protocol=DVCDatabase,
        # factory=DVCDatabase)
        # so2 = self.service_offer_factory(protocol=MetaRepo,
        # factory=MetaRepo)
        so2 = self.service_offer_factory(protocol=DVC,
                                         factory=self.dvc_factory)
        return [so, so2]

    def dvc_factory(self):
        d = DVC()
        # d.initialize()

        return d

    def _repo_factory(self):
        dvc = self.application.get_service(DVC)
        r = ExperimentRepoTask(dvc=dvc)
        return r

    def _preferences_default(self):
        return [self._make_preferences_path('dvc')]

    def _preferences_panes_default(self):
        return [DVCPreferencesPane, DVCDBConnectionPreferencesPane]

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
        return [TaskExtension(actions=[SchemaAddition(factory=PullAnalysesAction,
                                                      path='MenuBar/data.menu')]), ]
# ============= EOF =============================================
