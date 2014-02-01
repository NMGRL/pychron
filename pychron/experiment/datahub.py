#===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.experiment.utilities.identifier import make_aliquot_step, make_step
from pychron.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter
from pychron.loggable import Loggable


class Datahub(Loggable):

    mainstore=Instance(IsotopeDatabaseManager)
    secondarystore=Instance(MassSpecDatabaseImporter, ())

    def bind_preferences(self):

        prefid = 'pychron.database'

        bind_preference(self.secondarystore.db, 'name', '{}.massspec_dbname'.format(prefid))
        bind_preference(self.secondarystore.db, 'host', '{}.massspec_host'.format(prefid))
        bind_preference(self.secondarystore.db, 'username', '{}.massspec_username'.format(prefid))
        bind_preference(self.secondarystore.db, 'password', '{}.massspec_password'.format(prefid))

    def secondary_connect(self):
        if self.secondarystore:
            return self.secondarystore.connect()

    def has_secondary_store(self):
        return self.secondarystore and self.secondarystore.db.connected

    def is_conflict(self, spec):
        """
            return True if databases are in conflict
        """
        self._new_step=''
        self._new_aliquot=1

        if spec.is_step_heat():
            ps, ns, vs=self._get_greatest_step(spec.identifier, spec.aliquot)
            step=make_step(vs[0]+1)
            self._new_runid = make_aliquot_step(spec.aliquot, step)
            self._new_step = step
            self._new_aliquot=spec.aliquot
        else:
            ps,ns, vs=self._get_greatest_aliquots(spec.identifier)
            self._new_runid = make_aliquot_step(vs[0]+1, '')
            self._new_aliquot = vs[0]+1

        if sum(vs)/float(len(vs))!=vs[0]:

            hn, hv=ns[0], vs[0]
            txt=''
            for _,ln,lv in zip(ns[1:], vs[1:]):
                if lv!=hv:
                    txt.append('{}!={} {}!={}'.format(hn,ln, hv,lv))

            return ', '.join(txt)

    def update_spec(self, spec):
        spec.aliquot=self._new_aliquot
        spec.step=self._new_step
        self.debug('setting AutomatedRunSpec aliquot={}, step={}'.format(spec.aliquot,
                                                                         spec.step))

    @property
    def new_runid(self):
        return self._new_runid

    def get_greatest_aliquot(self, identifier, store='main'):
        store=getattr(self, '{}store'.format(store))
        return store.get_greatest_aliquot(identifier)

    def _get_greatest_aliquots(self, identifier):
        return zip(*[(store.precedence, store.name, store.get_greatest_aliquot(identifier))
            for store in self.sorted_stores])

    def _get_greatest_steps(self, identifier, aliquot):
        vs = [(store.precedence, store.get_greatest_step(identifier, aliquot))
              for store in (self.mainstore, self.secondarystore)]
        return vs

    _sorted_stores=None
    @property
    def sorted_stores(self):
        if self._sorted_stores:
            return self._sorted_stores
        else:
            r=sorted((self.mainstore, self.secondarystore))
            self._sorted_stores=r
            return r

        # if store and store.db:
        #     db=store.db
        #     with db.session_ctx():
        #         a=db.get_last_analysis(ln=identifier, ret='aliquot')
        #         if a is not None:
        #             if not isinstance(a, (float, int)):
        #                 a=int(a.aliquot)
        #             return a

    def _datastores_default(self):
        return []

    def _mainstore_default(self):
        mainstore=IsotopeDatabaseManager(precedence=1)

        return mainstore

#============= EOF =============================================

