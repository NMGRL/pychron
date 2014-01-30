import unittest
from pychron.processing.dataset.tests.mixin import IntensityMixin, analysis_args


class SignalTestCase(IntensityMixin):
# ======= signal err
    def test_Ar40_err(self):
        k = 'Ar40'
        self._signal_err(k)

    def test_Ar39_err(self):
        k = 'Ar39'
        self._signal_err(k)

    def test_Ar38_err(self):
        k = 'Ar38'
        self._signal_err(k)

    def test_Ar37_err(self):
        k = 'Ar37'
        self._signal_err(k)

    def test_Ar36_err(self):
        k = 'Ar36'
        self._signal_err(k)

    # ======= signal
    def test_Ar40(self):
        k = 'Ar40'
        self._signal(k)

    def test_Ar39(self):
        k = 'Ar39'
        self._signal(k)

    def test_Ar38(self):
        k = 'Ar38'
        self._signal(k)

    def test_Ar37(self):
        k = 'Ar37'
        self._signal(k)

    def test_Ar36(self):
        k = 'Ar36'
        self._signal(k)

    #===============================================
    def _signal(self, k):
        an = self.analysis
        v = an.isotopes[k].get_corrected_value()
        self._almost_equal(v.nominal_value, k)

    def _signal_err(self, k):
        an = self.analysis
        v = an.isotopes[k].get_corrected_value()
        self._almost_equal(v.std_dev, '{}Er'.format(k))

    def _interference_corrected(self, k):
        an = self.analysis
        v = an.isotopes[k].get_interference_corrected_value()
        self._almost_equal(v.nominal_value, '{}_DecayCor'.format(k))

class SignalTestCase_A(SignalTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args+(0,)


class SignalTestCase_B(SignalTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (1,)

class SignalTestCase_C(SignalTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (2,)

class SignalTestCase_D(SignalTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (3,)


class SignalTestCase_E(SignalTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (4,)

class SignalTestCase_F(SignalTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (5,)