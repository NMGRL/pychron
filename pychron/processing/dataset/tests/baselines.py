import unittest
from pychron.processing.dataset.tests.mixin import IntensityMixin, analysis_args


class BaselineCorrectedTestCase(IntensityMixin):
# ======= baseline only
    def test_Ar40_baseline_corrected(self):
        k = 'Ar40'
        self._baseline_corrected(k)

    def test_Ar39_baseline_corrected(self):
        k = 'Ar39'
        self._baseline_corrected(k)

    def test_Ar38_baseline_corrected(self):
        k = 'Ar38'
        self._baseline_corrected(k)

    def test_Ar37_baseline_corrected(self):
        k = 'Ar37'
        self._baseline_corrected(k)

    def test_Ar36_baseline_corrected(self):
        k = 'Ar36'
        self._baseline_corrected(k)

    # ======= baseline only error
    def test_Ar40_baseline_corrected_err(self):
        k = 'Ar40'
        self._baseline_corrected_err(k)

    def test_Ar39_baseline_corrected_err(self):
        k = 'Ar39'
        self._baseline_corrected_err(k)

    def test_Ar38_baseline_corrected_err(self):
        k = 'Ar38'
        self._baseline_corrected_err(k)

    def test_Ar37_baseline_corrected_err(self):
        k = 'Ar37'
        self._baseline_corrected_err(k)

    def test_Ar36_baseline_corrected_err(self):
        k = 'Ar36'
        self._baseline_corrected_err(k)

    def _baseline_corrected(self, k):
        an = self.analysis
        v = an.get_baseline_corrected_value(k)
        self._almost_equal(v.nominal_value, '{}_BslnCorOnly'.format(k))

    def _baseline_corrected_err(self, k):
        an = self.analysis
        v = an.get_baseline_corrected_value(k)
        self._almost_equal(v.std_dev, '{}_Er_BslnCorOnly'.format(k))

class BaselineCorrectedTestCase_A(BaselineCorrectedTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args+(0,)

class BaselineCorrectedTestCase_B(BaselineCorrectedTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (1,)

class BaselineCorrectedTestCase_C(BaselineCorrectedTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (2,)
class BaselineCorrectedTestCase_D(BaselineCorrectedTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (3,)

class BaselineCorrectedTestCase_E(BaselineCorrectedTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (4,)

class BaselineCorrectedTestCase_F(BaselineCorrectedTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (5,)
if __name__ == '__main__':
    unittest.main()