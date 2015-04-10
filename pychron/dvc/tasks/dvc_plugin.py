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
import os
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dvc.dvc_persister import DVCPersister, DVCDatabase
from pychron.dvc.meta_repo import MetaRepo
from pychron.dvc.tasks.preferences import DVCPreferencesPane
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.paths import paths


class DVCPlugin(BaseTaskPlugin):
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=DVCPersister,
                                        factory=DVCPersister)
        so1 = self.service_offer_factory(protocol=DVCDatabase,
                                         factory=DVCDatabase)
        so2 = self.service_offer_factory(protocol=MetaRepo,
                                         factory=MetaRepo)
        return [so, so1, so2]

    def _preferences_panes_default(self):
        return [DVCPreferencesPane]

    def start(self):
        add = not os.path.isfile(paths.meta_db)

        db = DVCDatabase()
        repo = MetaRepo()

        if add:
            repo.add(db.path, commit=False)
            repo.commit('added {}'.format(db.path))

# ============= EOF =============================================



