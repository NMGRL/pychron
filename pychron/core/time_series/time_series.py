#===============================================================================
# Copyright 2011 Jake Ross
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

import numpy as np
from pychron.core.helpers.datetime_tools import get_datetime  # , convert_timestamp

def smooth(x, window_len=11, window='hanning'):
    x = np.asarray(x)
    s = np.r_[2 * x[0] - x[window_len - 1::-1], x, 2 * x[-1] - x[-1:-window_len:-1]]
    if window == 'flat':  # moving average
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.' + window + '(window_len)')

    y = np.convolve(w / w.sum(), s, mode='same')
    return y[window_len:-window_len + 1]

def seasonal_subseries(x, y, **kw):
    ybins = [[], [], [], [], [], [], [], [], [], [], [], [],
            [], [], [], [], [], [], [], [], [], [], [], []]
    xbins = [[], [], [], [], [], [], [], [], [], [], [], [],
            [], [], [], [], [], [], [], [], [], [], [], []]
    m = 3600 * 24. / len(x)
    for xi, yi in zip(x, y):
        i = get_datetime(xi).hour
        ybins[i - 1].append(yi)
        xbins[i - 1].append((i - 1) * 3600 + (len(xbins[i - 1])) * m)
    ms = [np.mean(x) for x in ybins]

    return xbins, ybins, ms

def downsample_1d(data, factor=5, estimator=np.mean):
    n = data.shape[0]
    crarr = data[:n - (n % int(factor))]
    a = [crarr[i::factor] for i in range(factor)]
    return estimator(np.concatenate([a]), axis=0)
# def aautocorrelation(x, **kw):
#    result = np.correlate(x, x, mode = 'full')
#    r = result[result.size / 2:]
#    return np.linspace(0, len(r) - 1, len(r)), r
#
# def bautocorrelation(x, **kw):
#    s = np.fft.fft(x)
#    r = np.real(np.fft.ifft(s * np.conjugate(s))) / np.var(x)
#    return np.linspace(0, len(r) - 1, len(r)), r

def autocorrelation(x, nlags=100):
#    from autocorr import autocorr
    from pychron.core.time_series import autocorr
    return autocorr(x, nlags=nlags)

# if __name__ == '__main__':
#    import csv
#    path = '/Users/fargo2/Desktop/tempscan2.txt'
# #    path = '/Users/fargo2/Desktop/beam_def.txt'
#    from pylab import plot, show, random, acorr, sin, linspace, array
#    n = []
#    ys = []
#    with open(path, 'r') as f:
#        reader = csv.reader(f)
#        for line in reader:
# #           ys.append(float(line[0].strip()))
#            #convert timestamp to float
# #            n.append(convert_timestamp(line[0]))
#            #n.append(get_datetime(line[0]))
#            ys.append(float(line[1]))
#    #ys = random(1000)
#   # ys = sin(4 * linspace(0, 6 , 1000)) + random(1000)
#    #acorr(ys, maxlags = 50)
#   # ys = autocorrelation(ys, nlags = 50)
#    ys = autocorr(array(ys), nlags = 50)
#    plot(ys)
#
#    show()

