from pychron.processing.dataset.tests.mixin import IntensityMixin


class BaselineMeta(type):
    def __new__(mcs, name, bases, d):
        def gen_test(k):
            def test(self):
                self._baseline_corrected(k)

            return test

        def gen_etest(k):
            def test(self):
                self._baseline_corrected_err(k)

            return test

        for k in ('Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36'):
            d['test_{}_baseline'.format(k)] = gen_test(k)
            d['test_{}_baseline_err'.format(k)] = gen_etest(k)

        return type.__new__(mcs, name, bases, d)


class BaselineCorrectedTest(IntensityMixin):
    __metaclass__ = BaselineMeta

    def _baseline_corrected(self, k):
        an = self.analysis
        v = an.get_baseline_corrected_value(k)
        self._almost_equal(v.nominal_value, '{}_BslnCorOnly'.format(k))

    def _baseline_corrected_err(self, k):
        an = self.analysis
        v = an.get_baseline_corrected_value(k)
        self._almost_equal(v.std_dev, '{}_Er_BslnCorOnly'.format(k))

