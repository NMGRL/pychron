import unittest
from pychron.processing.dataset.tests.mixin import IntensityMixin, analysis_args


class BlankTestCase(IntensityMixin):
# ======= blanks
    def test_Ar40_blank_err(self):
        k = 'Ar40'
        self._blank_err(k)

    def test_Ar40_blank(self):
        k = 'Ar40'
        self._blank(k)

    def test_Ar39_blank(self):
        k = 'Ar39'
        self._blank(k)

    def test_Ar38_blank(self):
        k = 'Ar38'
        self._blank(k)

    def test_Ar37_blank(self):
        k = 'Ar37'
        self._blank(k)

    def test_Ar36_blank(self):
        k = 'Ar36'
        self._blank(k)

    def _blank_err(self, k):
        an = self.analysis
        v = an.isotopes[k].blank.error
        self._almost_equal(v, '{}_BkgdEr'.format(k))

    def _blank(self, k):
        an = self.analysis
        v = an.isotopes[k].blank.value
        self._almost_equal(v, '{}_Bkgd'.format(k))




class BlankTestCase_A(BlankTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args+(0,)

class BlankTestCase_B(BlankTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (1,)

class BlankTestCase_C(BlankTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (2,)

class BlankTestCase_D(BlankTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (3,)

class BlankTestCase_E(BlankTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (4,)

class BlankTestCase_F(BlankTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (5,)