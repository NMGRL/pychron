# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
# ============= enthought library imports =======================
from numpy import linspace, Inf, zeros_like
from scipy.optimize import fsolve
from traits.api import Array, Property, Float

# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import std_dev, ufloat

from pychron.core.regression.ols_regressor import OLSRegressor
from pychron.core.stats import calculate_mswd2
from pychron.core.stats.core import validate_mswd
from pychron.pychron_constants import MSE, SE


def kron(i, j):
    """ "
    # calculates Kronecker delta
    if i == j:
        return 1.
    else:
        return 0.
    """
    return int(i == j)


class YorkRegressor(OLSRegressor):
    """York 1969, Mahon 1996"""

    xns = Array
    xds = Array

    yns = Array
    yds = Array

    xnes = Array
    xdes = Array

    ynes = Array
    ydes = Array

    slope = Property
    _slope = Float

    intercept = Property
    _intercept = Float
    _intercept_variance = None

    x_intercept = Property
    x_intercept_error = Property

    mswd = Property
    error_calc_type = SE

    def calculate(self, *args, **kw):
        super(YorkRegressor, self).calculate(*args, **kw)

        if not len(self.xserr):
            return
        if not len(self.yserr):
            return

        # self.calculate_correlation_coefficients()
        self._calculate()

    def calculate_correlation_coefficients(self, clean=True):
        if len(self.xds):
            xds = self.xds
            xns = self.xns
            xdes = self.xdes
            xnes = self.xnes
            yns = self.yns
            ynes = self.ynes

            if clean:
                xds = self._clean_array(xds)
                xns = self._clean_array(xns)
                xdes = self._clean_array(xdes)
                xnes = self._clean_array(xnes)
                yns = self._clean_array(yns)
                ynes = self._clean_array(ynes)

            fd = xdes / xds  # f40Ar

            fyn = ynes / yns  # f36Ar
            fxn = xnes / xns  # f39Ar

            a = 1 + (fyn / fd) ** 2
            b = 1 + (fxn / fd) ** 2
            return (a * b) ** -0.5
        else:
            return zeros_like(self.clean_xs)

    def _get_weights(self):
        ex = self.clean_xserr
        ey = self.clean_yserr
        Wx = ex**-2
        Wy = ey**-2
        return Wx, Wy

    def _calculate_UV(self, W):
        xs = self.clean_xs
        ys = self.clean_ys

        # xs, ys = self.xs, self.ys
        x_bar, y_bar = self._calculate_xy_bar(W)
        U = xs - x_bar
        V = ys - y_bar
        return U, V

    def _calculate_xy_bar(self, W):
        # xs, ys = self.xs, self.ys
        xs, ys = self.clean_xs, self.clean_ys
        sW = sum(W)
        try:
            x_bar = sum(W * xs) / sW
            y_bar = sum(W * ys) / sW
        except ZeroDivisionError:
            x_bar, y_bar = 0, 0

        return x_bar, y_bar

    def get_slope(self):
        self.calculate()
        return self._slope

    def get_intercept(self):
        self.calculate()
        return self._intercept

    def get_intercept_error(self):

        if self.error_calc_type == "CI":
            e = self.calculate_ci_error(0)[0]
        # elif self.error_calc_type in (SEM, MSEM):
        #     e = (self.get_intercept_variance() ** 0.5) * self.n ** -0.5
        elif self.error_calc_type in (SE, MSE):
            e = self.get_intercept_variance() ** 0.5
        else:
            e = 0

        return e

    def get_intercept_variance(self):
        if self._intercept_variance is None:
            self.get_slope_variance()

        return self._intercept_variance

    def get_slope_variance(self):
        b = self._slope
        W = self._calculate_W(b)
        U, V = self._calculate_UV(W)

        sigbsq = 1 / sum(W * U**2)

        sigasq = sigbsq * sum(W * self.clean_xs**2) / sum(W)

        self._intercept_variance = sigasq
        return sigbsq

    def get_slope_error(self):
        return self.get_slope_variance() ** 0.5

    def get_x_intercept(self):
        xint = self._get_x_intercept()

        xerr = self.predict(xint)
        return ufloat(xint, std_dev(xerr))

    def _get_slope(self):
        return self._slope

    def _get_intercept(self):
        return self._intercept

    def _get_x_intercept(self):
        v = -self.intercept / self.slope
        return v

    # def _get_x_intercept_error(self):
    #     """
    #         this method for calculating the x intercept error is incorrect.
    #         the current solution is to swap xs and ys and calculate the y intercept error
    #     """
    #     # v = self.x_intercept
    #     # e = self.get_intercept_error() * v ** 0.5
    #
    #     e = 0
    #     return e

    def _get_mswd(self):
        if not self._slope:
            self.calculate()
        a = self.intercept
        b = self.slope
        x, y, sx, sy = self.clean_xs, self.clean_ys, self.clean_xserr, self.clean_yserr

        v = 0
        if len(sx) and len(sy):
            v = calculate_mswd2(
                x, y, sx, sy, a, b, corrcoeffs=self.calculate_correlation_coefficients()
            )
            self.valid_mswd = validate_mswd(v, len(x), k=2)

        return v

    def _calculate_W(self, b):
        sig_x = self.clean_xserr
        sig_y = self.clean_yserr

        var_x = sig_x**2
        var_y = sig_y**2
        r = self.calculate_correlation_coefficients()
        # print var_x.shape, var_y.shape, r.shape, b
        return (var_y + b**2 * var_x - 2 * b * r * sig_x * sig_y) ** -1

    def _calculate(self):
        b = 0
        cnt = 0
        b, a, cnt = self._calculate_slope_intercept(Inf, b, cnt)
        if cnt >= 500:
            print("regression did not converge")
            #             self.warning('regression did not converge')
        #         else:
        #             self.info('regression converged after {} iterations'.format(cnt))

        self._slope = b
        self._intercept = a

    def _calculate_slope_intercept(self, pb, b, cnt, total=500, tol=1e-10):
        """
        recursively calculate slope
        b=slope
        a=intercept
        """
        a = 0
        if abs(pb - b) < tol or cnt > total:
            W = self._calculate_W(b)
            XBar, YBar = self._calculate_xy_bar(W)
            a = YBar - b * XBar
            return b, a, cnt
        else:
            sig_x = self.clean_xserr
            sig_y = self.clean_yserr

            r = self.calculate_correlation_coefficients()

            var_x = sig_x**2
            var_y = sig_y**2

            W = self._calculate_W(b)
            U, V = self._calculate_UV(W)

            sumA = sum(W**2 * V * (U * var_y + b * V * var_x - r * V * sig_x * sig_y))
            sumB = sum(
                W**2 * U * (U * var_y + b * V * var_x - b * r * U * sig_x * sig_y)
            )
            try:
                nb = sumA / sumB
                b, a, cnt = self._calculate_slope_intercept(b, nb, cnt + 1)
            except ZeroDivisionError:
                pass

        return b, a, cnt

    def predict(self, x):
        m, b = self._slope, self._intercept
        return m * x + b


class NewYorkRegressor(YorkRegressor):
    """
    mahon 1996
    """

    def get_slope_variance(self):
        """
        adapted from https://github.com/LLNL/MahonFitting/blob/master/mahon.py
        Trappitsch et al. (2018)

        :return:
        """

        b = self._slope
        W = self._calculate_W(b)
        U, V = self._calculate_UV(W)

        sx = self.clean_xserr
        sy = self.clean_yserr

        var_x = sx**2
        var_y = sy**2

        r = self.calculate_correlation_coefficients()
        sxy = r * sx * sy

        aa = 2 * b * (U * V * var_x - U**2 * sxy)
        bb = U**2 * var_y - V**2 * var_x
        cc = W**3 * (sxy - b * var_x)

        da = b**2 * (U * V * var_x - U**2 * sxy)
        db = b * (U**2 * var_y - V**2 * var_x)
        dc = U * V * var_y - V**2 * sxy
        dd = da + db - dc

        # eq 19
        dthdb = sum(W**2 * (aa + bb)) + 4 * sum(cc * dd)

        xbar, _ = self._calculate_xy_bar(W)

        # now calculate sigasq and sigbsq
        wksum = sum(W)
        sigasq = 0.0
        sigbsq = 0.0

        x = b**2 * (V * var_x - 2 * U * sxy) + 2 * b * U * var_y - V * var_y
        xx = b**2 * U * var_x + 2 * V * sxy - 2 * b * V * var_x - U * var_y
        for i, wi in enumerate(W):
            var_xi = var_x[i]
            var_yi = var_y[i]
            sxyi = sxy[i]

            # calculate dell theta / dell xi and dell theta / dell yi
            dthdxi = 0.0
            dthdyi = 0.0
            ww = wi / wksum
            for j, wj in enumerate(W):
                # add to dthdxi and dthdyi
                a = wj**2.0 * (kron(i, j) - ww)
                dthdxi += a * x[j]
                # correct equation! not equal to equation 21 in Mahon (1996)
                dthdyi += a * xx[j]

            # now calculate dell a / dell xi and dell a / dell yi
            dadxi = -b * ww - xbar * dthdxi / dthdb
            dadyi = ww - xbar * dthdyi / dthdb

            # now finally add to sigasq and sigbsq
            sigbsq += (
                dthdxi**2.0 * var_xi
                + dthdyi**2.0 * var_yi
                + 2 * sxyi * dthdxi * dthdyi
            )
            sigasq += (
                dadxi**2.0 * var_xi + dadyi**2.0 * var_yi + 2 * sxyi * dadxi * dadyi
            )

        # now divide sigbsq
        sigbsq /= dthdb**2.0
        self._intercept_variance = sigasq
        return sigbsq

        # # this seems to be the issue. application of the kronecker delta not correct
        #
        # # kronecker delta i.e int(i==j)
        # kd = identity(W.shape[0])
        # sW = sum(W)
        #
        # ee = W ** 2 * (kd - W / sW)
        #
        # # eq 20
        # dVdx = sum(ee * (b ** 2 * (V * var_x - 2 * U * sxy) + \
        #                  2 * b * U * var_y - V * var_y))
        #
        # # eq 21
        # dVdy = sum(ee * (b ** 2 * (U * var_x + 2 * V * sxy) - \
        #                  2 * b * V * var_x - U * var_y))
        #
        # # eq 18
        # a = sum(dVdx ** 2 * var_x + dVdy ** 2 * var_y + 2 * sxy * dVdx * dVdy)
        # try:
        #     var_b = a / dVdb ** 2
        # except ZeroDivisionError:
        #     var_b = 1
        #
        # xm, _ = self._calculate_xy_bar(W)
        #
        # dadx = -b * W / sW - xm * dVdx / dVdb
        # dady = W / sW - xm * dVdy / dVdb
        #
        # # eq 18
        # var_a = sum(dadx ** 2 * var_x + dady ** 2 * var_y + 2 * sxy * dadx * dady)
        #
        # self._intercept_variance = var_a
        # return var_b


class ReedYorkRegressor(YorkRegressor):
    """
    reed 1989
    """

    _degree = 1

    #     def _set_degree(self, d):
    #         '''
    #             York regressor only for linear fit
    #         '''
    #         self._degree = 2
    def _get_weights(self):
        wx = self.clean_xserr**-2
        wy = self.clean_yserr**-2

        return wx, wy

    def _calculate(self):
        if self.coefficients is None:
            return

        Wx, Wy = self._get_weights()

        def f(mi):
            W = self._calculate_W(mi, Wx, Wy)
            U, V = self._calculate_UV(W)

            suma = sum((W**2 * U * V) / Wx)
            S = sum((W**2 * U**2) / Wx)

            a = (2 * suma) / (3 * S)

            sumB = sum((W**2 * V**2) / Wx)
            B = (sumB - sum(W * U**2)) / (3 * S)

            g = -sum(W * U * V) / S

            ff = pow(mi, 3) - 3 * a * pow(mi, 2) + 3 * B * mi - g
            return ff

        m = self.coefficients[-1]
        roots = fsolve(f, (m,))
        slope = roots[0]

        self._slope = slope

        W = self._calculate_W(slope, Wx, Wy)
        x_bar, y_bar = self._calculate_xy_bar(W)
        self._intercept = y_bar - slope * x_bar

    def _calculate_W(self, slope, Wx, Wy):
        W = Wx * Wy / (slope**2 * Wy + Wx)
        return W

    def get_intercept_variance(self):
        var_slope = self.get_slope_variance()
        xs = self.clean_xs
        wx, wy = self._get_weights()
        w = self._calculate_W(self._slope, wx, wy)
        return var_slope * sum(w * xs**2) / sum(w)

    def get_slope_variance(self):
        n = len(self.clean_xs)

        Wx, Wy = self._get_weights()
        slope = self._slope
        W = self._calculate_W(slope, Wx, Wy)
        U, V = self._calculate_UV(W)

        # this is not the correct algo for the Read method
        # this is the York 1966 equations which Reed 1992 says are erroneous
        # Reed 1992 Linear least‐squares fits with errors in both coordinates. II: Comments on parameter variances
        sumA = sum(W * (slope * U - V) ** 2)
        sumB = sum(W * U**2)
        try:
            var = 1 / float(n - 2) * sumA / sumB
        except ZeroDivisionError:
            var = 0

        return var

    def predict(self, x, *args, **kw):
        """
        a=Y-bX

        a=y-intercept
        b=slope

        """
        slope, intercept = self.get_slope(), self.get_intercept()
        return slope * x + intercept


if __name__ == "__main__":
    from numpy import ones, array, polyval
    from pylab import plot, show

    xs = [
        0.89,
        1.0,
        0.92,
        0.87,
        0.9,
        0.86,
        1.08,
        0.86,
        1.25,
        1.01,
        0.86,
        0.85,
        0.88,
        0.84,
        0.79,
        0.88,
        0.70,
        0.81,
        0.88,
        0.92,
        0.92,
        1.01,
        0.88,
        0.92,
        0.96,
        0.85,
        1.04,
    ]
    ys = [
        0.67,
        0.64,
        0.76,
        0.61,
        0.74,
        0.61,
        0.77,
        0.61,
        0.99,
        0.77,
        0.73,
        0.64,
        0.62,
        0.63,
        0.57,
        0.66,
        0.53,
        0.46,
        0.79,
        0.77,
        0.7,
        0.88,
        0.62,
        0.80,
        0.74,
        0.64,
        0.93,
    ]
    exs = ones(27) * 0.01
    eys = ones(27) * 0.01

    xs = [0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
    ys = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
    wxs = array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1])
    wys = array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500])
    exs = 1 / wxs**0.5
    eys = 1 / wys**0.5

    plot(xs, ys, "o")

    reg = NewYorkRegressor(ys=ys, xs=xs, xserr=exs, yserr=eys)

    m, b = reg.get_slope(), reg.get_intercept()
    xs = linspace(0, 8)
    plot(xs, polyval((m, b), xs))
    show()
# ============= EOF =============================================
