# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.experiment.utilities.identifier import make_runid
from pychron.loggable import Loggable


class AnalysisModifier(Loggable):
    use_main = True
    use_secondary = False

    main_db = Instance(IsotopeAdapter)
    secondary_db = Instance(MassSpecDatabaseAdapter)

    def modify_analyses(self, ans, new_labnumber):
        self.info('Set labnumber to {}'.format(new_labnumber))
        for ai in ans:
            self.debug('setting {} to {}'.format(ai.record_id,
                                                 make_runid(new_labnumber,
                                                            ai.aliquot, ai.step)))

        if self.use_main:
            self._modify_main(ans, new_labnumber)

        if self.use_secondary:
            self._modify_secondary(ans, new_labnumber)

    def _modify_main(self, ans, new_labnumber):
        self.info('modifying analyses in main db')
        db = self.main_db
        if not db.connect():
            self.debug('Not connected to main db')
            return

        with db.session_ctx():
            dbln = db.get_labnumber(new_labnumber)

            for ai in ans:
                print ai.uuid
                dban = db.get_analysis_uuid(ai.uuid)
                dban.labnumber = dbln

    def _modify_secondary(self, ans, new_labnumber):
        self.info('modifying analyses in secondary db')
        db = self.secondary_db
        if not db.connect():
            self.debug('Not connected to secondary db')
            return

        with db.session_ctx():
            for ai in ans:
                rid = ai.record_id
                dban = db.get_analysis_rid(rid)
                if dban:
                    dban.RID = make_runid(new_labnumber, dban.Aliquot, dban.Step)
                    dban.IrradPosition = new_labnumber
                else:
                    self.warning('Analysis {} does not exist in Secondary DB'.format(rid))

    def _main_db_default(self):
        from apptools.preferences.preference_binding import bind_preference

        db = IsotopeAdapter()
        prefid = 'pychron.database'
        bind_preference(db, 'kind', '{}.kind'.format(prefid))
        if db.kind == 'mysql':
            bind_preference(db, 'host', '{}.host'.format(prefid))
            bind_preference(db, 'username', '{}.username'.format(prefid))
            bind_preference(db, 'password', '{}.password'.format(prefid))

        bind_preference(db, 'name', '{}.db_name'.format(prefid))
        return db

    def _secondary_db_default(self):
        from apptools.preferences.preference_binding import bind_preference

        db = MassSpecDatabaseAdapter()
        prefid = 'pychron.massspec.database'
        bind_preference(db, 'host', '{}.host'.format(prefid))
        bind_preference(db, 'username', '{}.username'.format(prefid))
        bind_preference(db, 'name', '{}.name'.format(prefid))
        bind_preference(db, 'password', '{}.password'.format(prefid))
        return db
# ============= EOF =============================================



