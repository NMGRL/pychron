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

import unittest
from pychron.processing.entry.labnumber_entry import LabnumberEntry
from test.database import isotope_manager_factory
#============= standard library imports ========================
#============= local library imports  ==========================

class LabEntryTest(unittest.TestCase):
    def setUp(self):
        db = isotope_manager_factory().db
        self.le = LabnumberEntry(db=db)

    #         self.le.irradiation = 'NM-251'
    #         self.le.level = 'H'

    #     def testNPositions(self):
    #         n = len(self.le.irradiated_positions)
    #         self.assertEqual(n, 12)
    #
    #     def testWrite(self):
    #         le = self.le
    #         le.make_table()

    def testLoadFile(self):
        p = './data/irradiation_import.xls'
        self.le.irradiation = 'TEST'

        self.le._load_positions_from_file(p, dry_run=False)

        self.assertEqual(self.le.irradiation, 'TEST')
        self.assertEqual(len(self.le.levels), 2)
        self.assertEqual(self.le.level, 'B')

        self.assertEqual(len(self.le.irradiated_positions), 61)
        self.assertEqual(self.le.irradiated_positions[0].sample, 'test_sample1')
        self.assertEqual(self.le.irradiated_positions[0].material, 'test_material')
        self.assertEqual(self.le.irradiated_positions[0].weight, 1.1)

#     def testLabnumberGenerator(self):
#         le = self.le
#         irradiation = 'TEST'
#         offset = 100000
# #         offset = 0
#         level_offset = 100
#         ge = le._labnumber_generator(irradiation, offset, level_offset)
#
#         lns = [li for li in ge]
#         self.assertListEqual(lns, [300000, 300001, 300100, 300101, 300200, 300201])
#         self.assertListEqual(lns, [200001, 200002, 200100, 200101, 200200, 200201])
#============= EOF =============================================
