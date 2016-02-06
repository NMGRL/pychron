from uncertainties import ufloat, umath

from pychron.processing.arar_constants import ArArConstants


def mcalc_fractional_error(*args):
    '''
        args= a,b,...,k,T
        where fa**2+fb**2+...+fk**2=fT**2
    '''

    T = args[-1]
    r = []
    te = T.std_dev / T.nominal_value
    for ai in args[:-1]:
        r.append(((ai.std_dev / ai.nominal_value) / te) ** 2)

    return r

def acalc_fractional_error(*args):
    '''
        args= a,b,...,k,T
        where a**2+b**2+...+k**2=T**2
    '''

    T = args[-1]

    r = []
    for ai in args[:-1]:
        r.append((ai.std_dev / T.std_dev) ** 2)

    return r

def calc_error_contrib(ar40, ar39, ar38, ar37, ar36, s40, s39, s38, s37, s36, J, constants):
    # fraction of ar36err from s36,ar37,ar38
    fe36_36, fe36_37, fe36_38 = acalc_fractional_error(s36,
                                                       ca3637 * s37,
                                                       cl3638 * s38,
                                                       ar36)

    # fraction of ar40err from 40signal, 36signal
    fe40_40, fe40_36 = acalc_fractional_error(s40, constants.atm4036_v * ar36, ar40)

    R = ar40 / ar39
    # fraction of R error from ar40 and ar39
    fe40, fe39 = mcalc_fractional_error(ar40, ar39, R)

#    JR.std_dev equals total error
    JR = J * R
    k = constants.lambda_k
    k.set_std_dev(0)
    IlambdaK = 1 / k
    M = JR + 1
#    print constants.lambda_k.std_dev() / constants.lambda_k.nominal_value
#    print IlambdaK.std_dev() / IlambdaK.nominal_value
    a = umath.log(M)
    c = IlambdaK * a

#    print IlambdaK, a
#    print c.nominal_value * ((IlambdaK.std_dev() / IlambdaK.nominal_value) ** 2 + (a.std_dev() / a.nominal_value) ** 2) ** 0.5
#    print c
    feLambdaK, feJR = mcalc_fractional_error(IlambdaK, a, c)
#    print feLambdaK, feJR, feLambdaK + feJR
#    af = (IlambdaK.std_dev() / IlambdaK.nominal_value) ** 2 * (M.std_dev() / M.nominal_value) ** 2

#    errLambdaK = a.std_dev() * feLambdaK
#    errJR = a.std_dev() * feJR

#    #fraction of JR from J and R
    Je, Re = mcalc_fractional_error(J, R, JR)
#    print Je, Re
    # fractional error from ar40. e40=F40+F36
    err = fe40 * Re * feJR

    # error in ar40 is sum of s40err and s36err
    err40 = fe40_40 * err

    err = fe40_36 * err
    # error in ar36 is sum of s40err and s36err
    err36 = fe36_36 * err
    err37 = fe36_37 * err
    err38 = fe36_38 * err

    # fractional error from ar39
    err39 = fe39 * Re * feJR

    errJ = Je * feJR
    errLambdaK = feLambdaK
    # print 'exception', err40, err36, err39, errJ
    # print 'exception', err36 + err40 + err39 + errJ

    # print 'exception', err36 + err37 + err38 + err40 + err39 + errJ + errLambdaK - 1
    assert abs(err36 + err37 + err38 + err40 + err39 + errJ + errLambdaK - 1) < 1e-10
    return err40, err39, err38, err37, err36, errJ, errLambdaK

if __name__ == '__main__':
    constants = ArArConstants()
    s40 = ufloat(5.50986, 5.50986 * 0.0004)
    s39 = ufloat(3.65491e-1, 3.65491e-1 * 0.0011)
    s38 = ufloat(4.4904e-3, 4.4904e-3 * 0.0117)
    s37 = ufloat(2.47163e-3, 2.47163e-3 * 0.038)
#    s38 = ufloat((4.4904e-3, 0))
#    s37 = ufloat((2.47163e-3, 0))
    s36 = ufloat(2.623e-5, 2.623e-5 * 0.5955)

    J = ufloat(1, 0)
    k4039 = 0
    ca3637 = 2.8e-4
    cl3638 = 0
    cl38 = s38

    ar39 = s39
    ar36 = s36 - ca3637 * s37 - cl3638 * cl38
    ar37 = s37
    ar38 = s38
#    k40 = ar39 * k4039
    ar40 = s40 - constants.atm4036_v * ar36
    args = calc_error_contrib(ar40, ar39, ar38, ar37, ar36,
                             s40, s39, s38, s37, s36, J, constants)
    for ni, ai, vi in zip(('ar40', 'ar39', 'ar38', 'ar37', 'ar36', 'J   ', 'LambdaK'),
                      args,
                      (s40, s39, s38, s37, s36, J, ufloat(1, 0))
                      ):
        print '{:<10s}'.format(ni), \
            '{:<10s}'.format('{:0.2f}'.format(vi.std_dev / vi.nominal_value * 100)), \
                ai * 100

