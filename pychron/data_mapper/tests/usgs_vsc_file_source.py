# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
from __future__ import absolute_import
import os
import unittest

import datetime

from pychron.data_mapper.sources.usgs_vsc_source import USGSVSCMAPSource
from pychron.data_mapper.tests import fget_data_dir
from pychron.data_mapper.tests.file_source import BaseFileSourceTestCase


class USGSVSCIrradiationSourceUnittest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = USGSVSCMAPSource()
        p = os.path.join(fget_data_dir(), 'IRR330.txt')
        cls.src.irradiation_path = p
        cls.spec = cls.src.get_irradiation_import_spec()

    def test_name(self):
        self.assertEqual('IRR330', self.spec.irradiation.name)

    def test_doses(self):
        self.assertEqual([(1.0, datetime.datetime(2014, 9, 23, 9, 13), datetime.datetime(2014, 9, 23, 10, 13))],
                         self.spec.irradiation.doses, [])

    def test_3637(self):
        self.assertEqual((2.810000E-4, 6.21e-6), self.spec.irradiation.levels[0].production.Ca3637)

    def test_4039(self):
        self.assertEqual((1.003E-3, 3.79e-4), self.spec.irradiation.levels[0].production.K4039)

    def test_3937(self):
        self.assertEqual((7.10E-4, 4.96e-5), self.spec.irradiation.levels[0].production.Ca3937)

    def test_3837(self):
        self.assertEqual((3.29E-5, 7.5e-6), self.spec.irradiation.levels[0].production.Ca3837)

    def test_3839(self):
        self.assertEqual((1.314E-2, 1.2e-5), self.spec.irradiation.levels[0].production.K3839)


class USGSVSCFileSourceUnittest(BaseFileSourceTestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = USGSVSCMAPSource()
        p = os.path.join(fget_data_dir(), '16Z0071', '16K0071A.TXT')
        cls.src.path = p
        cls.spec = cls.src.get_analysis_import_spec()
        cls.expected = {'runid': '16K0071-01A',
                        'irradiation': 'IRR347',
                        'irradiation_level': 'A',
                        'sample': 'GA1550',
                        'material': 'Bio',
                        'project': 'Std',
                        'j': 0.0045,
                        'j_err': 1e-7,
                        'timestamp_month': 3,
                        'cnt40': 40,
                        'cnt39': 50,
                        'cnt38': 10,
                        'cnt37': 10,
                        'cnt36': 80,
                        'discrimination': 1.0462399093612802,
                        'uuid': ''
                        }

    def test_irradiation(self):
        self.assertEqual(self.spec.run_spec.irradiation, self.expected['irradiation'])

    def test_level(self):
        self.assertEqual(self.spec.run_spec.irradiation_level, self.expected['irradiation_level'])

    def test_sample(self):
        self.assertEqual(self.spec.run_spec.sample, self.expected['sample'])

    def test_material(self):
        self.assertEqual(self.spec.run_spec.material, self.expected['material'])

    def test_project(self):
        self.assertEqual(self.spec.run_spec.project, self.expected['project'])

    def test_j(self):
        self.assertEqual(self.spec.j, self.expected['j'])

    def test_j_err(self):
        self.assertEqual(self.spec.j_err, self.expected['j_err'])


if __name__ == '__main__':
    unittest.main()

# ============= EOF =============================================
