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
from copy import copy
import os
from traits.api import Instance, HasTraits, List, Str, Bool, Event, Int
from traitsui.api import View, VGroup, Item, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from traitsui.group import HGroup
from traitsui.item import UItem
from traitsui.tabular_adapter import TabularAdapter
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.experiment.utilities.identifier import make_runid
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceMixin
from pychron.processing.tasks.analysis_edit.selection_view import AnalysisAdapter


class AnalysisAdapter(TabularAdapter):
    font = '10'
    columns = [('Identifier', 'identifier'),
               ('Aliquot', 'aliquot'),
               ('Step', 'step')]


class AnalysisModifierView(HasTraits, PersistenceMixin):
    irradiations = List
    irradiation = Str
    levels = List
    level = Str
    identifiers = List
    identifier = Str
    use_main = Bool(True)
    use_secondary = Bool
    persistence_path = os.path.join(paths.hidden_dir, 'labnumber_selector')

    analyses = List
    modified_analyses = List
    selected = List
    refresh = Event
    aliquot_offset = Int
    step_offset = Int
    dry = Bool(False)

    pattributes = ('irradiation', 'level', 'identifier',
                   'use_secondary', 'use_main', 'dry')

    def __init__(self, db, *args, **kw):

        super(AnalysisModifierView, self).__init__(*args, **kw)
        self.db = db
        with db.session_ctx():
            self.irradiations = [i.name for i in db.get_irradiations()]
            if self.irradiations:
                self.irradiation = self.irradiations[0]

        self.load()

        self.modified_analyses = [copy(ai) for ai in self.analyses]

    def _irradiation_changed(self, new):
        if new:
            db = self.db
            with db.session_ctx():
                dbirrad = db.get_irradiation(new)
                if dbirrad:
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
                if level:
                    self.identifiers = [li.labnumber.identifier for li in level.positions]
                    if self.identifiers:
                        self.identifier = self.identifiers[0]
        else:
            self.identifiers = []
            self.identifier = ''

    def _aliquot_offset_changed(self, new):
        self._offset(new, 'aliquot')

    def _step_offset_changed(self, new):
        self._offset(new, 'increment')

    def _offset(self, new, attr):
        for i in self._get_items():
            oa = next((ai for ai in self.analyses if ai.uuid == i.uuid), None)
            if oa:
                setattr(i, attr, getattr(oa, attr) + new)

        self.refresh = True

    def _get_items(self):
        items = self.selected
        if not items:
            items = self.modified_analyses
        return items

    def _identifier_changed(self, new):
        if new:
            for i in self._get_items():
                i.identifier = new

            self.refresh = True

    def traits_view(self):
        ident_grp = VGroup(Item('irradiation', editor=EnumEditor(name='irradiations')),
                           Item('level', editor=EnumEditor(name='levels')),
                           Item('identifier', editor=EnumEditor(name='identifiers')),
                           Item('aliquot_offset'),
                           Item('step_offset'),
                           Item('dry',
                                tooltip='Do a dry run. Do not save changes to database'),
                           Item('use_secondary', label='Use Secondary DB',
                                tooltip='Also modify the secondary db, e.g. a Mass Spec db.'))

        ogrp = UItem('analyses', editor=TabularEditor(adapter=AnalysisAdapter(),
                                                      editable=False))
        ngrp = UItem('modified_analyses', editor=TabularEditor(adapter=AnalysisAdapter(),
                                                               refresh='refresh',
                                                               multi_select=True,
                                                               selected='selected'))
        agrp = HGroup(ogrp, ngrp)
        v = View(VGroup(ident_grp, agrp),
                 resizable=True,
                 width=600,
                 kind='livemodal',
                 title='Edit Analyses',
                 buttons=['OK', 'Cancel'])
        return v


class AnalysisModifier(Loggable):
    use_main = True
    use_secondary = False
    dry = False

    main_db = Instance(IsotopeAdapter)
    secondary_db = Instance(MassSpecDatabaseAdapter)

    def do_modification(self, ans):
        if not self.main_db.connect():
            self.debug('not connected main db')

        nans = self.define_modifications(ans)
        if nans:
            self.modify_analyses(ans, nans)

    def define_modifications(self, ans):
        v = AnalysisModifierView(self.main_db,
                                 analyses=ans)
        info = v.edit_traits()
        if info.result:
            v.dump()
            self.use_main = v.use_main
            self.use_secondary = v.use_secondary
            self.dry = v.dry
            return v.modified_analyses

    def modify_analyses(self, ans, nans):
        def func(ans, nans):
            for ai, ni in zip(ans, nans):
                if ai.record_id != ni.record_id:
                    self.debug('setting {} to {}'.format(ai.record_id, ni.record_id))
                    yield ai, ni

        ans, nans = zip(*func(ans, nans))

        if self.use_main:
            self._modify_main(ans, nans)

        if self.use_secondary:
            if self.secondary_db.connect():
                self._modify_secondary(ans, nans)
            else:
                self.debug('not connected to secondary db')

    def _modify_main(self, ans, new_ans):
        self.info('modifying analyses in main db. dry={}'.format(self.dry))
        db = self.main_db
        if not db.connect():
            self.debug('Not connected to main db')
            return

        with db.session_ctx(commit=not self.dry):
            for ai, ni in zip(ans, new_ans):
                dbln = db.get_labnumber(ni.identifier)
                dban = db.get_analysis_uuid(ai.uuid)
                dban.labnumber = dbln
                dban.aliquot = ni.aliquot
                dban.step = ni.step
                db.increment = ni.increment

    def _modify_secondary(self, ans, new_ans):
        self.info('modifying analyses in secondary db. dry={}'.format(self.dry))
        db = self.secondary_db
        if not db.connect():
            self.debug('Not connected to secondary db')
            return

        with db.session_ctx(commit=not self.dry):
            for ai, ni in zip(ans, new_ans):
                rid = ai.record_id
                dban = db.get_analysis_rid(rid)
                if dban:
                    ident = ni.identifier
                    dbirradpos = db.get_irradiation_position(ident)
                    if dbirradpos:
                        dban.RID = make_runid(ident, ni.aliquot, ni.step)
                        dban.Aliquot = '{:02n}'.format(int(ni.aliquot))
                        dban.Increment = ni.step
                        dban.Aliquot_pychron = ni.aliquot

                        dban.IrradPosition = ident
                        dban.RedundantSampleID = dbirradpos.SampleID
                    else:
                        self.unique_warning('Labnumber {} does not exist in Secondary DB'.format(ident))
                else:
                    self.warning('Analysis {} does not exist in Secondary DB'.format(rid))

                    # for ai in ans:
                    # rid = ai.record_id
                    # dban = db.get_analysis_rid(rid)
                    # if dban:
                    #         dbirradpos = db.get_irradiation_position(new_labnumber)
                    #         if dbirradpos:
                    #             dban.RID = make_runid(new_labnumber, dban.Aliquot, dban.Increment)
                    #             dban.IrradPosition = new_labnumber
                    #             dban.RedundantSampleID = dbirradpos.SampleID
                    #         else:
                    #             self.warning('Labnumber {} does not exist in Secondary DB'.format(rid))
                    #     else:
                    #         self.warning('Analysis {} does not exist in Secondary DB'.format(rid))

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



