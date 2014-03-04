import numpy as np

from numpy import random


def pearson(expected=False):
    xs = [0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
    ys = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]

    wxs = np.array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1])
    wys = np.array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500])
    solutions = dict(reed=dict(slope=-0.4805,
                               slope_err=0.0702,
                               intercept=5.4799,
                               intercept_err=0.3555,
                               mswd=1.4832))
    if expected:
        if not expected in solutions:
            v = ','.join(solutions.keys())
            raise AttributeError('invalid expected value {}. use "{}"'.format(expected, v))

        return solutions[expected]

    return xs, ys, wxs, wys


def mean_data(scalar=5, std=1.5, n=1000):
    rs = random.RandomState(123456)

    xs = np.linspace(0, 100, n)
    ys = rs.normal(loc=scalar, scale=std, size=n)
    solution = {'mean': scalar,
                'std': std,
                'n': n}
    # rv=stats.norm(scalar,std)
    # ys=rv.rvs(size=n)


    # solution={'mean':rv.mean(),
    #           'std':rv.std(),
    #           'n': n}

    return xs, ys, solution


def ols_data():
    """
     draper and smith p.8
    """

    xs = [35.3, 29.7, 30.8, 58.8, 61.4, 71.3, 74.4, 76.7, 70.7, 57.5,
          46.4, 28.9, 28.1, 39.1, 46.8, 48.5, 59.3, 70, 70, 74.5, 72.1,
          58.1, 44.6, 33.4, 28.6]
    ys = [10.98, 11.13, 12.51, 8.4, 9.27, 8.73, 6.36, 8.50,
          7.82, 9.14, 8.24, 12.19, 11.88, 9.57, 10.94, 9.58,
          10.09, 8.11, 6.83, 8.88, 7.68, 8.47, 8.86, 10.36, 11.08]


    # self.Xk = 28.6
    # self.ypred_k = 0.3091
    solution = {'slope': -0.0798,
                'y_intercept': 13.623,
                'n': len(xs),
                'pred_x': 28.6,
                'pred_error': 0.309}

    return xs, ys, solution


def filter_data():
    xs = [35.3, 29.7, 30.8, 58.8, 61.4, 71.3, 74.4, 76.7, 70.7, 57.5,
          46.4, 28.9, 28.1, 39.1, 46.8, 48.5, 59.3, 70, 70, 74.5, 72.1,
          58.1, 44.6, 33.4, 28.6]

    ys = [10.98, 11.13, 12.51, 8.4, 9.27, 8.73, 6.36, 8.50,
          7.82, 9.14, 8.24, 12.19, 11.88, 9.57, 10.94, 9.58,
          10.09, 8.11, 6.83, 8.88, 7.68, 8.47, 8.86, 10.36, 11.08]

    xs.append(10)
    ys.append(1000)

    # self.Xk = 28.6
    # self.ypred_k = 0.3091
    solution = {'slope': -0.0798,
                'y_intercept': 13.623,
                'n': len(xs) - 1,
                'pred_x': 28.6,
                'pred_error': 0.309}

    return xs, ys, solution


def weighted_mean_data():
    """http://en.wikipedia.org/wiki/Weighted_mean#Example"""
    xs = [1, 1]
    ys = [80, 90]

    yserr = [1 / 20. ** 0.5,
             1 / 30. ** 0.5]

    # xs=[1,2,3,4,5,6]
    # ys=[1,1,1,1,1,2]
    # yserr=[0.1,1,1,1,1]

    solution = {'mean': 85.999999999999986, 'n': len(ys)}
    return xs, ys, yserr, solution