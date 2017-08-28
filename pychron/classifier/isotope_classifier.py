# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
from numpy import ones, vstack, zeros, hstack
from numpy.random import random

# ============= local library imports  ==========================
from pychron.classifier.base_classifier import BaseClassifier


def make_sample(iso):
    # print 'make sample {} {} {}'.format(iso.mass, iso.n, iso.intercept_percent_error)
    return iso.mass, iso.n, iso.value, iso.intercept_percent_error, iso.slope(), iso.standard_fit_error(), \
           iso.noutliers()


class IsotopeClassifier(BaseClassifier):
    """
    klasses:
            0= Bad
            1= Good
    """
    _clf = None
    _persistence_name = 'clf.isotope.p'

    def classifier_factory(self, klass=None, *args, **kw):
        kw['n_neighbors'] = 3
        return super(IsotopeClassifier, self).classifier_factory(klass=klass, *args, **kw)

    def predict_isotope(self, iso):
        return self.predict(make_sample(iso))

    def add_isotopes(self, isos, klasses):
        samples = [make_sample(iso) for iso in isos]
        self.add_training_data(samples, klasses)

    def fit(self, x, y):
        """
        x: 2d array, [n_samples, n_features]
        y: 1d array, [n_samples]. class for each sample

        :param x:
        :param y:
        :return:
        """
        if not self._clf:
            self._clf = self.classifier_factory()

        self._clf.fit(x, y)

    def predict(self, x):
        if self._clf is None:
            self.load()

        klass = None
        prob = 0
        print x
        if self._clf:
            klass = int(self._clf.predict(x)[0])
            prob = self._clf.predict_proba(x)[0][klass]

        return klass, prob


if __name__ == '__main__':
    ic = IsotopeClassifier()

    nsamples = 20
    err = random(size=nsamples)
    npts = ones(nsamples) * 100 + random(size=nsamples) * 10
    xgood = vstack((npts, err)).T
    ygood = ones(nsamples)

    err = 1 + random(size=nsamples) * 10
    npts = ones(nsamples) * 100 + random(size=nsamples)
    xbad = vstack((npts, err)).T
    ybad = zeros(nsamples)

    npts = ones(nsamples) * 10 + random(size=nsamples)
    err = random(size=nsamples) * 10
    xbad2 = vstack((npts, err)).T

    xx = vstack((xgood, xbad, xbad2))
    yy = hstack((ygood, ybad, ybad))
    ic.fit(xx, yy)

    for pt in ([100, 0.11], [100, 11], [10, 1], [75, 0.5]):
        k = ic.predict(pt)
        print pt, k
        # print pt, ic.classify(pt)

        # ax = plt.subplot(1, 1, 1)
        # ax.scatter(x[:, 0], x[:, 1], c=y)
        # plt.show()
# ============= EOF =============================================
