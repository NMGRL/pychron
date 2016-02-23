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
from matplotlib import path, transforms
from numpy import invert, zeros_like, asarray, round, min, max, array, vstack, all, copy
from skimage.draw import circle

# ============= local library imports  ==========================
from skimage.draw._draw import line, _coords_inside_image
from skimage.measure import find_contours, approximate_polygon, regionprops, label


def area(a):
    b = asarray(a, dtype=bool)
    return b.sum()


def polygon_clip(rp, cp, r0, c0, r1, c1):
    """Clip a polygon to the given bounding box.
    Parameters
    ----------
    rp, cp : (N,) ndarray of double
        Row and column coordinates of the polygon.
    (r0, c0), (r1, c1) : double
        Top-left and bottom-right coordinates of the bounding box.
    Returns
    -------
    r_clipped, c_clipped : (M,) ndarray of double
        Coordinates of clipped polygon.
    Notes
    -----
    This makes use of Sutherland-Hodgman clipping as implemented in
    AGG 2.4 and exposed in Matplotlib.
    """
    poly = path.Path(vstack((rp, cp)).T, closed=True)
    clip_rect = transforms.Bbox([[r0, c0], [r1, c1]])
    poly_clipped = poly.clip_to_bbox(clip_rect).to_polygons()[0]

    # This should be fixed in matplotlib >1.5
    if all(poly_clipped[-1] == poly_clipped[-2]):
        poly_clipped = poly_clipped[:-1]

    return poly_clipped[:, 0], poly_clipped[:, 1]


def polygon_perimeter(cr, cc, shape=None, clip=False):
    """Generate polygon perimeter coordinates.
    Parameters
    ----------
    cr : (N,) ndarray
        Row (Y) coordinates of vertices of polygon.
    cc : (N,) ndarray
        Column (X) coordinates of vertices of polygon.
    shape : tuple, optional
        Image shape which is used to determine maximum extents of output pixel
        coordinates. This is useful for polygons which exceed the image size.
        By default the full extents of the polygon are used.
    clip : bool, optional
        Whether to clip the polygon to the provided shape.  If this is set
        to True, the drawn figure will always be a closed polygon with all
        edges visible.
    Returns
    -------
    pr, pc : ndarray of int
        Pixel coordinates of polygon.
        May be used to directly index into an array, e.g.
        ``img[pr, pc] = 1``.
    """

    if clip:
        if shape is None:
            raise ValueError("Must specify clipping shape")
        clip_box = array([0, 0, shape[0] - 1, shape[1] - 1])
    else:
        clip_box = array([min(cr), min(cc),
                          max(cr), max(cc)])

    # Do the clipping irrespective of whether clip is set.  This
    # ensures that the returned polygon is closed and is an array.
    cr, cc = polygon_clip(cr, cc, *clip_box)

    cr = round(cr).astype(int)
    cc = round(cc).astype(int)

    # Construct line segments
    pr, pc = [], []
    for i in range(len(cr) - 1):
        line_r, line_c = line(cr[i], cc[i], cr[i + 1], cc[i + 1])
        pr.extend(line_r)
        pc.extend(line_c)

    pr = asarray(pr)
    pc = asarray(pc)

    if shape is None:
        return pr, pc
    else:
        return _coords_inside_image(pr, pc, shape)


class PolygonLocator:
    # def segment(self, src):
    #     markers = threshold_adaptive(src, 10)
    #     # n = markers[:].astype('uint8')
    #     # n = markers.astype('uint8')
    #     # n[markers] = 255
    #     # n[not markers] = 1
    #     # markers = n
    #
    #     # elmap = sobel(image, mask=image)
    #     elmap = canny(src, sigma=1)
    #     wsrc = watershed(elmap, markers, mask=src)
    #
    #     return invert(wsrc)

    def find_targets(self, src):
        src = copy(src)
        for contour in find_contours(src, 0):
            coords = approximate_polygon(contour, tolerance=0)
            x, y = coords.T
            rr, cc = polygon_perimeter(y, x)
            src[cc, rr] = 100

        lsrc = label(src)
        r, c = src.shape
        ts = []
        for rp in regionprops(lsrc):
            cy, cx = rp.centroid
            cy += 1
            cx += 1
            tx, ty = cx - c / 2., cy - r / 2.
            src[cy, cx] = 175
            t = int(tx), int(ty)
            if t not in ts:
                ts.append((rp, t))
        return ts, src

    def find_best_target(self, osrc):
        targetxy = None
        ts, src = self.find_targets(osrc)
        if ts:
            scores = []
            if len(ts) > 1:
                for rp, center in ts:
                    score = self.calculate_target_score(osrc, rp)
                    scores.append((score, center))

                targetxy = sorted(scores)[-1][1]
            else:
                targetxy = ts[0][1]

        return targetxy, src

    def calculate_target_score(self, src, rp):
        rr, cc = rp.coords.T
        region = src[rr, cc]
        score = region.sum() / float(rp.area)
        return score


class LumenDetector(object):
    threshold = 25
    pxpermm = 23

    mask_kind = 'Hole'
    beam_radius = 0
    custom_mask_radius = 0
    hole_radius = 0

    def find_target(self, src):
        p = PolygonLocator()
        targetxy, src = p.find_target(src)

        return targetxy, src

    def find_best_target(self, src):
        p = PolygonLocator()
        targetxy, src = p.find_best_target(src)

        return targetxy, src

    def get_value(self, src, scaled=True):
        """

        if scaled is True
        return sum of all pixels in masked area / (masked area *255)

        @param src:
        @param scaled:
        @return:
        """

        lum, mask = self._lum(src)

        v = lum.sum()

        if scaled:
            v /= (mask.sum() * 255.)
        # print lum.sum(), v
        return src, v

    def get_scores(self, src):
        lum, mask = self._lum(src)
        v = lum.sum()
        try:
            score_density = v / area(lum)
        except ZeroDivisionError:
            score_density = 0

        score_saturation = v / (mask.sum() * 255.)

        return score_density, score_saturation, lum

    def _lum(self, src):
        mask = self._mask(src)
        self._preprocess(src)

        return src[mask], mask

    def _mask(self, src):
        radius = self.mask_radius

        h, w = src.shape[:2]
        c = circle(h / 2., w / 2., radius)
        mask = zeros_like(src, dtype=bool)
        mask[c] = True
        src[invert(mask)] = 0
        return mask

    def _preprocess(self, src):
        threshold = self.threshold
        src[src < threshold] = 0

    @property
    def mask_radius(self):
        if self.mask_kind == 'Hole':
            d = self.hole_radius
        elif self.mask_kind == 'Beam':
            d = max(0.1, self.beam_radius * 1.1)
        else:
            d = self.custom_mask_radius

        return d * self.pxpermm

# ============= EOF =============================================
