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

# ============= standard library imports ========================

# ============= local library imports  ==========================
"""
    https://gist.github.com/sixtenbe/1178136
"""
from numpy import (
    Inf,
    isscalar,
    array,
    argmax,
    polyfit,
    asarray,
    argsort,
    vstack,
    arange,
)

from pychron.pychron_constants import NULL_STR


def _datacheck_peakdetect(x_axis, y_axis):
    if x_axis is None:
        x_axis = arange(len(y_axis))

    if len(y_axis) != len(x_axis):
        raise ValueError

    # needs to be a numpy array
    y_axis = array(y_axis)
    x_axis = array(x_axis)
    return x_axis, y_axis


def find_peaks(y_axis, x_axis=None, lookahead=300, delta=0):
    """

    Converted from/based on a MATLAB script at:
    http://billauer.co.il/peakdet.html

    function for detecting local maximas and minmias in a signal.
    Discovers peaks by searching for values which are surrounded by lower
    or larger values for maximas and minimas respectively

    keyword arguments:
    y_axis -- A list containg the signal over which to find peaks
    x_axis -- (optional) A x-axis whose values correspond to the y_axis list
        and is used in the return to specify the postion of the peaks. If
        omitted an index of the y_axis is used. (default: None)
    lookahead -- (optional) distance to look ahead from a peak candidate to
        determine if it is the actual peak (default: 200)
        '(sample / period) / f' where '4 >= f >= 1.25' might be a good value
    delta -- (optional) this specifies a minimum difference between a peak and
        the following points, before a peak may be considered a peak. Useful
        to hinder the function from picking up false peaks towards to end of
        the signal. To work well delta should be set to delta >= RMSnoise * 5.
        (default: 0)
            delta function causes a 20% decrease in speed, when omitted
            Correctly used it can double the speed of the function

    return -- two lists [max_peaks, min_peaks] containing the positive and
        negative peaks respectively. Each cell of the lists contains a tupple
        of: (position, peak_value)
        to get the average peak value do: np.mean(max_peaks, 0)[1] on the
        results to unpack one of the lists into x, y coordinates do:
        x, y = zip(*tab)
    """
    max_peaks = []
    min_peaks = []
    dump = []  # Used to pop the first hit which almost always is false

    # check input data
    x_axis, y_axis = _datacheck_peakdetect(x_axis, y_axis)
    # store data length for later use
    length = len(y_axis)

    # perform some checks
    if lookahead < 1:
        raise ValueError("Lookahead must be '1' or above in value")
    if not (isscalar(delta) and delta >= 0):
        raise ValueError("delta must be a positive number")

    # maxima and minima candidates are temporarily stored in
    # mx and mn respectively
    mn, mx = Inf, -Inf

    # Only detect peak if there is 'lookahead' amount of points after it
    for index, (x, y) in enumerate(zip(x_axis[:-lookahead], y_axis[:-lookahead])):
        if y > mx:
            mx = y
            mxpos = x
        if y < mn:
            mn = y
            mnpos = x

        # look for max
        if y < mx - delta and mx != Inf:
            # Maxima peak candidate found
            # look ahead in signal to ensure that this is a peak and not jitter
            if y_axis[index : index + lookahead].max() < mx:
                max_peaks.append([mxpos, mx])
                dump.append(True)
                # set algorithm to only find minima now
                mx = Inf
                mn = Inf
                if index + lookahead >= length:
                    # end is within lookahead no more peaks can be found
                    break
                continue
                # else:  #slows shit down this does
                #    mx = ahead
                #    mxpos = x_axis[np.where(y_axis[index:index+lookahead]==mx)]

        # look for min
        if y > mn + delta and mn != -Inf:
            # Minima peak candidate found
            # look ahead in signal to ensure that this is a peak and not jitter
            if y_axis[index : index + lookahead].min() > mn:
                min_peaks.append([mnpos, mn])
                dump.append(False)
                # set algorithm to only find maxima now
                mn = -Inf
                mx = -Inf
                if index + lookahead >= length:
                    # end is within lookahead no more peaks can be found
                    break
                    # else:  #slows shit down this does
                    #    mn = ahead
                    #    mnpos = x_axis[np.where(y_axis[index:index+lookahead]==mn)]

    # Remove the false hit on the first value of the y_axis
    try:
        if dump[0]:
            max_peaks.pop(0)
        else:
            min_peaks.pop(0)
        del dump
    except IndexError:
        # no peaks were found, should the function return empty lists?
        pass

    return [max_peaks, min_peaks]


class PeakCenterError(BaseException):
    def __init__(self, *args, **kw):
        super(PeakCenterError, self).__init__(*args)
        self.low_pos_error = kw.get("low_pos_error")
        self.high_pos_error = kw.get("high_pos_error")


def fformat(v, format_str):
    if format_str:
        try:
            v = format_str.format(v)
        except ValueError:
            pass
    return v


def calculate_resolution(x, y, format_str=None, return_all=False):
    try:
        [lx, cx, hx], [ly, cy, hy], mx, my = calculate_peak_center(
            x, y, percent=95, ignore_max=True
        )
        res = cx / (hx - lx)
        data = ([lx, cx, hx], [ly, cy, hy])
    except PeakCenterError as e:
        res, data = NULL_STR, None

    res = fformat(res, format_str)
    if return_all:
        return res, data
    else:
        return res


def calculate_resolving_power(x, y, format_str=None, return_all=False):
    try:
        [lx5, cx5, hx5], [ly5, cy5, hy5], _, _ = calculate_peak_center(
            x, y, test_peak_flat=False, percent=95, ignore_max=True
        )
        [lx95, cx95, hx95], [ly95, cy95, hy95], _, _ = calculate_peak_center(
            x, y, test_peak_flat=False, percent=5, ignore_max=True
        )

        ldelta = abs(lx95 - lx5)
        hdelta = abs(hx95 - hx5)

        lrp = (lx5 + ldelta / 2) / ldelta
        hrp = (hx95 + hdelta / 2) / hdelta
        ldata, hdata = ((lx5, lx95), (ly5, ly95)), ((hx5, hx95), (hy5, hy95))
    except PeakCenterError:
        lrp, hrp, ldata, hdata = NULL_STR, NULL_STR, None, None

    lrp, hrp = fformat(lrp, format_str), fformat(hrp, format_str)
    if return_all:
        return lrp, hrp, ldata, hdata
    else:
        return lrp, hrp


def calculate_peak_center(
    x, y, test_peak_flat=True, min_peak_height=1.0, percent=80, ignore_max=False
):
    """
    returns: (low_x, center_x, high_x), (low_y, center_y, high_y), max_y, min_y

        or

        raises a PeakCenterError exception
    """

    x = array(x)
    y = array(y)
    xy = vstack((x, y)).T
    x, y = xy[argsort(xy[:, 0])].T

    ma = max(y)
    max_i = argmax(y)
    if not ignore_max and ma < min_peak_height:
        raise PeakCenterError(
            "No peak greater than {}. max = {}".format(min_peak_height, ma)
        )

    if max_i <= 3 or max_i >= len(x) - 3:
        raise PeakCenterError(
            "PeakCenterError: peak not well centered. Max intensity too close to scan limits"
        )
        # max_i = len(x) // 2

    mx = x[max_i]
    my = ma

    # look backward for point that is peak_percent% of max
    for i in range(max_i, 0, -1):
        # this prevent looping around to the end of the list
        if i < 1:
            raise PeakCenterError(
                "PeakCenterError: could not find a low pos", low_pos_error=True
            )

        try:
            if y[i] < (ma * (1 - percent / 100.0)):
                break
        except IndexError:
            raise PeakCenterError(
                "PeakCenterError: could not find a low pos", low_pos_error=True
            )

    # xstep = (x[i] - x[i - 1]) / 2.
    # lx = x[i] - xstep
    # ly = y[i] - (y[i] - y[i - 1]) / 2.
    lx, ly = x[i], y[i]

    # look forward for point that is 80% of max
    for i in range(max_i, x.shape[0], 1):
        try:
            if y[i] < (ma * (1 - percent / 100.0)):
                break
        except IndexError:
            raise PeakCenterError(
                "PeakCenterError: could not find a high pos", high_pos_error=True
            )

    try:
        hx = x[i]
        hy = y[i]
        # hx = x[i + 1] - xstep
        # hy = y[i] - (y[i] - y[i + 1]) / 2.
    except IndexError:
        raise PeakCenterError(
            "peak not well centered, len(x)={}, len(y)={}, i={}".format(
                len(x), len(y), i
            )
        )

    if (hx - lx) < 0:
        raise PeakCenterError(
            "unable to find peak bounds high_pos < low_pos. {} < {}".format(hx, lx)
        )

    cx = (hx + lx) / 2.0
    cy = ma
    if test_peak_flat:
        # find index in x closest to cx
        ccx = abs(x - cx).argmin()
        # check to see if were on a plateau
        yppts = y[ccx - 2 : ccx + 2]

        slope, _ = polyfit(list(range(len(yppts))), yppts, 1)
        std = yppts.std()

        if std > 5 and abs(slope) < 1:
            raise PeakCenterError(
                "No peak plateau std = {} (>5) slope = {} (<1)".format(std, slope)
            )

    return [lx, cx, hx], [ly, cy, hy], mx, my


def fast_find_peaks(ys, xs, **kw):
    try:
        from peakutils import indexes
    except ImportError:
        from pyface.message_dialog import warning

        warning(
            None,
            "PeakUtils required to identify and label peaks.\n\n"
            'Please install PeakUtils. From commandline use "pip install peakutils"',
        )
        return [], [], []

    ys, xs = asarray(ys), asarray(xs)
    idx = indexes(ys, **kw)
    peaks_x, pidx = interpolate(xs, ys, ind=idx)
    peak_x_ranges = []

    for i in pidx:
        ymax = ys[i]
        # search forward
        py = ymax
        for ji, yi in enumerate(ys[i:]):
            if yi / ymax < 0.1 or yi > py:
                xmax = xs[i + ji]
                break
            py = yi
        else:
            xmax = xs.max()

        py = ymax
        # search backward
        nys = ys[:i]
        n = len(nys)
        for ji, yi in enumerate(reversed(nys)):
            if yi / ymax < 0.1 or yi > py:
                xmin = xs[n - ji]
                break
            py = yi
        else:
            xmin = xs.min()

        peak_x_ranges.append((xmin, xmax))

    try:
        return peaks_x, ys[idx], peak_x_ranges
    except IndexError:
        # from pyface.message_dialog import warning
        # warning(None, 'There was an issue finding the peaks')
        return [], [], []


def interpolate(x, y, ind=None, width=10, func=None):
    """
    modified from peakutils to handle edge peaks

    Tries to enhance the resolution of the peak detection by using
    Gaussian fitting, centroid computation or an arbitrary function on the
    neighborhood of each previously detected peak index.

    Parameters
    ----------
    x : ndarray
        Data on the x dimension.
    y : ndarray
        Data on the y dimension.
    ind : ndarray
        Indexes of the previously detected peaks. If None, indexes() will be
        called with the default parameters.
    width : int
        Number of points (before and after) each peak index to pass to *func*
        in order to encrease the resolution in *x*.
    func : function(x,y)
        Function that will be called to detect an unique peak in the x,y data.

    Returns
    -------
    ndarray :
        Array with the adjusted peak positions (in *x*)
    """
    pidx = []
    out = []
    try:
        if func is None:
            from peakutils import gaussian_fit

            func = gaussian_fit

        if ind is None:
            from peakutils import indexes

            ind = indexes(y)
        for i, slice_ in (
            (i, slice(max(0, i - width), min(i + width, y.shape[0]))) for i in ind
        ):
            try:
                fit = func(x[slice_], y[slice_])
                out.append(fit)
                pidx.append(i)
            except Exception:
                pass
    except ImportError:
        from pyface.message_dialog import warning

        warning(
            None,
            "PeakUtils required to identify and label peaks.\n\n"
            'Please install PeakUtils. From commandline use "pip install peakutils"',
        )

    return array(out), pidx


# ============= EOF =============================================
