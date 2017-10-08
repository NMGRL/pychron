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

from traits.api import Any, DelegatesTo, Property

from pychron.managers.manager import Manager
from pychron.paths import paths


class BaseSpectrometerManager(Manager):
    spectrometer = Any
    spectrometer_klass = None
    simulation = DelegatesTo('spectrometer')
    name = Property(depends_on='spectrometer')

    def test_connection(self, **kw):
        return self.spectrometer.test_connection(**kw)

    def test_intensity(self, **kw):
        return self.spectrometer.test_intensity(**kw)

    def _spectrometer_default(self):
        return self.spectrometer_klass(application=self.application)

    def send_configuration(self):
        if self.spectrometer:
            self.spectrometer.send_configuration()

    def reload_mftable(self):
        self.spectrometer.reload_mftable()

    def protect_detector(self, det, protect):
        pass

    def set_deflection(self, det, defl):
        pass

    def bind_preferences(self):
        pass

    def load(self, db_mol_weights=True):
        spec = self.spectrometer
        mftable = spec.magnet.mftable

        self.debug('******************************* LOAD Spec')
        if db_mol_weights:
            # get the molecular weights from the database
            # dbm = IsotopeDatabaseManager(application=self.application,
            #                              warn=False)
            dbm = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
            if dbm and dbm.is_connected():
                self.info('loading molecular_weights from database')
                mws = dbm.db.get_molecular_weights()
                # convert to a dictionary
                m = dict([(mi.name, mi.mass) for mi in mws])
                spec.molecular_weights = m
                mftable.db = dbm.db

        if not spec.molecular_weights:
            import csv
            # load the molecular weights dictionary
            p = os.path.join(paths.spectrometer_dir, 'molecular_weights.csv')
            if os.path.isfile(p):
                self.info('loading "molecular_weights.csv" file')
                with open(p, 'U') as f:
                    reader = csv.reader(f, delimiter='\t')
                    args = [[l[0], float(l[1])] for l in reader]
                    spec.molecular_weights = dict(args)
            else:
                self.info('writing a default "molecular_weights.csv" file')
                # make a default molecular_weights.csv file
                from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS as mw

                with open(p, 'U' if os.path.isfile(p) else 'w') as f:
                    writer = csv.writer(f, delimiter='\t')
                    data = [a for a in mw.itervalues()]
                    data = sorted(data, key=lambda x: x[1])
                    for row in data:
                        writer.writerow(row)
                spec.molecular_weights = mw

        self.spectrometer.load()
        mftable.spectrometer_name = self.spectrometer.name

        return True

    def finish_loading(self):
        self.debug('Finish loading')

        # integration_time = 1.048576

        # set device microcontrollers
        # self.spectrometer.set_microcontroller(self.spectrometer_microcontroller)
        # self.spectrometer.set_microcontroller()

        # update the current hv
        self.spectrometer.source.sync_parameters()

        # set integration time
        self.spectrometer.get_integration_time()
        # integration_time = self.spectrometer.get_integration_time()
        # self.integration_time = integration_time

        # self.integration_time = 0.065536

        self.spectrometer.load_configurations()

        self.bind_preferences()
        self.spectrometer.finish_loading()

    def _get_name(self):
        r = ''
        if self.spectrometer:
            if self.spectrometer.microcontroller:
                r = self.spectrometer.microcontroller.name
        return r

    def read_trap_current(self):
        return self.spectrometer.source.read_trap_current()

    def read_emission(self):
        return self.spectrometer.source.read_emission()
# ============= EOF =============================================



