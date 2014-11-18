from pychron.core.ui import set_qt

set_qt()
from unittest import TestCase
from pychron.processing.isotope import Isotope
import numpy as np
from pychron.core.regression.ols_regressor import OLSRegressor

__author__ = 'ross'


class IsotopeTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # xs=[0,1,2,3,4,5,6,7,8,9,10]
        # ys=[0,1,2,3,4,5,6,7,8,9,10]
        m = 1
        b = 1
        xs = np.linspace(0, 10, 10)
        ys = xs * m + b

        ys[5] = 0

        cls.iso = Isotope(xs=xs, ys=ys)


        # cls.iso.filter_outliers_dict=fod
        cls.intercept = b
        cls.slope = m

        cls.reg = OLSRegressor(xs=xs, ys=ys, fit='linear')
        # cls.reg.filter_outliers_dict=fod

    def setUp(self):
        fod = dict(filter_outliers=True,
                   iterations=1, std_devs=2)
        self.iso.set_filtering(fod)
        self.reg.filter_outliers_dict = fod

    def test_reg_intercept(self):
        self.reg.calculate()
        self.assertAlmostEqual(self.reg.predict(0), self.intercept)

    def test_iso_intercept(self):
        self.assertAlmostEqual(self.iso.uvalue.nominal_value, self.intercept)

    def test_fail_iso_intercept(self):
        self.iso.set_filtering(dict(filter_outliers=False,
                                    iterations=1, std_devs=2))

        self.assertNotAlmostEqual(self.iso.uvalue.nominal_value, self.intercept)