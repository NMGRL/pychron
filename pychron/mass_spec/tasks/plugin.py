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
from __future__ import absolute_import
from traits.api import List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.data_mapper.sources.mass_spec_source import MassSpecDBSource
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.mass_spec.database.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.mass_spec.mass_spec_recaller import MassSpecRecaller
from pychron.mass_spec.tasks.preferences import (
    MassSpecConnectionPane,
    MassSpecConfigPane,
)


class MassSpecPlugin(BaseTaskPlugin):
    id = "pychron.mass_spec.plugin"
    name = "MassSpec"
    sources = List(contributes_to="pychron.entry.data_sources")

    def _sources_default(self):
        db = self._db_factory()
        return [
            ("Mass Spec", MassSpecDBSource(db=db)),
        ]

    def test_database(self):
        ret, err = "Skipped", ""
        db = self._db_factory()
        if db:
            connected = db.connect(warn=False)
            ret = "Passed"
            if not connected:
                err = db.connection_error
                ret = "Failed"
        return ret, err

    def _preferences_panes_default(self):
        return [MassSpecConnectionPane, MassSpecConfigPane]

    def _recaller_factory(self):
        db = self._db_factory()
        recaller = MassSpecRecaller(db=db)
        return recaller

    def _get_pref(self, name):
        prefs = self.application.preferences
        return prefs.get("pychron.massspec.database.{}".format(name))

    def _db_factory(self):
        db = self.application.get_service(MassSpecDatabaseAdapter)
        if db:
            db.bind_preferences()
        return db

    def _service_offers_default(self):
        sos = []
        if self._get_pref("enabled"):
            sos.append(
                self.service_offer_factory(
                    protocol=MassSpecDatabaseAdapter, factory=MassSpecDatabaseAdapter
                )
            )

            sos.append(
                self.service_offer_factory(
                    protocol=MassSpecRecaller, factory=self._recaller_factory
                )
            )

        return sos


# ============= EOF =============================================
