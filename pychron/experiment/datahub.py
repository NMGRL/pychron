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
from pychron.database.adapters.massspec_database_adapter import MissingAliquotPychronException
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.experiment.utilities.identifier import make_aliquot_step, make_step
from pychron.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter
from pychron.loggable import Loggable

# http://stackoverflow.com/q/3844931/
from pychron.processing.analyses.dbanalysis import DBAnalysis
from pychron.processing.analyses.exceptions import NoProductionError


def checkEqual6502(lst):
    return not lst or [lst[0]] * len(lst) == lst


class Datahub(Loggable):
    mainstore = Instance(IsotopeDatabaseManager)
    secondarystore = Instance(MassSpecDatabaseImporter, ())

    bind_mainstore = True

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
            return str listing the differences if databases are in conflict
        """
        self._new_step = -1
        self._new_aliquot = 1
        self.debug('check for conflicts')
        self.secondary_connect()
        self.debug('connected to secondary')

        if spec.is_step_heat():
            k = 'Stepheat'
            self.debug('get greatest steps')
            ps, ns, vs = self._get_greatest_steps(spec.identifier, spec.aliquot)
            mv = max(vs) + 1
            step = make_step(mv)
            # print ps, ns, vs, spec.identifier
            self._new_runid = make_aliquot_step(spec.aliquot, step)
            self._new_step = mv
            self._new_aliquot = spec.aliquot
        else:
            k = 'Fusion'
            self.debug('get greatest aliquots')
            try:
                ps, ns, vs = self._get_greatest_aliquots(spec.identifier)

                # print 'b', ps, ns, vs, spec.identifier
                mv = max(vs)
                self._new_runid = make_aliquot_step(mv + 1, '')
                self._new_aliquot = mv + 1
            except MissingAliquotPychronException:
                self.warning('secondary db analyses missing aliquot_pychron')
                return 'secondary db analyses missing aliquot_pychron'

        self.debug('{} conflict args. precedence={}, names={}, values={}'.format(k, ps, ns, vs))
        if not checkEqual6502(list(vs)):
            hn, hv = ns[0], vs[0]
            txt = []
            for ln, lv in zip(ns[1:], vs[1:]):
                if lv != hv:
                    txt.append('{}!={} {}!={}'.format(hn, ln, hv, lv))
            err = ', '.join(txt)
            self.warning('Datastore conflicts. {}'.format(err))
            return err

    def update_spec(self, spec, aliquot_offset=0, step_offset=0):
        spec.aliquot = self._new_aliquot + aliquot_offset
        spec.step = self._new_step + step_offset
        spec.conflicts_checked = True

        self.debug('setting AutomatedRunSpec aliquot={}, step={}, increment={}'.format(spec.aliquot,
                                                                         spec.step,
                                                                         spec.increment))

    def load_analysis_backend(self, ln, arar_age):
        db = self.mainstore.db
        with db.session_ctx():
            ln = db.get_labnumber(ln)
            if ln:
                an = DBAnalysis()
                x = datetime.now()
                now = time.mktime(x.timetuple())
                an.timestamp = now
                try:
                    an.sync_irradiation(ln)
                except NoProductionError:
                    self.information_dialog('Irradiation={} Level={} has '
                                            'no Correction/Production Ratio set defined'.format(an.irradiation,
                                                                                                an.irradiation_level))
                    return False

                arar_age.trait_set(j=an.j,
                                   production_ratios=an.production_ratios,
                                   interference_corrections=an.interference_corrections,
                                   chron_segments=an.chron_segments,
                                   irradiation_time=an.irradiation_time,
                                   timestamp=now)

                arar_age.calculate_decay_factors()

    def add_experiment(self, exp):
        db = self.mainstore.db
        with db.session_ctx():
            dbexp = db.add_experiment(exp.path)
            exp.database_identifier = int(dbexp.id)

    def get_greatest_aliquot(self, identifier, store='main'):
        # store = getattr(self, '{}store'.format(store))
        # return store.get_greatest_aliquot(identifier)
        try:
            ps, ns, vs = self._get_greatest_aliquots(identifier)
            # print 'b',ps, ns, vs, spec.identifier
            mv = max(vs)
            return mv
        except MissingAliquotPychronException:
            pass

    def _get_greatest_aliquots(self, identifier):
        return zip(*[(store.precedence, store.db.name,
                      store.get_greatest_aliquot(identifier) or 0 if store.is_connected() else 0)
                     for store in self.sorted_stores])

    def _get_greatest_steps(self, identifier, aliquot):
        f = lambda x: x if x is not None else -1
        return zip(*[(store.precedence, store.db.name,
                      f(store.get_greatest_step(identifier, aliquot)) if store.is_connected() else -1)
                     for store in self.sorted_stores])

    def _datastores_default(self):
        return []

    def _mainstore_default(self):
        mainstore = IsotopeDatabaseManager(precedence=1,
                                           connect=self.bind_mainstore,
                                           bind=self.bind_mainstore)

        return mainstore

    @property
    def new_runid(self):
        return self._new_runid

    _sorted_stores = None
    @property
    def sorted_stores(self):
        if self._sorted_stores:
            return self._sorted_stores
        else:
            r = sorted(filter(lambda x: x.is_connected(),
                              (self.mainstore, self.secondarystore)),
                       key=lambda x: x.precedence)
            # r=sorted((self.mainstore, self.secondarystore))
            self._sorted_stores = r
            return r

#============= EOF =============================================

