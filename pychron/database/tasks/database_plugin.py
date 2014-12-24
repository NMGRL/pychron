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
from pychron.database.tasks.replication_task import ReplicationTask
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

    def start(self):
        self.startup_test()
        if self._connectable:
            self._db.populate_default_tables()
            del self._db

    def test_pychron(self):
        iso = IsotopeDatabaseManager(application=self.application,
                                     version_warn=True, attribute_warn=True)
        self._db = iso
        self._connectable = c = iso.is_connected()
        return 'Passed' if c else 'Failed'

    def test_massspec(self):
        ret = 'Skipped'
        db = self.application.get_service('pychron.database.adapters.massspec_database_adapter.MassSpecDatabaseAdapter')
        if db:
            db.bind_preferences()
            ret = 'Passed' if db.connect() else 'Failed'

        return ret

    def _get_pref(self, name):
        prefs = self.application.preferences
        return prefs.get('pychron.massspec.database.{}'.format(name))

    def _slave_factory(self):
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
            #                              host=host,
            #                              password=password,
            #                              username=username)
            #

        return sos

# ============= EOF =============================================
            #def _task_extensions_default(self):
            #    return [TaskExtension(actions=[SchemaAddition(id='update_database',
            #                                                  factory=UpdateDatabaseAction,
            #                                                  path='MenuBar/Tools')])]