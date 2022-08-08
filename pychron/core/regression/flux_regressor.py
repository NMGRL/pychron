# ===============================================================================
# Copyright 2013 Jake Ross
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

# ============= standard library imports ========================
from operator import itemgetter

from numpy import (
    asarray,
    column_stack,
    ones_like,
    array,
    average,
    ravel,
    zeros_like,
    sin,
    cos,
)

# ============= local library imports  ==========================
from scipy.interpolate import Rbf, bisplrep, bisplev, griddata
from statsmodels.regression.linear_model import WLS, OLS

# ============= enthought library imports =======================
from traits.api import Bool, Int, Enum

from pychron.core.geometry.geometry import calc_distances
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.core.regression.ols_regressor import MultipleLinearRegressor
from pychron.core.stats.idw import Invdisttree
from pychron.pychron_constants import WEIGHTED_MEAN, AVERAGE, LINEAR


class SpecialFluxRegressor(BaseRegressor):
    use_weighted_fit = Bool

    def predict(self, pts):
        return array(self._predict(pts))

    def predict_error(self, pts, error_calc=None):
        return array(self._predict(pts, return_error=True))

    def get_exog(self, x):
        return x

    def _calculate_coefficients(self):
        return ""

    def _calculate_coefficient_errors(self):
        return ""


class InterpolationRegressor(SpecialFluxRegressor):
    def predict(self, pts):
        return self.predict_grid(*pts.T)

    def fast_predict2(self, endog, exog):
        pass

    def predict_grid(self, pts):
        return zeros_like(pts)

    def predict_error(self, pts, **kw):
        return zeros_like(pts)


class BSplineRegressor(InterpolationRegressor):
    def calculate(self):
        x, y = self.clean_xs.T

        z = self.clean_ys
        # self.rbf = Rbf(x, y, z)

        self._tck = bisplrep(x, y, z, kx=4, ky=4)

    def predict_grid(self, x, y):
        znew = bisplev(x, y, self._tck)
        return znew


class RBFRegressor(InterpolationRegressor):
    rbf_kind = "multiquadric"

    def calculate(self):
        x, y = self.clean_xs.T

        z = self.clean_ys
        self.rbf = Rbf(x, y, z, function=self.rbf_kind)

    def predict_grid(self, x, y):
        return self.rbf(x, y)

    def fast_predict2(self, endog, exog):
        x, y = exog.T
        # print(x.shape, y.shape, endog.shape)
        fx, fy = self.clean_xs.T
        self.rbf = Rbf(fx, fy, endog, function=self.rbf_kind)
        return self.rbf(x, y)


class GridDataRegressor(InterpolationRegressor):
    method = "cubic"

    def calculate(self):
        pass

    def predict_grid(self, x, y):
        z = griddata(self.clean_xs, self.clean_ys, (x, y), method=self.method)
        print("pasdf", z)
        return z
        # return griddata(self.clean_xs, self.clean_ys, (x, y), method=self.method)

    def fast_predict2(self, endog, exog):
        x, y = exog.T
        # print(x.shape, y.shape, endog.shape)
        # fx, fy = self.clean_xs.T
        # self.rbf = Rbf(fx, fy, endog, function=self.rbf_kind)
        # return self.rbf(x, y)
        return griddata(self.clean_xs, endog, (x, y), method=self.method)


class IDWRegressor(InterpolationRegressor):
    def calculate(self):
        leafsize = 10
        known = self.clean_xs
        z = self.clean_ys
        self._invdisttree = Invdisttree(known, z, leafsize=leafsize, stat=1)

    def predict(self, pts):
        nnear = 8  # 8 2d, 11 3d => 5 % chance one-sided -- Wendel, mathoverflow.com
        eps = 0.1  # approximate nearest, dist <= (1 + eps) * true nearest
        p = 2  # weights ~ 1 / distance**p
        return self._invdisttree(pts, nnear=nnear, eps=eps, p=p)


def linear_interp(xy, xs, js):
    x2 = ((xs[0][0] - xs[1][0]) ** 2 + (xs[0][1] - xs[1][1]) ** 2) ** 0.5
    x = ((xy[0] - xs[0][0]) ** 2 + (xy[1] - xs[0][1]) ** 2) ** 0.5
    j = js[0] + x * (js[1] - js[0]) / (x2)
    return j

    # return func(*vs)
    # return func(a.mean_j, b.mean_j), func(a.mean_jerr, b.mean_jerr)


class NearestNeighborFluxRegressor(SpecialFluxRegressor):
    n = Int(3)
    interpolation_style = Enum(WEIGHTED_MEAN, AVERAGE, LINEAR)

    def set_neighbors(self, unks, mons):
        for unk in unks:
            idx, ds = self._get_neighbors(unk.x, unk.y)
            unk.bracket_a = mons[idx[0]].hole_id
            unk.bracket_b = mons[idx[-1]].hole_id

    def _get_neighbors(self, x, y):
        v2 = array([[x, y]])
        ds = ravel(calc_distances(self.clean_xs, v2))
        idx = sorted(enumerate(ds), key=itemgetter(1))
        idx = sorted(idx[: self.n])
        idx, ds = zip(*idx)
        return idx, ds

    def _predict(self, pts, return_error=False):
        def pred(x, y):
            """
            get the n positions that are closest (eucledian distance) to x,y
            """

            idx, _ = self._get_neighbors(x, y)
            v = 0
            if idx:
                idx = array(idx)

                vs = self.clean_ys[idx]
                # if self.interpolation_style in (AVERAGE, WEIGHTED_MEAN):
                if self.interpolation_style == WEIGHTED_MEAN:
                    es = self.clean_yserr[idx]
                    ws = es**-2
                    if return_error:
                        v = ws.sum() ** -0.5
                    else:
                        v = average(vs, weights=ws)
                elif self.interpolation_style == AVERAGE:
                    if return_error:
                        v = vs.std()
                    else:
                        v = vs.mean()
                elif self.interpolation_style == LINEAR:
                    v = linear_interp(
                        (x, y),
                        self.clean_xs[idx],
                        self.clean_yserr[idx] if return_error else self.clean_ys[idx],
                    )
            return v

        ret = [pred(*pt) for pt in pts]
        return ret


# class BracketingFluxRegressor(SpecialFluxRegressor):
#
#     def _predict(self, pts, return_error=False):
#         def pred(x, y):
#             """
#             get points with same y value
#             :param p:
#             :return:
#             """
#             tol = 0.001
#
#             # idx = (i for i, p in enumerate(self.clean_xs) if ((x - p[0]) ** 2 + (y - p[1]) ** 2) ** 0.5 < tol)
#             # idx = (i for i, p in enumerate(self.clean_xs) if )
#             idx = [abs(y - p[1]) < tol for p in self.clean_xs]
#             v = 0
#             if idx:
#                 vs = self.clean_ys[idx]
#
#                 if self.use_weighted_fit:
#                     es = self.clean_yserr[idx]
#                     ws = es ** -2
#                     if return_error:
#                         v = ws.sum()
#                     else:
#                         v = average(vs, weights=ws)
#                 else:
#                     if return_error:
#                         v = vs.std()
#                     else:
#                         v = vs.mean()
#             return v
#
#         ret = [pred(*pt) for pt in pts]
#         return ret
#
#
# class MatchingFluxRegressor(BaseRegressor):
#     def predict(self, pts):
#         return self._predict(pts, self.clean_ys)
#
#     def predict_error(self, pts, error_calc=None):
#         # pts = pts[0]
#         return self._predict(pts, self.clean_yserr)
#
#     def _predict(self, pts, ret):
#         def matching(xx, yy):
#             for i, pt in enumerate(self.clean_xs):
#                 if ((xx - pt[0]) ** 2 + (yy - pt[1]) ** 2) ** 0.5 < 0.0001:
#                     return ret[i]
#             else:
#                 return 0
#
#         return array([matching(x, y) for x, y in pts])


class BowlFluxRegressor(MultipleLinearRegressor):
    def _get_X(self, xs=None):
        if xs is None:
            xs = self.xs
        xs = asarray(xs)
        x1, x2 = xs.T
        # cols =[pow(xi, i+1) for i in range(self.degree) for xi in xs.T]
        # cols.append(ones_like(x1))

        # return column_stack(cols)
        return column_stack(
            (
                # x1 ** 6,
                # x2 ** 6,
                # x1 ** 5,
                # x2 ** 5,
                # x1**4,
                # x2**4,
                # x1**3,
                # x2**3,
                x1**2,
                x2**2,
                x1,
                x2,
                ones_like(x1),
            )
        )
        # return column_stack((x1, x2, x1 ** 2, x2 ** 2, x1 * x2, x1**2*x2, x2**2*x1, ones_like(x1)))
        # return column_stack((x1**2, x2**2, x1, x2, ones_like(x1)))


class HighOrderPolynominalFluxRegressor(MultipleLinearRegressor):
    def _get_X(self, xs=None):
        if xs is None:
            xs = self.xs
        xs = asarray(xs)
        x1, x2 = xs.T
        cols = [xi ** (i + 1) for i in range(self.degree) for xi in xs.T]
        cols.append(ones_like(x1))
        cols = column_stack(cols)
        # print(cols)

        # column_stack(
        #     (
        #         # x1 ** 6,
        #         # x2 ** 6,
        #         # x1 ** 5,
        #         # x2 ** 5,
        #         x1**4,
        #         x2**4,
        #         x1**3,
        #         x2**3,
        #         x1**2,
        #         x2**2,
        #         x1,
        #         x2,
        #         ones_like(x1),
        #     )
        # )

        return cols
        # return column_stack(
        #     (
        #         # x1 ** 6,
        #         # x2 ** 6,
        #         # x1 ** 5,
        #         # x2 ** 5,
        #         # x1**4,
        #         # x2**4,
        #         # x1**3,
        #         # x2**3,
        #         x1**2,
        #         x2**2,
        #         x1,
        #         x2,
        #         ones_like(x1),
        #     )
        # )


class PlaneFluxRegressor(MultipleLinearRegressor):
    use_weighted_fit = Bool(False)

    def _get_weights(self):
        e = self.clean_yserr
        if self._check_integrity(e, e):
            return 1 / e**2

    def _engine_factory(self, fy, X, check_integrity=True):
        if self.use_weighted_fit:
            return WLS(fy, X, weights=self._get_weights())
        else:
            return OLS(fy, X)


# ============= EOF =============================================
