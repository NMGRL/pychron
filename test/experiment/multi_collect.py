import time
from pychron.core.ui import set_toolkit
set_toolkit('qt4')

from pychron.paths import paths, build_directories

paths.build('_unittest')
build_directories(paths)

from pychron.core.helpers.logger_setup import logging_setup


from threading import Thread
from pychron.processing.arar_age import ArArAge
from pychron.spectrometer.ion_optics_manager import IonOpticsManager
from pychron.spectrometer.spectrometer_manager import SpectrometerManager
from pychron.experiment.automated_run.automated_run import AutomatedRun
from pychron.experiment.automated_run.spec import AutomatedRunSpec

import unittest
logging_setup('peak_hop')

from pychron.experiment.datahub import Datahub
#HOPS = [('Ar40:H1:10,     Ar39:AX,     Ar36:CDD', 5, 1),
#        #('Ar40:L2,     Ar39:CDD',                   5, 1)
#        #('Ar38:CDD',                                5, 1)
#        ('Ar37:CDD', 5, 1)
#]
HOPS = [('Ar40:CDD', 5, 1),
        ('Ar39:CDD', 5, 1),
        ('Ar38:CDD', 5, 1),
        ('Ar37:CDD', 5, 1),
        ('Ar36:CDD', 5, 1)]

#from traits.api import HasTraits, Str, Button
#from traitsui.api import View
#
#class A(HasTraits):
#    a=Button
#    traits_view=View('a')
#    def _a_fired(self):
#        unittest.main(exit=False)

class MulticollectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        aspec = AutomatedRunSpec()
        aspec.mass_spectrometer = 'jan'
        aspec.labnumber = '17005'
        aspec.aliquot = 82
        aspec.syn_extraction='test'


        a = AutomatedRun()
        a.script_info.measurement_script_name = 'unknown'
        a.script_info.extraction_script_name = 'pause'

        s = SpectrometerManager()
        ion = IonOpticsManager(spectrometer=s.spectrometer)

        s.load(db_mol_weights=False)
        a.spectrometer_manager = s
        a.ion_optics_manager = ion
        a.arar_age = ArArAge()

        a._alive = True
        a.uuid = '12345-ABCDE'

        a.spec = aspec
        a._measured = True
        a.persister.save_enabled = True
        a.persister.datahub=dh=Datahub(bind_mainstore=False)
        dh.mainstore.db.kind='mysql'
        dh.mainstore.db.username='root'
        dh.mainstore.db.name='pychrondata_dev'
        dh.mainstore.db.password='Argon'
        dh.mainstore.db.connect()


        cls.arun = a

    def setUp(self):
        a = self.arun

        a.setup_persister()

        a.persister.pre_measurement_save()
        a._integration_seconds = 0.05

    def measure(self):
        t = Thread(name='run', target=self._measure)
        t.start()
        t.join()

    def _measure(self):
        a = self.arun

        counts = 5
        dets = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
        a.measurement_script.ncounts =5
        a.py_position_magnet('Ar40', 'H1')
        a.py_activate_detectors(dets)
        st = time.time()
        a.py_data_collection(counts, st, 0)
        a.py_baselines(10, st, 0, 39.5, 'H1', series=1)

    # def test_syn_extraction(self):
    #     a=self.arun
    #     a.use_syn_extraction = True
    #     ret=a.do_extraction()
    #     self.assertTrue(ret)

    def test_persister_runid(self):
        a = self.arun
        a.use_syn_extraction = False
        a.do_extraction()
        self.assertEqual(a.persister.runid, '17005-82')


        # def test_multicollect_save(self):
    #     self.measure()
    #
    #     msi = MassSpecDatabaseImporter()
    #     msi.connect(warn=False)
    #     arun = self.arun
    #     arun.persister.massspec_importer = msi
    #     ret = arun.post_measurement_save()
    #     self.assertTrue(ret)

        #def test_peak_hop_setup(self):
        #    a=self.arun
        #    self.measure()
        #    self.assertEqual(a._save_isotopes,
        #                     self.save_isotopes)


if __name__ == '__main__':
    unittest.main()
    #a=A()
    #a.configure_traits()
