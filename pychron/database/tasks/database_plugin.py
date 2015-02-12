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
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.database.tasks.connection_preferences import ConnectionPreferencesPane, MassSpecConnectionPane
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


class DatabasePlugin(BaseTaskPlugin):
    id = 'pychron.database'
    name = 'Database'
    _connectable = False
    _db = None

    test_pychron_description = 'Test the connection to the Pychron Database'
    test_massspec_description = 'Test the connection to the MassSpec Database'
    test_pychron_version_description = 'Test compatibility of Pychron with the current Database'

    test_pychron_error = ''
    test_massspec_error = ''
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
        err = iso.db.test_version()
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

    def test_massspec(self):
        ret = 'Skipped'
        db = self.application.get_service('pychron.database.adapters.massspec_database_adapter.MassSpecDatabaseAdapter')
        if db:
            db.bind_preferences()
            connected = db.connect(warn=False)
            ret = 'Passed'
            if not connected:
                self.test_massspec_error = db.connection_error
                ret = 'Failed'
        return ret

    def _get_pref(self, name):
        prefs = self.application.preferences
        return prefs.get('pychron.massspec.database.{}'.format(name))

    def _slave_factory(self):
        from pychron.database.tasks.replication_task import ReplicationTask

        s = ReplicationTask()
        return s

    def _tasks_default(self):
        return [TaskFactory(id='pychron.slave',
                            name='Replication',
                            factory=self._slave_factory)]

    def _preferences_panes_default(self):
        return [ConnectionPreferencesPane,
                MassSpecConnectionPane]

    def _service_offers_default(self):
        sos = [self.service_offer_factory(
            protocol=IsotopeDatabaseManager,
            factory=IsotopeDatabaseManager)]

        if self._get_pref('enabled'):
            from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter

            sos.append(self.service_offer_factory(
                protocol=MassSpecDatabaseAdapter,
                factory=MassSpecDatabaseAdapter))
            # name = self._get_pref('name')
            # host = self._get_pref('host')
            # password = self._get_pref('password')
            # username = self._get_pref('username')
            # db = MassSpecDatabaseAdapter(name=name,
            # host=host,
            #                              password=password,
            #                              username=username)
            #

        return sos

        # ============= EOF =============================================
        # def _task_extensions_default(self):
        #    return [TaskExtension(actions=[SchemaAddition(id='update_database',
        #                                                  factory=UpdateDatabaseAction,
        #                                                  path='MenuBar/Tools')])]