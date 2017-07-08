# ===============================================================================
# Copyright 2017 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from pychron.core.regression.ols_regressor import PolynomialRegressor
from pychron.core.regression.wls_regressor import WeightedPolynomialRegressor
from numpy import linspace
import matplotlib.pyplot as plt


# def get_data():
#     y = [76.14, 75.02, 73.34]
#     e = [0.06, 0.02, 0.03]
#     x = [29, 136, 384]
#
#     return x, y, e
def get_data():
    x = [29, 136, 181, 359, 384]
    y = [75.56, 74.56, 74.11, 73.37, 73.04]
    e = [0.2, 0.07, 0.31, .09, .13]
    return x,y,e


def results():
    x, y, e = get_data()
    reg = PolynomialRegressor(degree=1, xs=x, ys=y)

    mi, ma = min(x), max(x)
    pad = (ma - mi) * 0.1
    fxs = linspace(mi - pad, ma + pad)
    plt.errorbar(x, y,  yerr=e,)
    reg.calculate()

    l, u = reg.calculate_error_envelope(fxs, error_calc='CI')
    plt.plot(fxs, l, 'b')
    plt.plot(fxs, u, 'b')
    # plt.plot(fxs, reg.predict(fxs), 'b-')
    print 'Age={}, SD={} SEM={} CI={}'.format(reg.predict(328), reg.predict_error(328), reg.predict_error(328, 'SEM'),
                                        reg.predict_error(328, 'CI'))

    reg = WeightedPolynomialRegressor(degree=1, xs=x, ys=y, yserr=e)
    reg.calculate()
    plt.plot(fxs, reg.predict(fxs), 'g')
    l,u=reg.calculate_error_envelope(fxs, error_calc='CI')
    plt.plot(fxs, l, 'r')
    plt.plot(fxs, u, 'r')

    print 'Weighted fit Age={}, SD={} SEM={} CI={}'.format(reg.predict(328),
                                                     reg.predict_error(328), reg.predict_error(328,'SEM'),
                                                     reg.predict_error(328, 'CI'))
    plt.show()


if __name__ == '__main__':
    results()



# ============= EOF =============================================
