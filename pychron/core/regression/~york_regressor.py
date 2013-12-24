# #===============================================================================
# # Copyright 2012 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# #===============================================================================
# from traits.etsconfig.etsconfig import ETSConfig
# ETSConfig.toolkit = 'qt4'
# #============= enthought library imports =======================
# from numpy import linspace, apply_along_axis, sign, roll, \
#      where, Inf, vectorize, zeros, ones_like
# from scipy.optimize import fsolve
# #============= standard library imports ========================
# #============= local library imports  ==========================
# from pychron.core.regression.ols_regressor import OLSRegressor
#
# class YorkRegressor(OLSRegressor):
#     _degree = 1
# #     def _set_degree(self, d):
# #         '''
# #             York regressor only for linear fit
# #         '''
# #         self._degree = 2
#
#     def _compute_args(self, mi, Wx, Wy):
#
#         W = Wx * Wy / (pow(mi, 2) * Wy + Wx)
#         sW = sum(W)
#         x_bar = sum(W * self.xs) / sW
#         y_bar = sum(W * self.ys) / sW
#         return W, x_bar, y_bar
#
#     def predict(self, *args, **pw):
#         _slope, intercept = self._predict()
#         return intercept
#
#     def _predict(self, *args, **kw):
#         '''
#
#             YorkRegressor always returns predicted intercept
#             i.e x=0
#
#             based on
#              "Linear least-squares fits with errors in both coordinates",
#              Am. J. Phys 57 #7 p. 642 (1989) by B.C. Reed
#         '''
#         xs = self.xs
#         ys = self.ys
#         Wx = 1 / self.xserr ** 2
#         Wy = 1 / self.yserr ** 2
#
#         def _f(mi):
#             W, _x_, _y_ = self._compute_args(mi, Wx, Wy)
#             U = xs - _x_
#             V = ys - _y_
#
#             suma = sum((W ** 2 * U * V) / Wx)
#             S = sum((W ** 2 * U ** 2) / Wx)
#
#             a = (2 * suma) / (3 * S)
#
#             sumB = sum((W ** 2 * V ** 2) / Wx)
#             B = (sumB - sum(W * U ** 2)) / (3 * S)
#
#             g = -sum(W * U * V) / S
#
#             ff = pow(mi, 3) - 3 * a * pow(mi, 2) + 3 * B * mi - g
#             return ff
#
#         m = self.coefficients[-1]
#         # find root (slope) that is closest to the nominal linear regression slope
#         roots = fsolve(_f, (m,))
#         b = roots[0]
#
#         W, _x_, _y_ = self._compute_args(b, Wx, Wy)
#         a = _y_ - b * _x_
# #         from pylab import plot, show
# #         ms = linspace(-1, 1)
# #         plot(ms, vectorize(_f)(ms))
# #         show()
#
#         print sum(W * (ys - a - b * xs) ** 2) / (len(xs) - 2)
#
#         return b, a
#
#     def predict_error(self, slope=None):
#         '''
#             YorkRegressor always returns predicted intercept error
#             i.e x=0
#         '''
#         if slope is None:
#             slope, intercept = self._predict()
#
#         xs = self.xs
#         ys = self.ys
#
#         n = len(xs)
#
#         Wx = 1 / self.xserr ** 2
#         Wy = 1 / self.yserr ** 2
#         W, X_bar, Y_bar = self._compute_args(slope, Wx, Wy)
#         U = xs - X_bar
#         V = ys - Y_bar
# #         x = X_bar
# #         x_bar = sum(W * x) / sum(W)
# #         sigma_b = (1 / sum(W * U ** 2)) ** 0.5
# #         sigma_a = (1 / sum(W) + x_bar ** 2 * sigma_b ** 2) ** 0.5
# #         varm = sum(W * U * U)
#         sumA = sum(W * (slope * U - V) ** 2) / sum(W * U ** 2)
#         varm = sumA / float(n - 2)
# #         print varm ** 0.5
#         varc = (sum(W * xs ** 2) / sum(W)) * varm
#         return varm ** 0.5 , varc ** 0.5
# #         return sigma_a
#
# if __name__ == '__main__':
#     from numpy import ones, array
#     xs = [0.89, 1.0, 0.92, 0.87, 0.9, 0.86, 1.08, 0.86, 1.25,
#             1.01, 0.86, 0.85, 0.88, 0.84, 0.79, 0.88, 0.70, 0.81,
#             0.88, 0.92, 0.92, 1.01, 0.88, 0.92, 0.96, 0.85, 1.04
#             ]
#     ys = [0.67, 0.64, 0.76, 0.61, 0.74, 0.61, 0.77, 0.61, 0.99,
#           0.77, 0.73, 0.64, 0.62, 0.63, 0.57, 0.66, 0.53, 0.46,
#           0.79, 0.77, 0.7, 0.88, 0.62, 0.80, 0.74, 0.64, 0.93
#           ]
#     exs = ones(27) * 0.01
#     eys = ones(27) * 0.01
#
#     xs = [0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
#     ys = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
#     wxs = array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1])
#     wys = array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500])
#     exs = 1 / wxs ** 0.5
#     eys = 1 / wys ** 0.5
#
# #     plot(xs, ys, 'o')
#
#     reg = YorkRegressor(
#                              ys=ys,
#                              xs=xs,
#                              xserr=exs,
#                              yserr=eys
#                              )
#     reg.predict()
# #     show()
# #============= EOF =============================================
