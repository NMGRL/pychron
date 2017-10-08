# ===============================================================================
# Copyright 2016 ross
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
from pychron.experiment.automated_run.automated_run import AutomatedRun


class VolumeCalculationRun(AutomatedRun):
    def py_split(self, eqtime, inlet, outlet):
        self._equilibrate(eqtime, inlet, outlet)

    def calculate_volume(self, s1, s2, refvol):
        """
        s2/s1 = vol/(vol+refvol)

        vol = (refvol * s2 / s1) / (1 - s2 / s1)

        :param s1:
        :param s2:
        :param refvol:
        :return:
        """
        s1, s2, refvol = float(s1), float(s2), float(refvol)
        return (refvol * s2 / s1) / (1 - s2 / s1)


if __name__ == '__main__':
    v2 = 500

    s1 = 100.
    s2 = 1.

    # s2/s1 = v1/(v1+v2)
    #
    #
    # s2/s1*(v1+v2) = v1
    # v2*s2/s1 = v1 - s2/s1 *v1
    # v2*s2/s1 = v1(1-s2/s1)
    v1 = (v2 * s2 / s1) / (1 - s2 / s1)
    print v1
# ============= EOF =============================================
