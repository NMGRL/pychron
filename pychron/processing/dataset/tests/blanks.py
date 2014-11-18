from pychron.processing.dataset.tests.mixin import IntensityMixin


class BlankMeta(type):
    def __new__(mcs, name, bases, d):
        def gen_test(k):
            def test(self):
                self._blank(k)

            return test

        def gen_etest(k):
            def test(self):
                self._blank_err(k)

            return test

        for k in ('Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36'):
            d['test_{}_blank'.format(k)] = gen_test(k)
            d['test_{}_blank_err'.format(k)] = gen_etest(k)

        return type.__new__(mcs, name, bases, d)


class BlankTest(IntensityMixin):
    __metaclass__ = BlankMeta

    def _blank_err(self, k):
        an = self.analysis
        v = an.isotopes[k].blank.error
        self._almost_equal(v, '{}_BkgdEr'.format(k))

    def _blank(self, k):
        an = self.analysis
        v = an.isotopes[k].blank.value
        self._almost_equal(v, '{}_Bkgd'.format(k))
