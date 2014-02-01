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
from datetime import datetime
import time
from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.experiment.utilities.identifier import make_aliquot_step, make_step
from pychron.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter
from pychron.loggable import Loggable

# http://stackoverflow.com/q/3844931/
from pychron.processing.analyses.analysis import DBAnalysis


def checkEqual6502(lst):
    return not lst or [lst[0]] * len(lst) == lst


class Datahub(Loggable):
    mainstore = Instance(IsotopeDatabaseManager)
    secondarystore = Instance(MassSpecDatabaseImporter, ())

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
        self._new_step = ''
        self._new_aliquot = 1

        if spec.is_step_heat():
            ps, ns, vs = self._get_greatest_step(spec.identifier, spec.aliquot)
            step = make_step(vs[0] + 1)
            self._new_runid = make_aliquot_step(spec.aliquot, step)
            self._new_step = step
            self._new_aliquot = spec.aliquot
        else:
            ps, ns, vs = self._get_greatest_aliquots(spec.identifier)
            print ps, ns, vs, spec.identifier
            self._new_runid = make_aliquot_step(vs[0] + 1, '')
            self._new_aliquot = vs[0] + 1


        # if sum(vs)/float(len(vs))!=vs[0]:
        if not checkEqual6502(vs):
            hn, hv = ns[0], vs[0]
            txt = []
            for ln, lv in zip(ns[1:], vs[1:]):
                if lv != hv:
                    txt.append('{}!={} {}!={}'.format(hn, ln, hv, lv))

            return ', '.join(txt)

    def update_spec(self, spec):
        spec.aliquot = self._new_aliquot
        spec.step = self._new_step
        self.debug('setting AutomatedRunSpec aliquot={}, step={}'.format(spec.aliquot,
                                                                         spec.step))

    def load_analysis_backend(self, ln, arar_age):
        db = self.mainstore.db
        with db.session_ctx():
            ln = db.get_labnumber(ln)
            if ln:
                an = DBAnalysis()
                x = datetime.now()
                now = time.mktime(x.timetuple())
                an.timestamp = now
                an.sync_irradiation(ln)

                arar_age.trait_set(j=an.j,
                                   production_ratios=an.production_ratios,
                                   interference_corrections=an.interference_corrections,
                                   chron_segments=an.chron_segments,
                                   irradiation_time=an.irradiation_time,
                                   timestamp=now)

                arar_age.calculate_decay_factors()

    @property
    def new_runid(self):
        return self._new_runid

    def get_greatest_aliquot(self, identifier, store='main'):
        store = getattr(self, '{}store'.format(store))
        return store.get_greatest_aliquot(identifier)

    def _get_greatest_aliquots(self, identifier):
        return zip(*[(store.precedence, store.db.name,
                      store.get_greatest_aliquot(identifier) if store.is_connected() else 0)
                     for store in self.sorted_stores])

    def _get_greatest_steps(self, identifier, aliquot):
        vs = [(store.precedence, store.name,
               store.get_greatest_step(identifier, aliquot) if store.is_connected() else 0)
              for store in (self.mainstore, self.secondarystore)]
        return vs

    _sorted_stores = None

    @property
    def sorted_stores(self):
        if self._sorted_stores:
            return self._sorted_stores
        else:
            r = sorted(filter(lambda x: x.is_connected(), (self.mainstore, self.secondarystore)))
            # r=sorted((self.mainstore, self.secondarystore))
            self._sorted_stores = r
            return r

            # if store and store.db:
            #     db=store.db
            #     with db.session_ctx():
            #         a=db.get_last_analysis(ln=identifier, ret='aliquot')
            #         if a is not None:
            #             if not isinstance(a, (float, int)):
            #                 a=int(a.aliquot)
            #             return a

    def add_experiment(self, exp):
        db = self.mainstore.db
        with db.session_ctx():
            dbexp = db.add_experiment(exp.path)
            exp.database_identifier = int(dbexp.id)

    def _datastores_default(self):
        return []

    bind_mainstore=True
    def _mainstore_default(self):
        mainstore = IsotopeDatabaseManager(precedence=1,
                                           connect=self.bind_mainstore,
                                           bind=self.bind_mainstore)

        return mainstore

#============= EOF =============================================

