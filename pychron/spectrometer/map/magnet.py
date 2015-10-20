# ===============================================================================
# Copyright 2011 Jake Ross
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
from pyface.message_dialog import warning
from traits.api import Any, List
# ============= standard library imports ========================
from numpy import roots, array, polyval
import os
import time
# ============= local library imports  ==========================
from pychron.config_loadable import ConfigMixin
from pychron.core.helpers.filetools import pathtolist
from pychron.paths import paths
from pychron.spectrometer.base_magnet import BaseMagnet, get_float


class MapMagnet(BaseMagnet, ConfigMixin):
    """
    Abstraction for the MAP Magent
    """
    device = Any

    ranges = List

    reverse_coeffs = True

    def load(self):
        # load dac table
        self._load_dac_table()

    # ===============================================================================
    # positioning
    # ===============================================================================
    def set_range(self, r, verbose=False):
        """
        if float convert to integer and use as range.

        send B[r-1] ::

            # r = 6
            dev.tell('B5')

        :param r: float or int
        :param verbose:
        """
        dev = self.device
        if dev:
            r = int(r)
            dev.tell('B{}.'.format(r), verbose=verbose)

    def set_dac(self, v, verbose=False):
        """
        set the magnet dac voltage.

        set the range then send W[v] ::

            dev.tell('W4543.')

        :param v: v, dac voltage
        :param verbose:
        :return: bool, True if dac changed else False
        """
        r, coeffs = self._calculate_range(v)
        self.set_range(r)

        dac = int(polyval(coeffs, v))
        self.debug('requested={}. range={}, dac={}'.format(v, r, dac))

        dev = self.device
        if dev:
            dev.tell('W{}.'.format(dac), verbose=verbose)
            time.sleep(self.settling_time)

        change = v != self._dac
        self._dac = v
        self.dac_changed = True
        return change

    @get_float
    def read_dac(self):
        return self._dac

    # private
    def _load_dac_table(self):
        """
        the original MassSpec DAC file uses coefficients in the form of
        y = a + bx + cx^2

        pychron and numpy use the reverse.
        y = ax^2 + bx + c

        use the reverse_coeffs flag to convert massspec to pychron
        """
        path = os.path.join(paths.spectrometer_dir, 'map_magnet_dac.txt')
        if not os.path.isfile(path):
            warning(None, 'No magnet dac file located at {}'.format(path))
            return

        coeffs_list = pathtolist(path)
        for coeffs in coeffs_list:
            coeffs = map(float, coeffs.split(','))
            if self.reverse_coeffs:
                coeffs = coeffs[::-1]

            limits = self._calculate_range_limits(coeffs)
            self.ranges.append((limits, coeffs))

    def _calculate_range_limits(self, coeffs):
        limits = 0, 1

        mil = roots(coeffs)[1]
        coeffs = array(coeffs)
        coeffs[-1] -= 65535
        mal = roots(coeffs)[1]
        limits = mil, mal
        return limits

    def _calculate_range(self, dac):
        for i, ((mi, ma), coeffs) in enumerate(self.ranges):
            if ma > dac:
                return i, coeffs

# ============= EOF =============================================
