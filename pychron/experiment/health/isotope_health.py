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
# ============= local library imports  ==========================
from pychron.experiment.classifier.isotope_classifier import IsotopeClassifier, make_sample
from pychron.loggable import Loggable


class IsotopeHealth(Loggable):
    def __init__(self, *args, **kw):
        super(IsotopeHealth, self).__init__(*args, **kw)
        self._clf = IsotopeClassifier()

    def check(self, iso, tol=0.5):
        k, p = self._clf.predict(make_sample(iso))
        self.debug('check {} {} {}'.format(iso.name, k, p))
        if k is not None:
            if not k and p > tol:
                self.info('Isotope {} classified bad: {}<{}'.format(iso.name, p, tol))
                return True
# ============= EOF =============================================



