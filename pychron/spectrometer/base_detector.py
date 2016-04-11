# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import HasTraits, Str, Int, Bool, Float, Property, \
    Color, Array

# ============= standard library imports ========================
from numpy import array, hstack


# ============= local library imports  ==========================


class BaseDetector(HasTraits):
    name = Str
    kind = Str

    intensity = Str
    std = Str
    intensities = Array
    nstd = Int(10)
    active = Bool(True)
    gain = Float

    color = Color
    series_id = Int
    isotope = Str

    isotopes = Property

    index = Int

    def set_intensity(self, v):
        if v is not None:
            n = self.nstd
            if self.intensities is None:
                self.intensities = array([])

            self.intensities = hstack((self.intensities[-n:], [v]))
            self.std = '{:0.5f}'.format(self.intensities.std())
            self.intensity = '{:0.5f}'.format(v)

    @property
    def gain_outdated(self):
        return abs(self.get_gain() - self.gain) < 1e-7

    def get_gain(self):
        v = self._read_gain()
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = 0
        self.gain = v
        return v

    def set_gain(self):
        self._set_gain()

    # private
    def _set_gain(self):
        raise NotImplementedError

    def _read_gain(self):
        raise NotImplementedError

    def _get_isotopes(self):
        molweights = self.spectrometer.molecular_weights
        return sorted(molweights.keys(), key=lambda x: int(x[2:]))

    def __repr__(self):
        return 'Detector({})'.format(self.name)

# ============= EOF =============================================
