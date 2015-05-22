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
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_persister import DVCPersister
from pychron.dvc.tasks.preferences import DVCPreferencesPane
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class DVCPlugin(BaseTaskPlugin):
    def test_dvc_fetch_meta(self):
        self.dvc.fetch_meta()

    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=DVCPersister,
                                        factory=DVCPersister)
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

    def _preferences_panes_default(self):
        return [DVCPreferencesPane]

        # def start(self):
        # add = not os.path.isfile(paths.meta_db)
        #
        # db = DVCDatabase()
        #     repo = MetaRepo()
        #
        #     if add:
        #         repo.add(db.path, commit=False)
        #         repo.commit('added {}'.format(db.path))

# ============= EOF =============================================



