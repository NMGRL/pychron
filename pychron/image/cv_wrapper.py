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
from collections import namedtuple

from numpy import array, asarray, ndarray, zeros_like
from numpy.lib.function_base import percentile
from scipy.ndimage.filters import laplace

try:
    from cv2 import (
        VideoCapture,
        VideoWriter,
        imwrite,
        line,
        fillPoly,
        polylines,
        rectangle,
        imread,
        findContours,
        drawContours,
        arcLength,
        approxPolyDP,
        contourArea,
        isContourConvex,
        boundingRect,
        GaussianBlur,
        addWeighted,
        circle,
        moments,
        minAreaRect,
        minEnclosingCircle,
        convexHull,
    )

    from cv2 import RETR_EXTERNAL, CHAIN_APPROX_NONE, LINE_AA

    # from cv2 import ConvertImage, fromarray, LoadImage, Flip, \
    #     Resize, CreateImage, CvtColor, Scalar, CreateMat, Copy, GetSubRect, \
    #     PolyLine, Split, \
    #     Merge, Laplace, ConvertScaleAbs, GetSize
    # from cv2 import CV_CVTIMG_SWAP_RB, CV_8UC1, CV_BGR2GRAY, CV_GRAY2BGR, \
    #     CV_8UC3, CV_RGB, CV_16UC1, CV_32FC3, CV_CHAIN_APPROX_NONE, \
    #     CV_RETR_EXTERNAL, \
    #     CV_AA, CV_16UC3, CV_16SC1
except ImportError as e:
    print("exception", e)
    print("OpenCV required")

# ============= local library imports  ==========================
from pychron.core.geometry.centroid import calculate_centroid


def get_focus_measure(src, kind):
    if not isinstance(src, ndarray):
        src = asarray(src)

    dst = laplace(src.astype(float))
    d = dst.flatten()
    d = percentile(d, 99)
    return d.mean()


def crop(src, x, y, w, h):
    if not isinstance(src, ndarray):
        src = asarray(src)

    return src[y : y + h, x : x + w]


def save_image(src, path):
    if not isinstance(src, ndarray):
        src = asarray(src)

    imwrite(path, src)


def colorspace(src, cs=None):
    from skimage.color.colorconv import gray2rgb

    if not isinstance(src, ndarray):
        src = asarray(src)

    return gray2rgb(src)


def grayspace(src):
    from skimage.color.colorconv import rgb2gray, rgba2rgb
    if len(src.shape) == 3:
        if src.shape[2] == 4:
            src = rgba2rgb(src)
    dst = rgb2gray(src)
    return dst


#
#
# def resize(src, w, h, dst=None):
#     if isinstance(dst, tuple):
#         dst = CreateMat(*dst)
#
#     if isinstance(src, ndarray):
#         src = asMat(src)
#
#     if dst is None:
#         dst = CreateMat(int(h), int(w), src.type)
#
#     Resize(src, dst)
#     return dst

#
# def flip(src, mode):
#     Flip(src, src, mode)
#     return src


def get_size(src):
    if hasattr(src, "width"):
        return src.width, src.height
    else:
        h, w = src.shape[:2]
        return w, h


#
#
# def swap_rb(src):
#     try:
#         ConvertImage(src, src, CV_CVTIMG_SWAP_RB)
#     except TypeError:
#         src = fromarray(src)
#         ConvertImage(src, src, CV_CVTIMG_SWAP_RB)
#     return src
#
#
# _cv_swap_rb = swap_rb


# def asMat(arr):
#     return fromarray(arr)
#
#
# def load_image(p, swap_rb=False):
#     img = imread(p)
#     if swap_rb:
#         img = _cv_swap_rb(img)
#     return img


def get_capture_device():
    v = VideoCapture()
    return v


def new_video_writer(path, fps, size):
    fourcc = "MJPG"
    v = VideoWriter(path, fourcc, fps, size)
    return v


# ===============================================================================
# image manipulation
# ===============================================================================
def sharpen(src):
    src = asarray(src)
    im = GaussianBlur(src, (3, 3), 3)
    addWeighted(src, 1.5, im, -0.5, 0, im)
    return im


# ===============================================================================
# drawing
# ===============================================================================
_new_point = namedtuple("Point", "x y")


def new_point(x, y, tt=False):
    x, y = int(x), int(y)
    if tt:
        return x, y
    else:
        return _new_point(x, y)


def convert_color(color):
    # if isinstance(color, tuple):
    #     color = RGB(*color)
    # else:
    #     color = Scalar(color)
    return color


def draw_circle(src, center, radius, color=(255.0, 0, 0), thickness=1):
    if isinstance(center, tuple):
        center = new_point(*center)
    circle(
        src,
        center,
        int(radius),
        convert_color(color),
        thickness=thickness,
        lineType=LINE_AA,
    )


def draw_lines(src, lines, color=(255, 0, 0), thickness=3):
    if lines:
        for p1, p2 in lines:
            p1 = new_point(*p1)
            p2 = new_point(*p2)
            line(src, p1, p2, convert_color(color), thickness, 8)


def draw_polygons(img, polygons, thickness=1, color=(0, 255, 0)):
    color = convert_color(color)
    if thickness == -1:
        fillPoly(img, polygons, color)
    else:
        polylines(img, array(polygons, dtype="int32"), 1, color, thickness=thickness)


def draw_rectangle(src, x, y, w, h, color=(255, 0, 0), thickness=1):
    p1 = new_point(x, y, tt=True)
    p2 = new_point(x + w, y + h, tt=True)

    rectangle(src, p1, p2, convert_color(color), thickness=thickness)


def draw_contour_list(
    src,
    contours,
    hierarchy,
    external_color=(0, 255, 255),
    hole_color=(255, 0, 255),
    thickness=1,
):
    n = len(contours)
    for i, _ in enumerate(contours):
        j = i + 1
        drawContours(src, contours, i, convert_color((j * 255 / n, j * 255 / n, 0)), 2)


def get_centroid(pts):
    return calculate_centroid(pts)


# ===============================================================================
# segmentation
# ===============================================================================
def contour(src):
    return findContours(src, RETR_EXTERNAL, CHAIN_APPROX_NONE)


def get_polygons(
    src,
    contours,
    hierarchy,
    convextest=False,
    nsides=3,
    min_area=100,
    perimeter_smooth_factor=0.001,
    **kw
):
    polygons = []
    areas = []
    centroids = []
    min_enclose = []
    pactuals = []
    pconvex_hulls = []
    masks = []
    color = convert_color((255, 255, 255))
    for i, cont in enumerate(contours):
        pactual = arcLength(cont, True)
        result = approxPolyDP(cont, pactual * perimeter_smooth_factor, True)

        area = abs(contourArea(result))
        M = moments(cont)

        if not M["m00"]:
            continue
        cent = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])

        if not len(result) > nsides:
            continue

        if not area > min_area:
            continue

        if convextest and not isContourConvex(result):
            continue

        a, _, b = cont.shape
        polygons.append(cont.reshape(a, b))
        ca = minEnclosingCircle(result)

        pconvex_hull = arcLength(convexHull(result), True)

        mask = colorspace(zeros_like(src))

        drawContours(mask, contours, i, color, -1)

        mask = grayspace(mask).astype(bool)

        min_enclose.append(ca[1] ** 2 * 3.1415)
        areas.append(area)
        centroids.append(cent)
        pactuals.append(pactual)
        pconvex_hulls.append(pconvex_hull)
        masks.append(mask)

    return list(
        zip(polygons, areas, min_enclose, centroids, pactuals, pconvex_hulls, masks)
    )


# ============= EOF =============================================
