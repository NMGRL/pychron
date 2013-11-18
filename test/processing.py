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
from itertools import groupby
from pychron.processing.selection.data_selector import FileSelector
from pychron.processing.processor import Processor
from test.database import isotope_manager_factory
#============= standard library imports ========================
#============= local library imports  ==========================

class AutoFigureTest(unittest.TestCase):
    def setUp(self):
        man = isotope_manager_factory()
        self.processor = Processor(bind=False,
                                   db=man.db
        )

    def testGetBlanks(self):
        ans = self.processor.load_series('blank_unknown',
                                         'jan',
                                         'Fusions Diode',
                                         weeks=8,
                                         hours=0)

        self.assertEqual(len(ans), 1)

    def testGetBlanks2(self):
        ans = self.processor.load_series('blank_unknown',
                                         'jan',
                                         'Fusions CO2',
                                         weeks=10,
                                         hours=0)
        ai = ans[0]
        self.assertEqual(ai.extract_device, 'Fusions CO2')


class FileSelectorTest(unittest.TestCase):
    def setUp(self):
        self.path = './data/import_template.xls'
        fs = FileSelector()
        fs.open_file(self.path)
        self.fs = fs

    def testNRuns(self):
        n = len(self.fs.records)
        self.assertEqual(n, 20)

    def testGrouping(self):
        '''
            
        '''

        groups = groupby(self.fs.records, lambda x: x.group_id)

        n = len([a for a in groups])
        self.assertEqual(n, 3)

    def testAge(self):
        fs = self.fs
        for idx, v in (
            (0, 27.4394071696971),
            (9, 27.7518808469669),
            (19, 27.2141624504905)
        ):
            self.assertAlmostEqual(fs.records[idx].age.nominal_value,
                                   v,
                                   places=7
            )

    def testAgeError(self):
        fs = self.fs
        for idx, v in (
            (0, 0.758322715007161),
            (9, 0.655152263100337),
            (19, 0.397634647177263)
        ):
            self.assertAlmostEqual(fs.records[idx].age.std_dev,
                                   v,
                                   places=7)

    def testStatus(self):
        fs = self.fs
        for idx, v in ((0, 1),
                       #                        (1, 0)
        ):
            self.assertEqual(fs.records[idx].status,
                             v
            )

    def testRecordID(self):
        fs = self.fs
        for idx, v in (
            (0, '10000-01'),
            (1, '10000-02'),
            (9, '10000-10'),

            (10, '10010-01'),
            (11, '10011-01'),

            (16, '10002-02B'),
            (19, '10002-02E'),

        ):
            self.assertEqual(fs.records[idx].record_id,
                             v)


#============= EOF =============================================
