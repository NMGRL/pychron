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
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.database.tasks.connection_preferences import ConnectionPreferencesPane, MassSpecConnectionPane
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


class DatabasePlugin(BaseTaskPlugin):
    id = 'pychron.database'
    name = 'Database'
    _connectable = False
    _db = None

    def test_pychron(self):
        iso = IsotopeDatabaseManager(application=self.application,
                                     version_warn=True, attribute_warn=True)
        self._db = iso
        self._connectable = c = iso.is_connected()
        return 'Passed' if c else 'Failed'

    def test_massspec(self):
        ret = 'Skipped'

        prefs = self.application.preferences

        def get_pref(v):
            return prefs.get('pychron.massspec.database.{}'.format(v))

        use_massspec = get_pref('enabled')
        if use_massspec:
            from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter

            name = get_pref('name')
            host = get_pref('host')
            password = get_pref('password')
            username = get_pref('username')
            db = MassSpecDatabaseAdapter(name=name,
                                         host=host,
                                         password=password,
                                         username=username)
            ret = 'Passed' if db.connect() else 'Failed'
        return ret

    def _preferences_panes_default(self):
        return [ConnectionPreferencesPane,
                MassSpecConnectionPane]

    def _service_offers_default(self):
        so = self.service_offer_factory(
            protocol=IsotopeDatabaseManager,
            factory=IsotopeDatabaseManager)
        return [so, ]

    def start(self):
        self.startup_test()
        if self._connectable:
            self._db.populate_default_tables()
            del self._db

            # ============= EOF =============================================
            #def _my_task_extensions_default(self):
            #    return [TaskExtension(actions=[SchemaAddition(id='update_database',
            #                                                  factory=UpdateDatabaseAction,
            #                                                  path='MenuBar/Tools')])]