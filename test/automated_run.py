#===============================================================================
# Copyright 2013 Jake Ross
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
from pychron.core.ui import set_toolkit
set_toolkit('qt4')
import unittest
from pychron.processing.isotope import Isotope
#============= standard library imports ========================
#============= local library imports  ==========================

class FitBlockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fits= ('Ar41:(,10,average), (10,,cubic)',
                   'Ar40:parabolic',
                   'Ar39AX:parabolic',
                   'Ar39CDD:parabolic',
                   'Ar38:linear',
                   'Ar37:linear',
                   'Ar36:parabolic')

    def testAr40Fit(self):
        iso=Isotope()

        fits = dict([f.split(':') for f in self.fits])

        iso.set_fit_blocks(fits['Ar41'])
        self.assertEqual(iso.get_fit(0), 'average')
        self.assertEqual(iso.get_fit(-1), 'cubic')
        self.assertEqual(iso.get_fit(100), 'cubic')

#
# class AutomatedRunTest(unittest.TestCase):
#     def setUp(self):
#         self.arun = AutomatedRun()
#
#         # db = isotope_manager_factory().db
#         # db.connect()
#         # self.arun.db = db
#
#     def testFits1(self):
#         fits = 'linear'
#         dets = ['H2', 'H1', 'AX']
#
#         self.arun.py_activate_detectors(('H2', 'H1', 'AX'))
#         self.arun.py_set_fits(fits)
#
#         self.assertEqual('linear', self.arun.arar_age.isotopes['Ar40'])
        # self.arun._active_detectors = dets
        # self.arun.py_set_regress_fits(fits)

        # self.assertListEqual(self.arun.fits, [(None, ['linear', 'linear', 'linear'])])

    # def testFits2(self):
    #     fits = ('linear', 'linear', 'parabolic')
    #     dets = ['H2', 'H1', 'AX']
    #     #         self.arun.py_activate_detectors(('H2', 'H1', 'AX'))
    #     self.arun._active_detectors = dets
    #     self.arun.py_set_regress_fits(fits)
    #
    #     self.assertListEqual(self.arun.fits, [(None, ['linear', 'linear', 'parabolic'])])
    #
    # def testFits3(self):
    #     fits = (
    #         ((0, 100), ('linear', 'linear', 'parabolic')),
    #     )
    #     dets = ['H2', 'H1', 'AX']
    #     #         self.arun.py_activate_detectors(('H2', 'H1', 'AX'))
    #     self.arun._active_detectors = dets
    #     self.arun.py_set_regress_fits(fits)
    #     self.assertListEqual(self.arun.fits,
    #                          [((0, 100), ['linear', 'linear', 'parabolic'])])
    #
    # def testGetFitBlock1(self):
    #     fits = ('linear', 'linear', 'parabolic')
    #     dets = ['H2', 'H1', 'AX']
    #     #         self.arun.py_activate_detectors(('H2', 'H1', 'AX'))
    #     self.arun._active_detectors = dets
    #     self.arun.py_set_regress_fits(fits)
    #     fits = self.arun._get_fit_block(10, self.arun.fits)
    #     self.assertListEqual(fits, ['linear', 'linear', 'parabolic'])
    #
    # def testGetFitBlock2(self):
    #     fits = (
    #         ((0, 100), ('linear', 'linear', 'parabolic')),
    #     )
    #     dets = ['H2', 'H1', 'AX']
    #     #         self.arun.py_activate_detectors(('H2', 'H1', 'AX'))
    #     self.arun._active_detectors = dets
    #     self.arun.py_set_regress_fits(fits)
    #     fits = self.arun._get_fit_block(150, self.arun.fits)
    #     self.assertListEqual(fits, ['linear', 'linear', 'parabolic'])
    #
    # def testGetFitBlock3(self):
    #     fits = (
    #         ((0, 100), ('linear', 'linear', 'parabolic')),
    #         ((100,), ('linear', 'linear', 'linear')),
    #     )
    #     dets = ['H2', 'H1', 'AX']
    #     #         self.arun.py_activate_detectors(('H2', 'H1', 'AX'))
    #     self.arun._active_detectors = dets
    #     self.arun.py_set_regress_fits(fits)
    #     fits = self.arun._get_fit_block(10, self.arun.fits)
    #     self.assertListEqual(fits, ['linear', 'linear', 'parabolic'])
    #
    # def testGetFitBlock4(self):
    #     fits = (
    #         ((0, 100), ('linear', 'linear', 'linear')),
    #         ((100, None), ('linear', 'linear', 'parabolic')),
    #     )
    #     dets = ['H2', 'H1', 'AX']
    #     #         self.arun.py_activate_detectors(('H2', 'H1', 'AX'))
    #     self.arun._active_detectors = dets
    #     self.arun.py_set_regress_fits(fits)
    #     #         print 'fffff', self.arun.fits
    #     fits = self.arun._get_fit_block(10, self.arun.fits)
    #     self.assertListEqual(fits, ['linear', 'linear', 'linear'])
    #
    #
    # @unittest.skip('check iteration')
    # def testCheckIteration(self):
    #     arun = self.arun
    #     attr = 'age'
    #     comp = '>'
    #     value = 10
    #     start_count = 0
    #     frequency = 1
    #
    #     conditions = [
    #         TruncationCondition(attr, comp, value,
    #                             start_count,
    #                             frequency)
    #     ]
    #
    #     cnt = 1
    #     arun.labnumber = '61311'
    #     arun.analysis_type = 'unknown'
    #     arun.start()
    #
    #     result = arun._check_conditions(conditions, cnt)
    #     self.assertEqual(result, True)

#     def testTermination(self):
#         grpname = 'signal'
#         ncounts = 10
#         starttime = 0
#         starttime_offset = 0
#         series = 0
#         fits = ('linear',)
#         check_conditions = True
#         def data_write_hook(*args):
#             pass
#
#         self.arun._measure_iteration(grpname, data_write_hook, ncounts,
#                                      starttime, starttime_offset, series,
#                                      fits, check_conditions, refresh)
#============= EOF =============================================
