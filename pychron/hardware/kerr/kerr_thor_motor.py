# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================

# =============enthought library imports=======================
# =============standard library imports ========================
# =============local library imports  ==========================
from kerr_motor import KerrMotor


class KerrThorMotor(KerrMotor):
    """
    """

    def _build_io(self):
        return '1800'

    def _build_gains(self):
        return 'F6B0042003F401B004FF006400010101'

    def _wait_for_home(self, progress=None):
        """
        thor motor does not have limit switches so cannot use HOME_IN_PROG bit of the Status Byte

        Instead wait untill 4 successive read positions return the same value
        """
        self.block(4, progress=progress, homing=True)


# =============EOF-==============================================
