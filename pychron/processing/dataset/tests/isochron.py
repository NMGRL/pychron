
from pychron.processing.dataset.tests.mixin import  IntensityMixin


class IsochronTest(IntensityMixin):

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



