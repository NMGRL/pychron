import csv

from numpy import zeros_like, zeros, vstack, percentile, array, ones, random
from scipy.stats import norm
from pylab import hist, show

from pychron.core.regression.flux_regressor import PlaneFluxRegressor


random.seed(123456)


def test(ntrials):
    g = norm()
    e = 1
    ee = 1 + 3 * g.rvs(ntrials)
    hist(ee, bins=50)
    print percentile(ee, [15.87, 84.13])
    print array(percentile(ee, [15.87, 84.13])).mean()
    show()


def monte_carlo_error_estimation(reg, nominal_ys, pts, ntrials=100):
    # oys=reg.ys
    # nominal_ys=reg.predict(pts)
    g = norm()

    exog = reg.get_exog(pts)
    # res=zeros(ntrials, len(pts))
    for i in xrange(ntrials):
        # print 'trial', i, reg.ys
        devs = perturb(reg, exog, nominal_ys, g)
        if i == 0:
            res = devs
        else:
            res = vstack((res, devs))

    # print res
    # res=res.T

    # hist(res[:,0], bins=50)
    # show()
    # return 0,0
    ret = zeros(len(pts))
    for i, po in enumerate(pts):
        # r=res[i]**0.5
        r = res[i]
        # r.sort()
        ps = abs(array(percentile(r, [15.87, 84.13])))
        ret[i] = ps.mean()

    # reg.ys=oys
    # reg.calculate()
    return ret


def perturb(reg, exog, nominal_ys, g):
    ys = reg.ys
    yserr = reg.yserr
    yp = zeros_like(ys)

    for i, (y, e, d) in enumerate(zip(ys, yserr, g.rvs(len(ys)))):
        yp[i] = y + e * d

    # reg.ys=yp
    # reg.fast_calculate(filtering=True)
    # pys=reg.fast_predict(pts)
    pys = reg.fast_predict(yp, exog)
    return nominal_ys - pys


class TestReg(object):
    ys = None

    def predict(self, x):
        return ones(len(x)) * self.ys.mean()

    def calculate(self, *args, **kw):
        pass
        # return self.ys.mean()


if __name__ == '__main__':

    # test(100000)


    x = []
    y = []
    j = []
    je = []
    p = '/Users/ross/Sandbox/monte_carlo.txt'
    with open(p, 'r') as fp:
        reader = csv.reader(fp)
        for l in reader:
            if not l[0][0] == '#':
                a, b, c, d = map(float, l)
                x.append(a)
                y.append(b)
                j.append(c)
                je.append(d)
                # break

    x = array(x)
    y = array(y)
    xy = vstack((x, y)).T

    j = array(j)
    # reg = PlaneFluxRegressor(xs=xy, ys=j, yserr=je, error_calc_type='SD')
    # reg.calculate()
    # b=reg.predict_error([[(0,0.85)]])
    # a=reg.predict([(0,0.85)])
    # print a, b, b/a*100
    # print a/j*100
    # print b
    # print c
    # for n in (10, 20, 100, 1000):
    for n in (10, 100, 1000, 10000):
        # for n in (10, 20, 100, 1000):
        reg = PlaneFluxRegressor(xs=xy, ys=j, yserr=je, error_calc_type='SD')
        # reg=TestReg()
        # reg.clean_ys=j
        # reg.yserr=je
        # reg.ys=j
        reg.calculate(filtering=True)
        errors = monte_carlo_error_estimation(reg, reg.predict(xy), xy, ntrials=n)
        # timethis(monte_carlo_error_estimation, args=(reg, xy),
        #          kwargs=dict(ntrials=n))
        # nom, errors=monte_carlo_error_estimation(reg, xy, ntrials=n)
        print n, errors

'''[ 0.20522372]'''

'''
100 [  3.37982191e-06   7.83273113e-06   7.08803041e-06   1.53090975e-06]
100000 [  6.59271268e-05   7.63233600e-05   5.40135848e-05   1.05373392e-05]
'''
'''
10 [  9.56261659e-07   1.48631097e-06   5.42786007e-06   6.93392815e-06]
100 [  1.12917561e-06   7.06353138e-07   1.48474741e-06   4.56634915e-06]
1000 [  2.01720472e-06   3.20987783e-06   6.51463730e-06   1.83773091e-06]
10000 [  1.23267621e-06   9.75810804e-07   1.68391084e-06   1.33871430e-06]
'''