from pychron.processing.dataset.tests.mixin import IntensityMixin

class SignalsMeta(type):
    def __new__(mcs, name, bases, d):
        def gen_test(k):
            def test(self):
                self._signal(k)
            return test

        def gen_etest(k):
            def test(self):
                self._signal_err(k)
            return test

        def gen_ifctest(k):
            def test(self):
                self._interference_corrected(k)
            return test

        for k in ('Ar40', 'Ar39','Ar38','Ar37','Ar36'):
            d['test_{}_signal'.format(k)]=gen_test(k)
            d['test_{}_signal_err'.format(k)]=gen_etest(k)
            d['test_{}_ifc'.format(k)]=gen_ifctest(k)

        return type.__new__(mcs, name, bases, d)


class SignalsTest(IntensityMixin):
    __metaclass__=SignalsMeta
    def _signal(self, k):
        an = self.analysis
        v = an.isotopes[k].get_non_detector_corrected_value()
        self._almost_equal(v.nominal_value, k)

    def _signal_err(self, k):
        an = self.analysis
        v = an.isotopes[k].get_non_detector_corrected_value()
        self._almost_equal(v.std_dev, '{}Er'.format(k))

    def _interference_corrected(self, k):
        an = self.analysis
        v = an.isotopes[k].get_interference_corrected_value()
        self._almost_equal(v.nominal_value, '{}_DecayCor'.format(k))


