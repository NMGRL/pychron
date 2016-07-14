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
# ============= standard library imports ========================
from numpy import array
# ============= local library imports  ==========================
from pychron.database.adapters.local_lab_adapter import LocalLabAdapter
from pychron.experiment.automated_run.persistence import AutomatedRunPersister
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.datahub import Datahub
from pychron.loggable import Loggable
from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.processing.arar_age import ArArAge
from pychron.processing.isotope import Isotope


class AnalysisRecoverer(Loggable):
    def recover_last_analysis(self):
        self.debug('recover last analysis')

        ldb = LocalLabAdapter()

        if not ldb.connect():
            self.warning('No analyses to recover')
            return

        lt = ldb.get_last_analysis()
        if lt is None:
            self.warning('No analyses to recover')
            return

        self.debug('last analysis Time: {}, Identifier: {}, Aliquot: {}'.format(lt.create_date,
                                                                                lt.labnumber,
                                                                                lt.aliquot))
        persister = AutomatedRunPersister()
        datahub = Datahub()
        persister.datahub = datahub

        per_spec = self._make_per_spec(lt)
        persister.per_spec = per_spec

        persister.post_extraction_save()
        persister.post_measurement_save(save_local=False)

    def _make_per_spec(self, lt):
        run_spec = AutomatedRunSpec()
        per_spec = PersistenceSpec()
        arar_age = ArArAge()

        # populate per_spec
        per_spec.run_spec = run_spec
        per_spec.arar_age = arar_age

        # popluate run_spec
        run_spec.identifier = lt.labnumber
        run_spec.aliquot = lt.aliquot
        run_spec.step = lt.step
        run_spec.username = 'analysis_recovery'
        run_spec.uuid = lt.uuid

        cp = lt.collection_path
        man = H5DataManager()
        man.open_file(cp)

        # add signal/isotopes
        group = man.get_group('signal')
        for grp in man.get_groups(group):
            isok = grp._v_name
            iso = Isotope(name=isok,
                          fit='linear')

            # only handle one detector per isotope
            tbl = man.get_tables(grp)[0]

            iso.detector = tbl._v_name
            xs = array([x['time'] for x in tbl.iterrows()])
            ys = array([x['value'] for x in tbl.iterrows()])

            iso.xs = xs
            iso.ys = ys

            arar_age.isotopes[isok] = iso

        # add sniffs
        group = man.get_group('sniff')
        for k, iso in arar_age.isotopes.iteritems():
            grp = man.get_group(k, group)
            tbl = man.get_tables(grp)[0]

            iso.sniff.detector = tbl._v_name
            xs = array([x['time'] for x in tbl.iterrows()])
            ys = array([x['value'] for x in tbl.iterrows()])
            iso.sniff.xs = xs
            iso.sniff.ys = ys

        # add baselines
        group = man.get_group('baseline')
        for dettbl in man.get_tables(group):
            detname = dettbl._v_name

            xs = array([x['time'] for x in dettbl.iterrows()])
            ys = array([x['value'] for x in dettbl.iterrows()])

            for iso in arar_age.isotopes.itervalues():
                if iso.detector == detname:
                    iso.baseline.xs = xs
                    iso.baseline.ys = ys
                    iso.baseline.fit = 'average'

        return per_spec

# ============= EOF =============================================



