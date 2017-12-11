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
import os
import unittest

import datetime

from pychron.data_mapper.sources.usgs_vsc_source import USGSVSCMAPSource
from pychron.data_mapper.tests import fget_data_dir


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


class USGSVSCFileSourceUnittest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = USGSVSCMAPSource()
        p = os.path.join(fget_data_dir(), '16Z0071', '16K0071A.TXT')
        cls.src.path = p
        cls.spec = cls.src.get_analysis_import_spec()

    def test_runid(self):
        self.assertEqual(self.spec.run_spec.runid, '16K0071-01A')

    def test_irradiation(self):
        self.assertEqual(self.spec.run_spec.irradiation, 'IRR347')

    def test_level(self):
        self.assertEqual(self.spec.run_spec.irradiation_level, 'A')

    def test_sample(self):
        self.assertEqual(self.spec.run_spec.sample, 'GA1550')

    def test_material(self):
        self.assertEqual(self.spec.run_spec.material, 'Bio')

    def test_project(self):
        self.assertEqual(self.spec.run_spec.project, 'Std')

    def test_j(self):
        self.assertEqual(self.spec.j, 0.0045)

    def test_j_err(self):
        self.assertEqual(self.spec.j_err, 1e-07)

    def test_timestamp(self):
        ts = self.spec.timestamp
        self.assertEqual(ts.month, 3)

    def test_40_count_xs(self):
        self._test_count_xs('Ar40', 40)

    def test_40_count_ys(self):
        self._test_count_ys('Ar40', 40)

    def test_39_count_xs(self):
        self._test_count_xs('Ar39', 50)

    def test_39_count_ys(self):
        self._test_count_ys('Ar39', 50)

    def test_38_count_xs(self):
        self._test_count_xs('Ar38', 10)

    def test_38_count_ys(self):
        self._test_count_ys('Ar38', 10)

    def test_37_count_xs(self):
        self._test_count_xs('Ar37', 10)

    def test_37_count_ys(self):
        self._test_count_ys('Ar37', 10)

    def test_36_count_xs(self):
        self._test_count_xs('Ar36', 80)

    def test_36_count_ys(self):
        self._test_count_ys('Ar36', 80)

    def _test_count_xs(self, k, cnt):
        xs = self.spec.isotope_group.isotopes[k].xs
        self.assertEqual(len(xs), cnt)

    def _test_count_ys(self, k, cnt):
        ys = self.spec.isotope_group.isotopes[k].ys
        self.assertEqual(len(ys), cnt)

    def test_discrimination(self):
        disc = self.spec.discrimination
        self.assertEqual(disc, 1.0462399093612802)


if __name__ == '__main__':
    unittest.main()

# ============= EOF =============================================
