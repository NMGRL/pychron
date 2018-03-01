# ===============================================================================
# Copyright 2017 ross
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
from __future__ import absolute_import
from pychron.spectrometer.isotopx.source.base import IsotopxSource
from six.moves import map


class NGXSource(IsotopxSource):
    def set_hv(self, new):
        self.ask('SSO IE, {}'.format(new))

    def read_hv(self):
        resp = self.ask('GSO IE', verbose=True)
        actual = 0
        if ',' in resp:
            setpoint, actual = list(map(float, resp.split(',')))
        return actual

    def read_trap_current(self):
        resp = self.ask('GSO TC')
        actual = 0
        if ',' in resp:
            setpoint, actual = list(map(float, resp.split(',')))
        return actual

    def read_emission(self):
        resp = self.ask('GSO EC')
        actual = 0
        if ',' in resp:
            setpoint, actual = list(map(float, resp.split(',')))
        return actual
        # return self.ask('GSO ')
# ============= EOF =============================================
