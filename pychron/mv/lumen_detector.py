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

# ============= enthought library imports =======================
# ============= standard library imports ========================
from __future__ import absolute_import
from chaco.data_range_1d import DataRange1D
from chaco.default_colormaps import hot
from numpy import invert, zeros_like, asarray, max, copy, ones_like, zeros, uint8, average, ravel_multi_index
from skimage.color import rgb2gray, gray2rgb
from skimage.draw import circle, polygon
# ============= local library imports  ==========================
from skimage.feature import peak_local_max
from skimage.filters import gaussian

from pychron.mv.locator import Locator


def calc_area(a):
    b = asarray(a, dtype=bool)
    return b.sum()


class LumenDetector(Locator):
    threshold = 25
    pxpermm = 23

    mask_kind = 'Hole'
    beam_radius = 0
    custom_mask_radius = 0
    hole_radius = 0
    _cached_mask_value = None
    grain_measuring = False
    active_targets = None

    def __init__(self, *args, **kw):
        super(LumenDetector, self).__init__(*args, **kw)
        self._color_mapper = hot(DataRange1D(low=0, high=1))

    def get_value(self, src, threshold=10, area_threshold=10):
        """

        if scaled is True
        return sum of all pixels in masked area / (masked area *255)

        @param src:
        @param scaled:
        @return:
        """
        pixel_depth = self.pixel_depth

        self._mask(src)

        if not len(src.shape) == 2:
            gsrc = rgb2gray(src)
            tt = threshold / pixel_depth
            pd = 1
        else:
            gsrc = src
            tt = threshold / 100*pixel_depth
            pd = pixel_depth

        tsrc = gsrc[gsrc > tt]

        n = tsrc.shape[0]
        v = 0
        if n:
            v = tsrc.sum() / (n*pd)

        src[src <= threshold] = 0
        return src, v

    def find_targets(self, image, src, dim, mask=False, search=None):
        targets = self._find_targets(image, src, dim,
                                     filter_targets=False,
                                     inverted=True,
                                     convexity_filter=0.75,
                                     mask=mask, search=search)
        self.active_targets = None
        if targets:
            targets = self._filter(targets, self._target_near_center, src)
            if targets:
                self.active_targets = targets
                if image is not None:
                    self._draw_targets(image.source_frame, targets, dim)
                return targets

    def find_lum_peak(self, lum, dim, mask_dim, min_distance=5, blur=1):
        pixel_depth = self.pixel_depth

        if self.grain_measuring:
            targets = self.active_targets
            if targets is not None:
                self.debug('active targets={}'.format(len(targets)))
            else:
                self.debug('no active targets')
        else:
            targets = self.find_targets(None, lum, dim, mask=mask_dim, search={'n': 2})
            if targets:
                self.debug('found targets={}'.format(len(targets)))

        src = gaussian(lum, blur) * pixel_depth
        mask = self._mask(lum)

        h, w = lum.shape[:2]

        pts = peak_local_max(src, min_distance=min_distance, num_peaks=10)

        pt, px, py = None, None, None
        peak_img = zeros((h, w), dtype=uint8)

        if targets:
            target = targets[0]
            px, py = target.centroid
            pt = px - w / 2, py - h / 2, 1
            area = target.area
            self._draw_targets(src, targets, dim)
        else:
            area = mask.sum()

        if pts.shape[0]:
            idx = tuple(pts.T)
            intensities = src.flat[ravel_multi_index(idx, src.shape)]

            try:
                x, y = average(pts, axis=0, weights=intensities)
                if pt is None:
                    pt = x - w / 2, y - h / 2, sorted(intensities)[-1]
                    px, py = x, y

                peak_img[circle(y, x, min_distance)] = 255

            except ZeroDivisionError:
                pass

        sat = lum.sum() / (area * pixel_depth)
        return pt, px, py, peak_img, sat, src

    def get_scores(self, lum, pixel_depth=None):
        if pixel_depth is None:
            pixel_depth = self.pixel_depth

        mask = self._mask(lum)
        v = lum.sum()
        # x, y = peak_local_max(lum, min_distance=5, num_peaks=1)[0]

        # h, w = lum.shape[:2]
        # distance = ((x - w / 2.) ** 2 + (y - h / 2.) ** 2) ** 0.5
        distance = 1
        try:
            score_density = v / (calc_area(lum) * distance)
        except ZeroDivisionError:
            score_density = 0

        score_saturation = v / (mask.sum() * pixel_depth)

        return score_density, score_saturation, lum

    def _mask(self, src, radius=None):
        if radius is None:
            radius = self.mask_radius

        return super(LumenDetector, self)._mask(src, radius)

    @property
    def mask_radius(self):
        if self.mask_kind == 'Hole':
            d = self.hole_radius
        elif self.mask_kind == 'Beam':
            d = max(0.1, self.beam_radius * 1.1)
        else:
            d = self.custom_mask_radius

        return d

# ============= EOF =============================================
#
# def _lum(self, src):
#     # threshold = self.threshold
#     # src[src < threshold] = 0
#     mask = self._mask(src)
#
#     return mask
# def polygon_clip(rp, cp, r0, c0, r1, c1):
#     """Clip a polygon to the given bounding box.
#     Parameters
#     ----------
#     rp, cp : (N,) ndarray of double
#         Row and column coordinates of the polygon.
#     (r0, c0), (r1, c1) : double
#         Top-left and bottom-right coordinates of the bounding box.
#     Returns
#     -------
#     r_clipped, c_clipped : (M,) ndarray of double
#         Coordinates of clipped polygon.
#     Notes
#     -----
#     This makes use of Sutherland-Hodgman clipping as implemented in
#     AGG 2.4 and exposed in Matplotlib.
#     """
#     poly = path.Path(vstack((rp, cp)).T, closed=True)
#     clip_rect = transforms.Bbox([[r0, c0], [r1, c1]])
#     poly_clipped = poly.clip_to_bbox(clip_rect).to_polygons()[0]
#
#     # This should be fixed in matplotlib >1.5
#     if all(poly_clipped[-1] == poly_clipped[-2]):
#         poly_clipped = poly_clipped[:-1]
#
#     return poly_clipped[:, 0], poly_clipped[:, 1]
#
# #
# def polygon_perimeter(cr, cc, shape=None, clip=False):
#     """Generate polygon perimeter coordinates.
#     Parameters
#     ----------
#     cr : (N,) ndarray
#         Row (Y) coordinates of vertices of polygon.
#     cc : (N,) ndarray
#         Column (X) coordinates of vertices of polygon.
#     shape : tuple, optional
#         Image shape which is used to determine maximum extents of output pixel
#         coordinates. This is useful for polygons which exceed the image size.
#         By default the full extents of the polygon are used.
#     clip : bool, optional
#         Whether to clip the polygon to the provided shape.  If this is set
#         to True, the drawn figure will always be a closed polygon with all
#         edges visible.
#     Returns
#     -------
#     pr, pc : ndarray of int
#         Pixel coordinates of polygon.
#         May be used to directly index into an array, e.g.
#         ``img[pr, pc] = 1``.
#     """
#
#     if clip:
#         if shape is None:
#             raise ValueError("Must specify clipping shape")
#         clip_box = array([0, 0, shape[0] - 1, shape[1] - 1])
#     else:
#         clip_box = array([min(cr), min(cc),
#                           max(cr), max(cc)])
#
#     # Do the clipping irrespective of whether clip is set.  This
#     # ensures that the returned polygon is closed and is an array.
#     cr, cc = polygon_clip(cr, cc, *clip_box)
#
#     cr = round(cr).astype(int)
#     cc = round(cc).astype(int)
#
#     # Construct line segments
#     pr, pc = [], []
#     for i in range(len(cr) - 1):
#         line_r, line_c = line(cr[i], cc[i], cr[i + 1], cc[i + 1])
#         pr.extend(line_r)
#         pc.extend(line_c)
#
#     pr = asarray(pr)
#     pc = asarray(pc)
#
#     if shape is None:
#         return pr, pc
#     else:
#         return _coords_inside_image(pr, pc, shape)

#
# class PolygonLocator:
#     # def segment(self, src):
#     #     markers = threshold_adaptive(src, 10)
#     #     # n = markers[:].astype('uint8')
#     #     # n = markers.astype('uint8')
#     #     # n[markers] = 255
#     #     # n[not markers] = 1
#     #     # markers = n
#     #
#     #     # elmap = sobel(image, mask=image)
#     #     elmap = canny(src, sigma=1)
#     #     wsrc = watershed(elmap, markers, mask=src)
#     #
#     #     return invert(wsrc)
#     block_size = 20
#
#     # def _preprocess(self, src):
#     #     markers = threshold_adaptive(src, self.block_size)
#     #
#     #     # n = markers[:].astype('uint8')
#     #     n = markers.astype('uint8')
#     #     n[markers] = 255
#     #     n[invert(markers)] = 1
#     #     markers = n
#     #
#     #     # elmap = sobel(image, mask=image)
#     #     elmap = canny(src, sigma=1)
#     #     wsrc = watershed(elmap, markers, mask=src)
#     #     return invert(wsrc)
#     #
#     # def find_targets(self, src):
#     #     frm = grayspace(src) * 255
#     #     src = frm.astype('uint8')
#     #
#     #     src = self._preprocess(src)
#     #
#     #     # for i, contour in enumerate(find_contours(src, 0)):
#     #     #     coords = approximate_polygon(contour, tolerance=0)
#     #     #     x, y = coords.T
#     #     #     # print i, x,y
#     #     #     # rr, cc = polygon_perimeter(y, x)
#     #     #     rr, cc = polygon(y, x)
#     #     #
#     #     #     src[cc, rr] = 100
#     #
#     #     print 'found contours'
#     #     lsrc = label(src)
#     #     r, c = src.shape
#     #     ts = []
#     #     for i, rp in enumerate(regionprops(lsrc)):
#     #         cy, cx = rp.centroid
#     #         print 'region prop', i, cx, cy
#     #         # cy += 1
#     #         # cx += 1
#     #         tx, ty = cx - c / 2., cy - r / 2.
#     #         src[cy, cx] = 175
#     #         t = int(tx), int(ty)
#     #         if t not in ts:
#     #             ts.append((rp, t))
#     #     return ts, src
#
#     def find_best_target(self, osrc):
#         targetxy = None
#         ts, src = self.find_targets(osrc)
#         if ts:
#             scores = []
#             if len(ts) > 1:
#                 for rp, center in ts:
#                     score = self.calculate_target_score(osrc, rp)
#                     scores.append((score, center))
#
#                 targetxy = sorted(scores)[-1][1]
#             else:
#                 targetxy = ts[0][1]
#
#         return targetxy, src
#
#     def calculate_target_score(self, src, rp):
#         rr, cc = rp.coords.T
#         region = src[rr, cc]
#         score = region.sum() / float(rp.area)
#         return score
# def find_best_target(self, src):

#     p = PolygonLocator()
#     targetxy, src = p.find_best_target(src)
#
#     return targetxy, src
#
# def lum(self, src):
#     lum, mask = self._lum(src)
#     return lum, mask
#
# def get_value(self, src, scaled=True):
#     """
#
#     if scaled is True
#     return sum of all pixels in masked area / (masked area *255)
#
#     @param src:
#     @param scaled:
#     @return:
#     """
#
#     lum, mask = self._lum(src)
#
#     v = lum.sum()
#
#     if scaled:
#         v /= (mask.sum() * 255.)
#     # print lum.sum(), v
#     return src, v
#
