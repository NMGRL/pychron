from numpy import array


def pearson(expected=False):
    xs = [0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
    ys = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]

    wxs = array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1])
    wys = array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500])
    solutions = dict(reed=dict(slope=-0.4805,
                               slope_err=0.0702,
                               intercept=5.4799,
                               intercept_err=0.3555,
                               mswd=1.4832
    ))
    if expected:
        if not expected in solutions:
            v = ','.join(solutions.keys())
            raise AttributeError('invalid expected value {}. use "{}"'.format(expected, v))
            return
        return solutions[expected]

    return xs, ys, wxs, wys

