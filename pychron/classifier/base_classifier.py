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
import os

from numpy import vstack, hstack, array
from sklearn.externals import joblib
from sklearn.neighbors import KNeighborsClassifier

# ============= local library imports  ==========================
from pychron.paths import paths


class BaseClassifier(object):
    _clf = None

    def fit(self, x, y):
        raise NotImplementedError

    def predict(self):
        raise NotImplementedError

    def add_training_data(self, samples, klasses):
        self.load()
        if not self._clf:
            self._clf = self.classifier_factory()
            x = array(samples[:1])
            y = array(klasses[:1])
            samples = samples[1:]
            klasses = klasses[1:]
        else:
            x = self._clf._fit_X
            y = self._clf._y

        for sample, klass in zip(samples, klasses):
            x = vstack((x, sample))
            y = hstack((y, [klass]))

        self.fit(x, y)

    def classifier_factory(self, klass=None, *args, **kw):
        if klass is None:
            klass = KNeighborsClassifier

        return klass(*args, **kw)

    def load(self):
        p = self.persistence_path
        if os.path.isfile(p):
            self._clf = joblib.load(p)

    def dump(self):
        joblib.dump(self._clf, self.persistence_path)

    @property
    def persistence_path(self):
        return os.path.join(paths.hidden_dir, self._persistence_name)
# ============= EOF =============================================



