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

from pychron.core.test_helpers import get_data_dir
from pychron.data_mapper.sources.usgs_menlo_source import USGSMenloSource


def fget_data_dir():
    op = 'pychron/data_mapper/tests/data'
    return get_data_dir(op)


class USGSMenloFileSourceUnittest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = USGSMenloSource()
        p = os.path.join(fget_data_dir(), '16F0203A.TXT')
        cls.spec = cls.src.get_analysis_import_spec(p)

    def test_runid(self):
        self.assertEqual(self.spec.run_spec.runid, '16F0203A')

    def test_irradiation(self):
        self.assertEqual(self.spec.run_spec.irradiation, 'IRR351')

    def test_level(self):
        self.assertEqual(self.spec.run_spec.irradiation_level, 'OQ')

    def test_sample(self):
        self.assertEqual(self.spec.run_spec.sample, 'TM-13-04')

    def test_material(self):
        self.assertEqual(self.spec.run_spec.material, 'Andesite')

    def test_project(self):
        self.assertEqual(self.spec.run_spec.project, 'Pagan')

    def test_j(self):
        self.assertEqual(self.spec.j, 0.000229687907897)

    def test_j_err(self):
        self.assertEqual(self.spec.j_err, 0.00000055732)

    def test_timestamp(self):
        ts = self.spec.run_spec.analysis_timestamp
        self.assertEqual(ts.month, 7)

    def test_40_count_xs(self):
        self._test_count_xs('Ar40', 40)

    def test_40_count_ys(self):
        self._test_count_ys('Ar40', 40)

    def test_39_count_xs(self):
        self._test_count_xs('Ar39', 40)

    def test_39_count_ys(self):
        self._test_count_ys('Ar39', 40)

    def test_38_count_xs(self):
        self._test_count_xs('Ar38', 5)

    def test_38_count_ys(self):
        self._test_count_ys('Ar38', 5)

    def test_37_count_xs(self):
        self._test_count_xs('Ar37', 5)

    def test_37_count_ys(self):
        self._test_count_ys('Ar37', 5)

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
        self.assertEqual(disc, 1.0505546075085326)


if __name__ == '__main__':
    unittest.main()

# ============= EOF =============================================
