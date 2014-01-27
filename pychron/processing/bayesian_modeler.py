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

#============= standard library imports ========================
from numpy import  vstack, histogram, array
from numpy.random import normal
from multiprocessing import Pool

from pylab import show, plot, axvline
import time
# import math
from numpy.core.fromnumeric import argmax
# from scipy.stats.stats import mode
# from numpy.lib.function_base import median
from pychron.core.time_series.time_series import smooth


#============= local library imports  ==========================

'''
    Bayesian stratigraphic modeler
    
    input:
        age, error[, strat_pos]
        
        if strat_pos neglected, list assumed to be in stratigraphic order
        where idx=0 == youngest idx=n == oldest
    
    execute a Monte Carlo simulation reject any run that violates strat order
    
    1.
            ok run A<B<C
            -----A------
                \
                 \
                 -----B------
                      \
                       \
              -----C------
              
    2. 
            invalid run A<B>C
            -----A------
                \
                 \
                 -----B------
                    /   
                  /     
              -----C------
    
'''

# def func(args):
#     _, in_ages = args
#     nages = _monte_carlo_step(in_ages)
#     return nages

def _monte_carlo_step(in_ages):
#     _, in_ages = args
    ages = _generate_ages(in_ages)
    if _is_valid(ages):
        return ages

def _generate_ages(in_ages):
    ages = array([normal(loc=ai, scale=ei)
                  for ai, ei in in_ages])
    return ages

def _is_valid(ages):
    a = ages[0]
    for ai in ages[1:]:
        if ai < a:
            return False
        a = ai
    else:
        return True

def age_generator(ages, n):
    i = 0
    while i < n:
        yield ages
        i += 1

class BayesianModeler2(HasTraits):
    def run(self):
        ages = [(1, 0.1), (1.5, 0.4), (1.7, 0.1), (1.8, 0.2), (2.1, 0.5)]
        pool = Pool(processes=10)
        n = 1e5


#         st = time.time()
#         aa = ((ai, ages) for ai in arange(n))
#         print 'a"', time.time() - st
        age_gen = age_generator(ages, n)
        st = time.time()
        results = pool.map(_monte_carlo_step, age_gen)
        print 'a', time.time() - st

        st = time.time()
        results = vstack((ri for ri in results if ri is not None))
        print 'b', time.time() - st

        for xx, (ai, ei)in zip(results.T, ages):
#             print 'dev ', abs(xx.mean() - ai) / ai * 100, abs(xx.std() - ei) / ei * 100
#             print xx

            f, v = histogram(xx, 40)
            lp = plot(v[:-1], f)[0]
            c = lp.get_color()

            nf = smooth(f, window='flat')
            plot(v[:-1], nf, c=c, ls='--', lw=2)

            axvline(ai, c=c)
#             print f, v
            idx = argmax(nf)
#             axvline(xx.mean(), c=c, ls='--')
            axvline(v[idx], c=c, ls='--')

        show()


if __name__ == '__main__':
    bm = BayesianModeler2()
    bm.run()

#     from pylab import linspace, plot, show
#     loc = 5
#     x = linspace(0, 1)
#     y = [normal(loc=loc) for i in x]

#     plot(x, normal(size=x.shape[0]))
#     show()


#============= EOF =============================================
