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
import os
from traits.api import Instance, HasTraits, List, Str, Bool
from traitsui.api import View, VGroup, Item, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.experiment.utilities.identifier import make_runid
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceMixin


class LabnumberSelector(HasTraits, PersistenceMixin):
    irradiations = List
    irradiation = Str
    levels = List
    level = Str
    identifiers = List
    identifier = Str
    use_secondary = Bool
    use_secondary = Bool(True)
    persistence_path = os.path.join(paths.hidden_dir, 'labnumber_selector')

    pattributes = ('irradiation', 'level', 'identifier', 'use_secondary', 'use_main')

    def __init__(self, db, *args, **kw):

        super(LabnumberSelector, self).__init__(*args, **kw)
        self.db = db
        with db.session_ctx():
            self.irradiations = [i.name for i in db.get_irradiations()]
            if self.irradiations:
                self.irradiation = self.irradiations[0]

        self.load()

    def _irradiation_changed(self, new):
        if new:
            db = self.db
            with db.session_ctx():
                dbirrad = db.get_irradiation(new)
                self.levels = [li.name for li in dbirrad.levels]
                if self.levels:
                    self.level = ''
                    self.level = self.levels[0]
        else:
            self.levels = []
            self.level = ''

    def _level_changed(self, new):
        if new:
            db = self.db
            with db.session_ctx():
                level = db.get_irradiation_level(self.irradiation, new)
                self.identifiers = [li.labnumber.identifier for li in level.positions]
                if self.identifiers:
                    self.identifier = self.identifiers[0]
        else:
            self.identifiers = []
            self.identifier = ''

    def traits_view(self):
        v = View(VGroup(Item('irradiation', editor=EnumEditor(name='irradiations')),
                        Item('level', editor=EnumEditor(name='levels')),
                        Item('identifier', editor=EnumEditor(name='identifiers')),
                        Item('use_secondary', label='Use Secondary DB',
                             tooltip='Also modify the secondary db, e.g. a Mass Spec db.')),
                 kind='livemodal',
                 title='Select New Labnumber',
                 buttons=['OK', 'Cancel'])
        return v


class AnalysisModifier(Loggable):
    use_main = True
    use_secondary = False

    main_db = Instance(IsotopeAdapter)
    secondary_db = Instance(MassSpecDatabaseAdapter)

    def do_modification(self, ans):
        if not self.main_db.connect():
            self.debug('not connected main db')

        identifier = self.select_new_labnumber()
        if identifier:
            self.modify_analyses(ans, identifier)

    def select_new_labnumber(self):
        v = LabnumberSelector(self.main_db)
        info = v.edit_traits()
        if info.result:
            v.dump()
            self.use_main = v.use_main
            self.use_secondary = v.use_secondary
            return v.identifier

    def modify_analyses(self, ans, new_labnumber):
        self.info('Set labnumber to {}'.format(new_labnumber))
        for ai in ans:
            self.debug('setting {} to {}'.format(ai.record_id,
                                                 make_runid(new_labnumber,
                                                            ai.aliquot, ai.step)))

        if self.use_main:
            self._modify_main(ans, new_labnumber)

        if self.use_secondary:
            if self.secondary_db.connect():
                self._modify_secondary(ans, new_labnumber)
            else:
                self.debug('not connected to secondary db')

    def _modify_main(self, ans, new_labnumber):
        self.info('modifying analyses in main db')
        db = self.main_db
        if not db.connect():
            self.debug('Not connected to main db')
            return

        with db.session_ctx():
            dbln = db.get_labnumber(new_labnumber)

            for ai in ans:
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
                    dbirradpos = db.get_irradiation_position(new_labnumber)
                    if dbirradpos:
                        dban.RID = make_runid(new_labnumber, dban.Aliquot, dban.Increment)
                        dban.IrradPosition = new_labnumber
                        dban.RedundantSampleID = dbirradpos.SampleID
                    else:
                        self.warning('Labnumber {} does not exist in Secondary DB'.format(rid))
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



