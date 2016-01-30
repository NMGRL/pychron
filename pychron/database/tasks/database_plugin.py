# ===============================================================================
# Copyright 2013 Jake Ross
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
from envisage.ui.tasks.task_factory import TaskFactory

from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.database.tasks.connection_preferences import ConnectionPreferencesPane
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class DatabasePlugin(BaseTaskPlugin):
    id = 'pychron.database'
    name = 'Database'
    _connectable = False
    _db = None

    test_pychron_description = 'Test the connection to the Pychron Database'
    test_pychron_version_description = 'Test compatibility of Pychron with the current Database'

    test_pychron_error = ''
    test_pychron_version_error = ''

    def stop(self):
        from pychron.globals import globalv

        kind = globalv.prev_db_kind
        if kind:
            man = self._get_database_manager(connect=False)
            man.db.kind = globalv.prev_db_kind

    def start(self):
        self.startup_test()
        if self._connectable:
            self._db.populate_default_tables()
            del self._db

    def test_pychron_version(self):
        iso = self._get_database_manager()
        try:
            err = iso.db.test_version()
        except TypeError:
            err = 'Not connected'

        if err:
            self.test_pychron_version_error = err

        return 'Passed' if not err else 'Failed'

    def test_pychron(self):
        iso = self._get_database_manager()
        self._connectable = c = iso.is_connected()

        if not c:
            self.test_pychron_error = iso.db.connection_error

        return 'Passed' if c else 'Failed'

    def _get_database_manager(self, connect=True):
        if not self._db:
            iso = IsotopeDatabaseManager(application=self.application,
                                         warn=False,
                                         version_warn=False,
                                         attribute_warn=False,
                                         connect=connect)
            self._db = iso

        return self._db

    def _slave_factory(self):
        from pychron.database.tasks.replication_task import ReplicationTask

        s = ReplicationTask()
        return s

    def _tasks_default(self):
        return [TaskFactory(id='pychron.slave',
                            name='Replication',
                            factory=self._slave_factory)]

    def _preferences_panes_default(self):
        return [ConnectionPreferencesPane]

    def _service_offers_default(self):
        sos = [self.service_offer_factory(
            protocol=IsotopeDatabaseManager,
            factory=IsotopeDatabaseManager)]
        return sos

# ============= EOF =============================================
