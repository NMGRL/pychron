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

from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.mass_spec.database.massspec_database_adapter import MissingAliquotPychronException
from pychron.dvc.dvc import DVC
from pychron.experiment.utilities.identifier import make_aliquot_step, make_step, get_analysis_type
from pychron.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter
from pychron.loggable import Loggable

# http://stackoverflow.com/q/3844931/


def check_list(lst):
    """
        return True if list is empty or
        all elements equal e.g [1,1,1,1,1]
    """
    return not lst or [lst[0]] * len(lst) == lst


def check_secondary_database_save(identifier):
    ret = True
    if identifier == 'bu-debug':
        ret = False
    elif get_analysis_type(identifier) == 'detector_ic':
        ret = False
    return ret


class Datahub(Loggable):
    mainstore = Instance(DVC)
    secondarystore = Instance(MassSpecDatabaseImporter, ())

    bind_mainstore = True
    massspec_enabled = Bool

    def bind_preferences(self):
        prefid = 'pychron.massspec.database'

        bind_preference(self, 'massspec_enabled', '{}.enabled'.format(prefid))
        if self.massspec_enabled:
            bind_preference(self.secondarystore.db, 'name', '{}.name'.format(prefid))
            bind_preference(self.secondarystore.db, 'host', '{}.host'.format(prefid))
            bind_preference(self.secondarystore.db, 'username', '{}.username'.format(prefid))
            bind_preference(self.secondarystore.db, 'password', '{}.password'.format(prefid))

    def secondary_connect(self):
        self.debug('secondary enabled {}'.format(self.massspec_enabled))
        if self.massspec_enabled:
            if self.secondarystore:
                return self.secondarystore.connect()
        else:
            return True

    def has_secondary_store(self):
        if self.massspec_enabled:
            return self.secondarystore and self.secondarystore.db.connected

    def is_conflict(self, spec):
        """
            return str listing the differences if databases are in conflict
        """

        self._new_step = -1
        self._new_aliquot = 1
        self.debug('check for conflicts')
        if check_secondary_database_save(spec.identifier):
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
            self.debug('get greatest aliquots for {}'.format(spec.identifier))
            try:
                ps, ns, vs = self._get_greatest_aliquots(spec.identifier)
                self.debug('greatest aliquots. Sources: {}, Precedences: {}, Aliquots: {}'.format(ns, ps, vs))
                mv = max(vs)
                self._new_runid = make_aliquot_step(mv + 1, '')
                self._new_aliquot = mv + 1
            except MissingAliquotPychronException:
                self.warning('secondary db analyses missing aliquot_pychron')
                return 'secondary db analyses missing aliquot_pychron'

        self.debug('{} conflict args. precedence={}, names={}, values={}'.format(k, ps, ns, vs))
        if not check_list(list(vs)):
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

    def load_analysis_backend(self, ln, isotope_group):
        dvc = self.mainstore
        return dvc.load_analysis_backend(ln, isotope_group)

    def add_experiment(self, exp):
        db = self.mainstore.db
        with db.session_ctx() as sess:
            dbexp = db.add_experiment(exp.path)

            sess.flush()
            exp.database_identifier = dbexp.id

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
        if not check_secondary_database_save(identifier):
            main = self.mainstore
            return (main.precedence,), (main.db.name,), (main.get_greatest_aliquot(identifier),)
        else:
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

    # def _mainstore_default(self):
    #     # mainstore = DVC(precedence=1,
    #     #                 connect=self.bind_mainstore,
    #     #                 bind=self.bind_mainstore)
    #     mainstore = self.application.get_service('pychron.dvc.dvc.DVC')
    #     mainstore.precedence = 1
    #
    #     return mainstore

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

# ============= EOF =============================================
