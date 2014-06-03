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

#=============enthought library imports=======================

#============= standard library imports ========================
import math
from copy import deepcopy

from numpy import asarray, average
from uncertainties import ufloat, umath
from numpy import array

from pychron.processing.arar_constants import ArArConstants
from pychron.core.stats.core import calculate_weighted_mean




#============= local library imports  ==========================


def calculate_F_ratio(m4039, m3739, m3639, pr):
    """
    required ratios
    (40/39)m
    (36/39)m
    (37/39)m


    """

    atm4036 = 295.5
    n = m4039 - atm4036 * m3639 + atm4036 * pr.get('ca3637') * m3739
    d = 1 - pr.get('ca3937') * m3739
    F = n / d - pr.get('k4039')
    return F


def extract_isochron_xy(analyses):
    ans = [(ai.get_interference_corrected_value('Ar39'),
            ai.get_interference_corrected_value('Ar36'),
            ai.get_interference_corrected_value('Ar40'))
           for ai in analyses]
    a39, a36, a40 = array(ans).T
    # print 'a40',a40
    # print 'a39',a39
    # print 'a36',a36
    try:
        xx = a39 / a40
        yy = a36 / a40
    except ZeroDivisionError:
        return

    return xx, yy


def calculate_isochron(analyses, reg='NewYork'):
    ref = analyses[0]
    ans = [(ai.get_interference_corrected_value('Ar39'),
            ai.get_interference_corrected_value('Ar36'),
            ai.get_interference_corrected_value('Ar40'))
           for ai in analyses]

    a39, a36, a40 = array(ans).T
    try:
        xx = a39 / a40
        yy = a36 / a40
    except ZeroDivisionError:
        return

    xs, xerrs = zip(*[(xi.nominal_value, xi.std_dev) for xi in xx])
    ys, yerrs = zip(*[(yi.nominal_value, yi.std_dev) for yi in yy])

    xds, xdes = zip(*[(xi.nominal_value, xi.std_dev) for xi in a40])
    yns, ynes = zip(*[(xi.nominal_value, xi.std_dev) for xi in a36])
    xns, xnes = zip(*[(xi.nominal_value, xi.std_dev) for xi in a39])
    reg = isochron_regressor(xs, xerrs, ys, yerrs,
                             xds, xdes, xns, xnes, yns, ynes,
                             reg)
    xint = ufloat(reg.x_intercept, reg.x_intercept_error)
    try:
        R = xint ** -1
    except ZeroDivisionError:
        R = 0

    age = ufloat(0, 0)
    if R > 0:
        age = age_equation((ref.j.nominal_value, 0), R, arar_constants=ref.arar_constants)
    return age, reg, (xs, ys, xerrs, yerrs)


def isochron_regressor(xs, xes, ys, yes,
                       xds, xdes, xns, xnes, yns, ynes,
                       reg='Reed'):
    if reg.lower() in ('newyork', 'new_york'):
        from pychron.core.regression.new_york_regressor import NewYorkRegressor as klass
    else:
        from pychron.core.regression.new_york_regressor import ReedYorkRegressor as klass
    reg = klass(xs=xs, ys=ys,
                xserr=xes, yserr=yes,
                xds=xds, xdes=xdes,
                xns=xns, xnes=xnes,
                yns=yns, ynes=ynes)
    reg.calculate()
    return reg


def calculate_plateau_age(ages, errors, k39, kind='inverse_variance'):
    """
        ages: list of ages
        errors: list of corresponding  1sigma errors
        k39: list of 39ArK signals

        return age, error
    """
    # print 'ages=array({})'.format(ages)
    # print 'errors=array({})'.format(errors)
    # print 'k39=array({})'.format(k39)

    ages = asarray(ages)
    errors = asarray(errors)

    k39 = asarray(k39)
    from pychron.processing.plateau import Plateau

    p = Plateau(ages=ages,
                errors=errors, signals=k39)
    pidx = p.find_plateaus()
    # pidx = find_plateaus(ages, errors, k39,
    #                      overlap_sigma=2)
    if pidx:
        sx = slice(*pidx)
        plateau_ages = ages[sx]

        if kind == 'vol_fraction':
            weights = k39[sx]
            wm, we = average(plateau_ages, weights=weights)
        else:
            plateau_errors = errors[sx]
            wm, we = calculate_weighted_mean(plateau_ages, plateau_errors)

        return wm, we, pidx


def calculate_flux(f, age, arar_constants=None):
    """
        #rad40: radiogenic 40Ar
        #k39: 39Ar from potassium
        f: F value rad40Ar/39Ar
        age: age of monitor in years

        solve age equation for J
    """
    # if isinstance(rad40, (list, tuple)):
    #     rad40 = ufloat(*rad40)
    # if isinstance(k39, (list, tuple)):
    #     k39 = ufloat(*k39)

    if isinstance(f, (list, tuple)):
        f = ufloat(*f)

    if isinstance(age, (list, tuple)):
        age = ufloat(*age)
        #    age = (1 / constants.lambdak) * umath.log(1 + JR)
    try:
        # r = rad40 / k39
        if arar_constants is None:
            arar_constants = ArArConstants()

        j = (umath.exp(age * arar_constants.lambda_k.nominal_value) - 1) / f
        return j.nominal_value, j.std_dev
    except ZeroDivisionError:
        return 1, 0


#    return j
def calculate_decay_time(dc, f):
    return math.log(f) / dc


def calculate_decay_factor(dc, segments):
    """
        McDougall and Harrison
        p.75 equation 3.22

        the book suggests using ti==analysis_time-end of irradiation segment_i

        mass spec uses ti==analysis_time-start of irradiation segment_i

        using start seems more appropriate
    """

    a = sum([pi * ti for pi, ti, _ in segments])

    b = sum([pi * ((1 - math.exp(-dc * ti)) / (dc * math.exp(dc * dti)))
             for pi, ti, dti in segments])
    try:
        return a / b
    except ZeroDivisionError:
        return 1.0


def abundance_sensitivity_correction(isos, abundance_sensitivity):
    s40, s39, s38, s37, s36 = isos
    # correct for abundance sensitivity
    # assumes symmetric and equal abundant sens for all peaks
    n40 = s40 - abundance_sensitivity * (s39 + s39)
    n39 = s39 - abundance_sensitivity * (s40 + s38)
    n38 = s38 - abundance_sensitivity * (s39 + s37)
    n37 = s37 - abundance_sensitivity * (s38 + s36)
    n36 = s36 - abundance_sensitivity * (s37 + s37)
    return [n40, n39, n38, n37, n36]


def apply_fixed_k3739(a39, pr, fixed_k3739):
    """
        x=ca37/k39
        y=ca37/ca39
        T=s39dec_cor

        T=ca39+k39
        T=ca37/y+ca37/x

        ca37=(T*x*y)/(x+y)
    """
    x = fixed_k3739
    y = 1 / pr.get('ca3937', 1)
    ca37 = (a39 * x * y) / (x + y)
    ca39 = pr.get('ca3937', 0) * ca37
    k39 = a39 - ca39
    k37 = x * k39
    return ca37, ca39, k37, k39


def interference_corrections(a40, a39, a38, a37, a36,
                             production_ratios,
                             arar_constants=None,
                             fixed_k3739=False):
    if production_ratios is None:
        production_ratios = {}

    if arar_constants is None:
        arar_constants = ArArConstants()

    pr = production_ratios
    k37 = ufloat(0, 1e-20)

    if arar_constants.k3739_mode.lower() == 'normal' and not fixed_k3739:
        # iteratively calculate 37, 39
        for _ in range(5):
            ca37 = a37 - k37
            ca39 = pr.get('ca3937', 0) * ca37
            k39 = a39 - ca39
            k37 = pr.get('k3739', 0) * k39
    else:
        if not fixed_k3739:
            fixed_k3739 = arar_constants.fixed_k3739

        ca37, ca39, k37, k39 = apply_fixed_k3739(a39, pr, fixed_k3739)

    k38 = pr.get('k3839', 0) * k39

    if not arar_constants.allow_negative_ca_correction:
        ca37 = max(ufloat(0, 0), ca37)

    ca36 = pr.get('ca3637', 0) * ca37
    ca38 = pr.get('ca3837', 0) * ca37

    return k37, k38, k39, ca36, ca37, ca38, ca39


def calculate_atmospheric(a38, a36, k38, ca38, ca36, decay_time,
                          production_ratios=None,
                          arar_constants=None):
    """
        McDougall and Harrison
        Roddick 1983
        Foland 1993

        iteratively calculate atm36
    """
    if production_ratios is None:
        production_ratios = {}

    if arar_constants is None:
        arar_constants = ArArConstants()

    pr = production_ratios

    m = pr.get('cl3638', 0) * arar_constants.lambda_Cl36.nominal_value * decay_time
    atm36 = ufloat(0, 1e-20)
    for _ in range(5):
        ar38atm = arar_constants.atm3836.nominal_value * atm36
        cl38 = a38 - ar38atm - k38 - ca38
        cl36 = cl38 * m
        atm36 = a36 - ca36 - cl36
    return atm36, cl36


def calculate_F(isotopes,
                decay_time,
                interferences=None,
                arar_constants=None,
                fixed_k3739=False):
    """
        isotope values corrected for blank, baseline, (background)
        ic_factor, (discrimination), ar37 and ar39 decay

    """
    a40, a39, a38, a37, a36 = isotopes

    #a37*=113

    if interferences is None:
        interferences = {}

    if arar_constants is None:
        arar_constants = ArArConstants()

    #make local copy of interferences
    pr = dict(((k, v.__copy__()) for k, v in interferences.iteritems()))

    #for k,v in pr.iteritems():
    #    print k, v
    k37, k38, k39, ca36, ca37, ca38, ca39 = interference_corrections(a40, a39, a38, a37, a36,
                                                                     pr, arar_constants, fixed_k3739)
    atm36, cl36 = calculate_atmospheric(a38, a36, k38, ca38, ca36,
                                        decay_time,
                                        pr,
                                        arar_constants)

    # calculate rodiogenic
    # dont include error in 40/36
    atm40 = atm36 * arar_constants.atm4036.nominal_value
    k40 = k39 * pr.get('k4039', 1)

    rad40 = a40 - atm40 - k40
    try:
        f = rad40 / k39
    except ZeroDivisionError:
        f = ufloat(1.0, 0)

    rf = deepcopy(f)
    # f = ufloat(f.nominal_value, f.std_dev, tag='F')
    non_ar_isotopes = dict(ca39=ca39,
                           k38=k38,
                           ca38=ca38,
                           k37=k37,
                           ca37=ca37,
                           ca36=ca36,
                           cl36=cl36)

    try:
        rp = rad40 / a40 * 100
    except ZeroDivisionError:
        rp = ufloat(0, 0)

    computed = dict(rad40=rad40, rad40_percent=rp,
                    k39=k39)
    #print 'Ar40', a40-k40, a40, k40
    #print 'Ar39', a39-k39, a39, k39
    interference_corrected = dict(Ar40=a40 - k40,
                                  Ar39=k39,
                                  Ar38=a38,  #- k38 - ca38,
                                  Ar37=a37,  #- ca37 - k37,
                                  Ar36=atm36)
    ##clear errors in irrad
    for pp in pr.itervalues():
        pp.std_dev = 0
    f_wo_irrad = f

    return rf, f_wo_irrad, non_ar_isotopes, computed, interference_corrected


def age_equation(j, f,
                 include_decay_error=False,
                 arar_constants=None):
    if isinstance(j, tuple):
        j = ufloat(*j)
    elif isinstance(j, str):
        j = ufloat(j)

    if isinstance(f, tuple):
        f = ufloat(*f)
    elif isinstance(f, str):
        f = ufloat(f)
    if arar_constants is None:
        arar_constants = ArArConstants()

    scalar = float(arar_constants.age_scalar)
    lk = arar_constants.lambda_k
    if not include_decay_error:
        lk = lk.nominal_value
    try:
        return (lk ** -1 * umath.log(1 + j * f)) / scalar
    except (ValueError, TypeError):
        return ufloat(0, 0)


#===============================================================================
# non-recursive
#===============================================================================

def calculate_error_F(signals, F, k4039, ca3937, ca3637):
    """
        McDougall and Harrison
        p92 eq 3.43

    """

    m40, m39, m38, m37, m36 = signals
    G = m40 / m39
    B = m36 / m39
    D = m37 / m39
    C1 = 295.5
    C2 = ca3637.nominal_value
    C3 = k4039.nominal_value
    C4 = ca3937.nominal_value

    ssD = D.std_dev ** 2
    ssB = B.std_dev ** 2
    ssG = G.std_dev ** 2
    G = G.nominal_value
    B = B.nominal_value
    D = D.nominal_value

    ssF = ssG + C1 ** 2 * ssB + ssD * (C4 * G - C1 * C4 * B + C1 * C2) ** 2
    return ssF ** 0.5


def calculate_error_t(F, ssF, j, ssJ):
    """
        McDougall and Harrison
        p92 eq. 3.43
    """
    JJ = j * j
    FF = F * F
    constants = ArArConstants()
    ll = constants().lambdak.nominal_value ** 2
    sst = (JJ * ssF + FF * ssJ) / (ll * (1 + F * j) ** 2)
    return sst ** 0.5

#============= EOF =====================================
##============= EOF ====================================
# # plateau definition
# plateau_criteria = {'number_steps': 3}
#
#
# def overlap(a1, a2, e1, e2, overlap_sigma):
#     e1 *= overlap_sigma
#     e2 *= overlap_sigma
#     if a1 - e1 < a2 + e2 and a1 + e1 > a2 - e2:
#         return True
#
# def find_plateaus(ages, errors, signals, overlap_sigma=1, exclude=None):
#     """
#         return list of plateau indices
#     """
#
#     if exclude is None:
#         exclude = []
#     plats = []
#     platids = []
#     for i in range(len(ages)):
#         if i in exclude:
#             continue
#         ids = _find_plateau(ages, errors, signals, i, overlap_sigma, exclude)
#         if ids is not None and ids.any():
#             start, end = ids
#             plats.append(end - start)
#             platids.append((start, end))
#
#             #    print plats, platids
#     if plats:
#         plats = asarray(plats)
#         #platids = asarray(platids)
#
#         ps = platids[argmax(plats)]
#         if ps[0] != ps[1]:
#             return ps
#
#
# def _find_plateau(ages, errors, signals, start, overlap_sigma, exclude):
#     plats = []
#     platids = []
#     for i in range(1, len(ages)):
#         if i in exclude:
#             continue
#         if check_plateau(ages, errors, signals, start, i, overlap_sigma, exclude):
#             plats.append(i - start)
#             platids.append((start, i))
#     if plats:
#         plats = asarray(plats)
#         platids = asarray(platids)
#         return platids[argmax(plats)]
#
#
# def check_plateau(ages, errors, signals, start, end, overlap_sigma, exclude):
#     for i in range(start, min(len(ages), end + 1)):
#         if i in exclude:
#             continue
#         for j in range(start, min(len(ages), end + 1)):
#             if j in exclude:
#                 continue
#             if i != j:
#                 obit = not overlap(ages[i], ages[j], errors[i], errors[j], overlap_sigma)
#                 mswdbit = not check_mswd(ages, errors, start, end)
#                 percent_releasedbit = not check_percent_released(signals, start, end)
#                 n_steps_bit = (end - start) + 1 < 3
#                 if (obit or
#                         mswdbit or
#                         percent_releasedbit or
#                         n_steps_bit):
#                     return False
#
#     return True
#
#
# def check_percent_released(signals, start, end):
#     tot = sum(signals)
#     s = sum(signals[start:end + 1])
#     return s / tot >= 0.5
#
#
# def check_mswd(ages, errors, start, end):
#     #    a_s = ages[start:end + 1]
#     #    e_s = errors[start:end + 1]
#     #    print calculate_mswd(a_s, e_s)
#     return True
#
#
# #===============================================================================
# # recursive
# # from timeit testing recursive method is not any faster
# #  use non recursive method instead purely for readablity
# #===============================================================================
#
# def find_plateaus_r(ages, errors, start=0, end=1, plats=None, platids=None):
#     if plats is None:
#         plats = []
#         platids = []
#
#     if start == len(ages) or end == len(ages):
#         plats = asarray(plats)
#         platids = asarray(platids)
#         return platids[argmax(plats)]
#     else:
#         a = check_plateau_r(ages, errors, start, end)
#         if a:
#             plats.append((end - start))
#             platids.append((start, end))
#
#             return find_plateaus_r(ages, errors, start, end + 1, plats, platids)
#         else:
#             return find_plateaus_r(ages, errors, start + 1, end + 1, plats, platids)
#
#
# def check_plateau_r(ages, errors, start, end, isplat=True):
#     if end < len(ages):
#         return isplat and check_plateau_r(ages, errors, start, end + 1, isplat)
#     else:
#         for i in range(start, min(len(ages), end + 1)):
#             for j in range(start, min(len(ages), end + 1)):
#                 if i != j:
#                     if not overlap(ages[i], ages[j], errors[i], errors[j]):
#                         return False
#         return True
#
#
#
# #def plateau_age(data):
# #    '''
# #    data = rowtuple of corrected data
# #    '''
# #    #calculate the ages and store ref to 39
# #    ages = []
# #    ar_39_signals = []
# #
# #    integrated = new_unknown()
# #    keys = ['ar40', 'ar39', 'ar38', 'ar37', 'ar36']
# #    integrated.j_value = data[0].j_value
# #    for d in data:
# #        for k in keys:
# #            integrated.isotopes[k] += d.isotopes[k]
# #        ar_39_signals.append(d.isotopes['ar39'])
# #
# #        ages.append(calc_corrected_age(d))
# #    print 'integrated age :', calc_corrected_age(integrated)
# #
# #    indices = find_plateaus(ages)
# #    if indices is None:
# #        print 'no plateau'
# #    for d in data[indices[0]:indices[1]+1]:
# #        print 'plateau step',d.AnalysisID,d.DataReductionSessionID
# #
# #def calc_corrected_age(corrected_unknown):
# #    '''
# #    return age in Ma
# #
# #    '''
# #
# #    #correct unknown for blank value
# #    corrected_unknown.correct_for_blank()
# #    corrected_unknown.correct_for_decay()
# #
# #    days_since_irradiation = corrected_unknown.days_since_irradiation()
# #
# #    #set up some shorthand names
# #    corrected_40 = corrected_unknown.isotopes['ar40']
# #    corrected_39 = corrected_unknown.isotopes['ar39']
# #    corrected_38 = corrected_unknown.isotopes['ar38']
# #    corrected_37 = corrected_unknown.isotopes['ar37']
# #    corrected_36 = corrected_unknown.isotopes['ar36']
# #
# #
# #    j_value = corrected_unknown.j_value
# #    production_ratio = corrected_unknown.production_ratio
# #
# #    return __corrected_age_calc__(corrected_40, corrected_39, corrected_38, corrected_37, corrected_36,
# #                           j_value, production_ratio, days_since_irradiation) / 1e6
#
#
#
# def calculate_arar_age(signals, ratios, ratio_errs,
#                       a37decayfactor, a39decayfactor, j, jer, d, der):
#    s40, s40er, s39, s39er, s38, s38er, s37, s37er, s36, s36er = signals
#    p36cl38cl, k4039, k3839, ca3637, ca3937, ca3837 = ratios
#    k4039er, ca3637er, ca3937er = ratio_errs
# #    a37decayfactor = 1
# #    a39decayfactor = 1
#    #convert to ufloats
#    from uncertainties import ufloat
#    from uncertainties.umath import log
#
#    s40 = ufloat((s40, s40er))
#    s39 = ufloat((s39, s39er))
#    s38 = ufloat((s38, s38er))
#    s37 = ufloat((s37, s37er))
#    s36 = ufloat((s36, s36er))
#    k4039 = ufloat((k4039, k4039er))
#    ca3637 = ufloat((ca3637, ca3637er))
#    ca3937 = ufloat((ca3937, ca3937er))
#    j = ufloat((j, jer))
#    d = ufloat((d, der))
#
# #    #calculate the age
#    ca37 = s37 * a37decayfactor
#    s39 = s39 * a39decayfactor
#    ca36 = ca3637 * ca37
#    ca38 = ca3837 * ca37
#    ca39 = ca3937 * ca37
#    k39 = s39 - ca39
#    k38 = k3839 * k39
#
#    time_since_irradiation = (log(1 / a37decayfactor) /
#                        (-1 * constants.lambda_37 * 365.25))
#
#    if constants.lambda_cl36 < 0.1:
#        m = p36cl38cl * constants.lambda_cl36 * time_since_irradiation
#    else:
#        m = p36cl38cl
#    mcl = m / (m * constants.atm3836 - 1)
#    cl36 = mcl * (constants.atm3836 * (s36 - ca36) - s38 + k38 + ca38)
#    atm36 = s36 - ca36 - cl36
#
#    atm40 = atm36 * constants.atm4036
#    k40 = k39 * k4039
#    ar40rad = s40 - atm40 - k40
#    JR = j * ar40rad / k39
# #    age = (1 / constants.lambdak) * math.log(1 + JR)
#    age = (1 / constants.lambdak) * log(1 + JR)
#
#    #==========================================================================
#    # errors mass spec copy
#    #==========================================================================
#
#    square = lambda x: x * x
#
#    Tot40Er = s40er
#    Tot39Er = s39er
#    Tot38Er = s38er
#    Tot37Er = s37er
#    Tot36Er = s36er
#
#    D = d
#    D2 = d * d
#    D3 = d * D2
#    D4 = d * D3
#
#    T40 = s40 / D4
#    T39 = s39 / D3
#    T38 = s39 / D2
#    T37 = s39 / D
#    T36 = s36
#
#    A4036 = constants.atm4036
#    A3836 = constants.atm3836
#
#    s = ca3937 * D * T37
#    T = ca3637 * D * T37
#    G = D3 * T39 - s
# #    P = mcl * (ca3837 * D * T37 + A3836 * (T36 - T) - D2 * T38 + k3839 * G)
#    R = (-k4039 * G - A4036 * (T36 - T - mcl * (ca3837 * D * T37 + A3836 * (T36 - T) - D2 * T38 + k3839 * G)) + D4 * T40)
#    G2 = G * G
#
#    er40 = square(D4 * j / G) * square(Tot40Er)
#
#    er39 = square((j * (-D3 * k4039 + A4036 * D3 * k3839 * mcl)) / G - (D3 * j * R) / G2) * square(Tot39Er)
#
#    er38 = square(A4036 * D2 * j * mcl / G) * square(Tot38Er)
#
#    er37 = square((j * (ca3937 * D * k4039 - A4036 *
#            (-ca3637 * D - (-A3836 * ca3637 * D + ca3837 * D - ca3937 * D * k3839) * mcl)))
#            / G + (ca3937 * D * j * R) / G2) * square(Tot37Er)
#
#    er36 = square(A4036 * j * (1 - A3836 * mcl) / G) * square(Tot36Er)
#    '''
#    square((j * (4 * T40 * D3 - K4039 * (3 * D2 * T39 - Ca3937 * T37)
#        - A4036 * (-(Ca3637 * T37) - MCl * (-(A3836 * Ca3637 * T37)
#        + Ca3837 * T37 + K3839 * (3 * D2 * T39 - Ca3937 * T37)
#        - 2 * D * T38))))
#        / (D3 * T39 - s) - (1 * j * (3 * D2 * T39 - Ca3937 * T37)
#        * (T40 * D4 - K4039 * (D3 * T39 - s)
#        - A4036 * (T36 - T - MCl * (-(T38 * D2) + Ca3837 * T37 * D + A3836 * (T36 - T) + K3839 * (D3 * T39 - s)))))
#        / square(D3 * T39 - s)) * square(DiscEr)
#      '''
#    erD = square((j * (4 * T40 * D3 - k4039 * (3 * D2 * T39 - ca3937 * T37)
#        - A4036 * (-(ca3637 * T37) - mcl * (-(A3836 * ca3637 * T37)
#        + ca3837 * T37 + k3839 * (3 * D2 * T39 - ca3937 * T37)
#        - 2 * D * T38))))
#        / (D3 * T39 - s) - (1 * j * (3 * D2 * T39 - ca3937 * T37)
#        * (T40 * D4 - k4039 * (D3 * T39 - s)
#        - A4036 * (T36 - T - mcl * (-(T38 * D2) + ca3837 * T37 * D + A3836 * (T36 - T) + k3839 * (D3 * T39 - s)))))
#        / square(D3 * T39 - s)) * square(der)
#
#    er4039 = square(j * (s - D3 * T39) / G) * square(k4039er)
#
#    er3937 = square((j * (D * k4039 * T37 - A4036 * D * k3839 * mcl * T37)) / G + (D * j * T37 * R) / G2) * square(ca3937er)
#
#    er3637 = square(-((A4036 * j * (-D * T37 + A3836 * D * mcl * T37)) / G)) * square(ca3637er)
#
#    erJ = square(R / G) * square(jer)
#    JRer = (er40 + er39 + er38 + er37 + er36 + erD + er4039 + er3937 + er3637 + erJ) ** 0.5
#    age_err = (1e-6 / constants.lambdak) * JRer / (1 + ar40rad / k39 * j)
##===============================================================================
# # error pychron port
##===============================================================================
# #    s = ca3937 * s37
# #    T = ca3637 * s37
# #    G = s39 - s
# #    R = (-k4039 * G - constants.atm4036 * (s36 - T - mcl * (ca3837 * s37 + constants.atm3836 * (s36 - T) - s38 + k3839 * G)) + s40)
# #    #ErComp(1) = square(D4 * j / G) * square(Tot40Er)
# #    er40 = (d ** 4 * j / G) ** 2 * s40er ** 2
# #
# #    #square((j * (-D3 * K4039 + A4036 * D3 * K3839 * MCl)) / G - (D3 * j * R) / G2) * square(Tot39Er)
# #    d3 = d ** 3
# #    er39 = ((j * (-d3 * k4039 + constants.atm4036 * d3 * k3839 * mcl)) / G - (d3 * j * R) / G ** 2) ** 2 * s39er ** 2
# #
# #    #square(A4036 * D2 * j * MCl / G) * square(Tot38Er)
# #    er38 = (constants.atm4036 * d * d * j * mcl / G) ** 2 * s38er ** 2
# #
# #    #square((j * (Ca3937 * D * K4039 - A4036 *
# #    #        (-Ca3637 * D - (-A3836 * Ca3637 * D + Ca3837 * D - Ca3937 * D * K3839) * MCl)))
# #    #        / G + (Ca3937 * D * j * R) / G2) * square(Tot37Er)
# #    er37 = ((j * (ca3937 * d * k4039 - constants.atm4036
# #            * (-ca3637 * d - (-constants.atm3836 * ca3637 * d + ca3837 * d - ca3937 * d * k3839) * mcl)))
# #            / G + (ca3937 * d * j * R) / G ** 2) ** 2 * s37er ** 2
# #
# #    #square(A4036 * j * (1 - A3836 * MCl) / G) * square(Tot36Er)
# #    er36 = (constants.atm4036 * j * (1 - constants.atm3836 * mcl) / G) ** 2 * s36er ** 2
# #
# #    #square((j * (4 * T40 * D3 - K4039 * (3 * D2 * T39 - Ca3937 * T37)
# #    #    -A4036 * (-(Ca3637 * T37) - MCl * (-(A3836 * Ca3637 * T37)
# #    #    + Ca3837 * T37 + K3839 * (3 * D2 * T39 - Ca3937 * T37)
# #    #    - 2 * D * T38))))
# #    #    / (D3 * T39 - s) - (1 * j * (3 * D2 * T39 - Ca3937 * T37)
# #    #    * (T40 * D4 - K4039 * (D3 * T39 - s)
# #    #    - A4036 * (T36 - T - MCl * (-(T38 * D2) + Ca3837 * T37 * D + A3836 * (T36 - T) + K3839 * (D3 * T39 - s)))))
# #    #    / square(D3 * T39 - s)) * square(DiscEr)
# #
# #    erD = ((j * (4 * s40 / d - k4039 * (3 * s39 / d - ca3937 * s37 / d)
# #        - constants.atm4036 * (-(ca3637 * s37 / d) - mcl * (-(constants.atm3836 * ca3637 * s37 / d)
# #        + ca3837 * s37 / d + k3839 * (3 * s39 / d - ca3937 * s37 / d)
# #        - 2 * s38 / d))))
# #        / (s39 / d - s) - (1 * j * (3 * s39 / d - ca3937 * s37 / d)
# #        * (s40 / d - k4039 * (s40 / d - s)
# #        - constants.atm4036 * (s36 - T - mcl * (-(s38 / d) + ca3837 * s37 + constants.atm3836 * (s36 - T) + k3839 * (s39 / d - s)))))
# #        / (s39 / d - s) ** 2) ** 2 * der ** 2
# #    #square(j * (s - D3 * T39) / G) * square(K4039Er)
# #    er4039 = (j * (s - s39 / d) / G) ** 2 * k4039er ** 2
# #
# #    #square((j * (D * K4039 * T37 - A4036 * D * K3839 * MCl * T37)) / G + (D * j * T37 * R) / G2) * square(Ca3937Er)
# #    er3937 = ((j * (k4039 * s37 - constants.atm4036 * k3839 * mcl * s37)) / G + (j * s37 * R) / G ** 2) ** 2 * ca3937er ** 2
# #
# #    #square(-((A4036 * j * (-D * T37 + A3836 * D * MCl * T37)) / G)) * square(Ca3637Er)
# #    er3637 = (-((constants.atm4036 * j * (-s37 + constants.atm3836 * mcl * s37)) / G)) ** 2 * ca3637er ** 2
# #
# #    #square(R / G) * square(JErLocal)
# #    erJ = (R / G) ** 2 * jer ** 2
# #    JRer = (er40 + er39 + er38 + er37 + er36 + erD + er4039 + er3937 + er3637 + erJ) ** 0.5
# #    age_err = (1e-6 / constants.lambdak) * JRer / (1 + ar40rad / k39 * j)
#
#    return age / 1e6, age_err
