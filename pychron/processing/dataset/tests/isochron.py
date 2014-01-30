import unittest
from pychron.processing.dataset.tests.mixin import analysis_args, IntensityMixin


class IsochronTestCase(IntensityMixin):
# ======= ratios

    def test_Ar39_Ar40(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a39 = an.isotopes['Ar39'].get_interference_corrected_value()

        r = a39 / a40

        self._almost_equal(r.nominal_value, 'Isoch_39_40')

    def test_Ar39_Ar40err(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a39 = an.isotopes['Ar39'].get_interference_corrected_value()

        r = a39 / a40

        self._almost_equal(r.std_dev / r.nominal_value * 100, 'Isoch_39_40err')

    def test_Ar36_Ar40(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a36 = an.isotopes['Ar36'].get_interference_corrected_value()
        r = a36 / a40

        self._almost_equal(r.nominal_value, 'Isoch_36_40')

    def test_Ar36_Ar40err(self):
        an = self.analysis
        a40 = an.isotopes['Ar40'].get_interference_corrected_value()
        a36 = an.isotopes['Ar36'].get_interference_corrected_value()
        r = a36 / a40
        self._almost_equal(r.std_dev / r.nominal_value * 100, 'Isoch_36_40err')


# #==============================================================================================================
class IsochronTestCase_A(IsochronTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (0,)

class IsochronTestCase_B(IsochronTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args + (1,)

class IsochronTestCase_C(IsochronTestCase, unittest.TestCase):
    @classmethod
    def set_analysis(cls):
        return analysis_args+(2,)

