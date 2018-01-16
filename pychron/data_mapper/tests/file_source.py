import unittest


class BaseFileSourceTestCase(unittest.TestCase):
    def test_runid(self):
        self.assertEqual(self.spec.run_spec.runid, self.expected['runid'])

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

    def test_timestamp(self):
        ts = self.spec.timestamp
        self.assertEqual(ts.month, self.expected['timestamp_month'])

    def test_40_count_xs(self):
        self._test_count_xs('Ar40', self.expected['cnt40'])

    def test_40_count_ys(self):
        self._test_count_ys('Ar40', self.expected['cnt40'])

    def test_39_count_xs(self):
        self._test_count_xs('Ar39', self.expected['cnt39'])

    def test_39_count_ys(self):
        self._test_count_ys('Ar39', self.expected['cnt39'])

    def test_38_count_xs(self):
        self._test_count_xs('Ar38', self.expected['cnt38'])

    def test_38_count_ys(self):
        self._test_count_ys('Ar38', self.expected['cnt38'])

    def test_37_count_xs(self):
        self._test_count_xs('Ar37', self.expected['cnt37'])

    def test_37_count_ys(self):
        self._test_count_ys('Ar37', self.expected['cnt37'])

    def test_36_count_xs(self):
        self._test_count_xs('Ar36', self.expected['cnt36'])

    def test_36_count_ys(self):
        self._test_count_ys('Ar36', self.expected['cnt36'])

    def test_discrimination(self):
        disc = self.spec.discrimination
        self.assertEqual(disc, self.expected['discrimination'])

    def test_uuid(self):
        self.assertEqual(self.spec.run_spec.uuid, self.expected['uuid'])

    def _test_count_xs(self, k, cnt):
        xs = self.spec.isotope_group.isotopes[k].xs
        self.assertEqual(len(xs), cnt)

    def _test_count_ys(self, k, cnt):
        ys = self.spec.isotope_group.isotopes[k].ys
        self.assertEqual(len(ys), cnt)
if __name__ == '__main__':
    unittest.main()
