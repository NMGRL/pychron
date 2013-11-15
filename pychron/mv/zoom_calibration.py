#===============================================================================
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
#===============================================================================
from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = 'qt4'

import math
from skimage.filter.edges import sobel, vsobel
from pychron.regression.least_squares_regressor import LeastSquaresRegressor


# from numpy.lib.function_base import histogram
import os
import time
from pychron.ui.thread import Thread
from pychron.ui.gui import invoke_in_main_thread

from skimage.transform.hough_transform import probabilistic_hough, hough_line, \
    hough_peaks

from pychron.graph.graph import Graph

from numpy import array, diff, unique, argmax, bincount, ma, histogram, \
    zeros_like, polyfit, polyval, linspace, max, mean, std, exp
from pychron.image.image import Image
from pychron.image.cv_wrapper import load_image, draw_circle, grayspace, colorspace, \
    crop
from chaco.image_data import ImageData
from skimage import filter
from skimage.draw import line
# from skimage.segmentation._clear_border import clear_border
# from skimage.feature.corner import corner_harris, corner_peaks, corner_subpix
#============= enthought library imports =======================
from traits.api import HasTraits, Instance, Button, Range, on_trait_change
from traitsui.api import View, Item, UItem, HGroup
from pychron.mv.test_image import TestImage

#============= standard library imports ========================
#============= local library imports  ==========================

class ZoomCalibration(HasTraits):
    test_image = Instance(TestImage, ())
    test_button = Button
    threshold_low = Range(0, 100, 10)
    threshold_high = Range(0, 100, 50)


    def open_image(self):
        print
    def traits_view(self):
        v = View(
                 Item('test_button'),
#                 HGroup('threshold_low', 'threshold_high', show_labels=False),
                 UItem('test_image', style='custom'),
                 resizable=True,
                 width=1200,
                 height=600
                 )
        return v
#
#     def _threshold_low_changed(self):
#         if self.test_image.plotdata:
#             self._refresh()
#
#     def _threshold_high_changed(self):
#         if self.test_image.plotdata:
#             self._refresh()

    def _calculate_spacing(self, im):
        h, w, d = im.shape
#         cw, ch = 600, 600
        cw, ch = 300, 300
        cx = (w - cw) / 2
        cy = (h - ch) / 2
        im = crop(im, cx, cy, cw, ch)
#         d = self.test_image.plotdata.get_data('imagedata000')
        d = grayspace(im)
#         d /= 255.
#         edges = filter.canny(d, sigma=3,
# #                              low_threshold=0,
# #                              high_threshold=
#                              )
#         edges = edges.astype('uint8')
#         edges = vsobel(d)
        edges = sobel(d)

        nim = zeros_like(edges)
        nim[edges > 0.1] = 255
        edges = nim
        self.test_image.set_image(edges)


        hspace, angles, dists = hough_line(edges)

        self.test_image.set_image(hspace, 1)

        _hspace, angles, dists = hough_peaks(hspace, angles, dists,

                                             )
        nim = zeros_like(edges)
        h, w, d = im.shape
        xs = []

        for ti, di in zip(angles, dists):
            ai = math.degrees(ti) + 180
            di = abs(int(round(di)))
            aa = abs(ai - 90) < 1
            bb = abs(ai - 270) < 1
            if aa or bb :
                adi = abs(di)
                coords = line(0, adi, h - 1, adi)
                nim[coords] = 200
                xs.append(di)

        self.test_image.set_image(nim, 2)
        xs.sort()
        # compute difference between each pair
        dxs = diff(xs)
        print dxs
        dd = sorted(dxs)[1:]
        print dd
        while len(dd):
            if std(dd) < 3:
                print dd
                return mean(dd) * 4  # each bar =0.25mm
            else:
                dd = dd[:-1]


    def _test_button_fired(self):
        self._test1()

    def _test2(self):
        self.test_image.setup_images(3,
#                                     (475, 613)
                                    (640, 480)
                                     )

        root = '/Users/ross/Pychrondata_demo/data/snapshots/scan6'
        p = os.path.join(root, '008.jpg')
        im = load_image(p)
        im = grayspace(im)
        self.test_image.set_image(im)

        nim = zeros_like(im)
        nim[((im > 100) & (im < 200))] = 255
        self.test_image.set_image(nim, 1)


    def _test1(self):
        self.test_image.setup_images(3,
#                                     (475, 613)
                                    (640, 480)
                                     )

        t = Thread(target=self._test)
        t.start()
        self._t = t

    def _test(self):

        p = '/Users/ross/Pychrondata_demo/data/snapshots/scan6/007.jpg'
        g = Graph()
        g.new_plot()


        for scan_i, z, idxs in [
#                    1,
#                     2,
#                     3, 4, 5,
#                     (6, [20, 30, 40, 50, 60, 70, 80, 90, 100, ],
#                         [2, 3, 4, 5, 6, 7, 8, 9, 10]
#                      ),
                    (6, [10],
                        [1]
                     ),
#                     (6, [100, 90, 80, 70, 60, 50, 40, 30, 20],
#                         [11, 12, 13, 14, 15, 16, 17, 18, 19]
#                     )

                   ]:
            dxs = []
            zs = []
            root = '/Users/ross/Pychrondata_demo/data/snapshots/scan{}'.format(scan_i)
            for  zi, idx in zip(z, idxs):
                pn = os.path.join(root, '{:03n}.jpg'.format(idx))
                d = load_image(pn)

                dx = self._calculate_spacing(d)
                dxs.append(dx)

                zs.append(zi)

            g.new_series(zs, dxs, type='scatter')

            coeffs = polyfit(zs, dxs, 2)
            print 'parabolic intercept {}'.format(coeffs[-1])

            xs = linspace(0, max(zs))
            ys = polyval(coeffs, xs)
            g.new_series(xs, ys)

            fitfunc = lambda p, x: p[0] * exp(p[1] * x) + p[2]
            lr = LeastSquaresRegressor(fitfunc=fitfunc,
                                       initial_guess=[1, 0.1, 0],
                                       xs=zs,
                                       ys=dxs
                                       )
            xs = linspace(0, max(zs))
            ys = lr.predict(xs)
            print 'exponential intercept {}'.format(lr.predict(0))
            g.new_series(xs, ys)

        invoke_in_main_thread(g.edit_traits)


if __name__ == '__main__':
    z = ZoomCalibration()
    z.configure_traits()
#============= EOF =============================================
