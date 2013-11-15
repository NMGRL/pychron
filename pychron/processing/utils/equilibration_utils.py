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

#============= enthought library imports =======================
from traits.api import HasTraits
from traitsui.api import View, Item
#============= standard library imports ========================
from numpy import asarray, convolve, exp, linspace, where, ones_like
from pylab import plot, show, axvline, legend, \
    xlabel, ylabel, polyval, axhline, ylim, xlim, array
#============= local library imports  ==========================
def calc_optimal_eqtime(xs, ys):

    xs, ys = asarray(xs), asarray(ys)
    # calculate rise rate for 10s window
    window = [-1, 1]
    rise_rates = convolve(ys, window, mode='same') / convolve(xs, window, mode='same')

    tol = 0.1
    rm = where(rise_rates < tol)[0]
    try:
        idx = min(rm)
        xx, yy = xs[idx], ys[idx]
    except Exception, e:
        xx, yy = None, None
        print 'calc optimal eqtime', e

    return rise_rates, xx, yy

# def sniff(t, mag=1):
#    rate = 0.5
#    return mag * (1 - exp(-rate * t))
#
# def test_eq_calc():
#    ts = linspace(0, 50, 51)
#    ys = sniff(ts, 40)
#
#    rs = calc_optimal_eqtime(ts, ys)
#    plot(ts, ys, label='I')
#    plot(ts, rs, label='dI')
#
#    tol = 0.1
#    rm = where(rs < tol)[0]
#    axvline(x=ts[min(rm)], ls='--', color='black')
#    legend()
#    show()

def F(t, mag=1, rate=0.8):
    '''
        extraction line - mass spec equilibration function
    '''
    return mag * (1 - exp(-rate * t))

def G(t, f, rate=1):
    '''
        mass spec consumption function during equilibration
    '''
    return rate * t * f
#    return ones_like(t) * mag
#    return mag * (exp(-rate * t))

def ratio_change(mag, t_inlet_close=None):
    eq_m = -0.0001
    rise_rate = 0.0125
    ts = linspace(0, 400, 500)
    f = F(ts, mag=mag)
#     g = eq_m * f
    g = G(ts, f, rate=eq_m)
    b = rise_rate * ts

    fg = f + g + b
    if t_inlet_close == None:
        rf, t_inlet_close, vi_F = calc_optimal_eqtime(ts, fg)

    bs = []
    ts = []
    for ri in range(-5, 5):
        ti = t_inlet_close + ri
        fi = F(ti, mag=mag)
        gi = G(ti, fi, rate=eq_m)
        vi = fi + gi + rise_rate * ti
        b = vi - 2 * eq_m * ti
        bs.append(b)
        ts.append(ti)

    ts, bs = array(ts), array(bs)
    return t_inlet_close, ts, bs

def equil():


    eq_m = -0.0001
    rise_rate = 0.0125
    mag = 20
    ts = linspace(0, 400, 500)
    f = F(ts, mag=mag)
#     g = eq_m * f
    g = G(ts, f, rate=eq_m)
    b = rise_rate * ts

    fg = f + g + b
    plot(ts, f, label='F Equilibration')
    plot(ts, g, label='G Consumption')
    plot(ts, fg, label='F-G (Sniff Evo)')

    rf, rollover_F, vi_F = calc_optimal_eqtime(ts, f)
    rfg, rollover_FG, vi_FG = calc_optimal_eqtime(ts, fg)
    m = 2 * eq_m * mag

    axvline(x=rollover_F, ls='--', color='blue')
    axvline(x=rollover_FG, ls='--', color='red')

    idx = list(ts).index(rollover_F)

    b = fg[idx] - m * rollover_F
    evo = polyval((m, b), ts)
    plot(ts, evo, ls='-.', color='blue', label='Static Evo. A')
    # ee = where(evo > mag)[0]
    # to_F = ts[max(ee)]
    # print 'F', rollover_F, b, to_F


    b = vi_FG - m * rollover_FG
    evo = polyval((m, b), ts)
    plot(ts, evo, ls='-.', color='red', label='Static Evo. B')

    print polyval((m, b), 200)
    ee = where(evo > mag)[0]
#     to_FG = ts[max(ee)]
#     print 'FG', rollover_FG, b, to_FG

#     axvline(x=to_FG, ls='-', color='red')
#     axvline(x=to_F, ls='-', color='blue')

    axhline(y=mag, ls='-', color='black')
#    plot([ti], [mag], 'bo')

    legend(loc=0)
#     ylim(2980, 3020)
    ylim(18, 21)
    xlim(0, 20)
    ylabel('Intensity')
    xlabel('t (s)')
#    fig = gcf()
#    fig.text(0.1, 0.01, 'asdfasfasfsadfsdaf')


    show()

if __name__ == '__main__':
    ti, ts1, bs1 = ratio_change(1000)
    ti, ts2, bs2 = ratio_change(10, ti)
    rr = bs1 / bs2
    print rr
    rr = (rr - 100) / 100.*100

    plot(ts1 - ti, rr)

    show()


#============= EOF =============================================
