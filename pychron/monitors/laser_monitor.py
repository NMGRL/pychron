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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Float, Int

#============= standard library imports ========================
import time
#============= local library imports  ==========================
from monitor import Monitor

# NFAILURES = 3
# NTRIES = 3
class LaserMonitor(Monitor):
    """
    """
    max_duration = Float(60)  # in minutes
    gntries = 0

    # if max_duration_period is 10 check the max_duration every 10th cycle.
    max_duration_period = Int(10)
    _md_cnt = 0

    def _load_hook(self, config):
        """
        """

        self.set_attribute(config, 'max_duration',
                           'General', 'max_duration', cast='float', optional=True)

        self.set_attribute(config, 'max_duration_period',
                           'General', 'max_duration_period', cast='float', optional=True)

        return True

    def _fcheck_duration(self):
        """
        """
        if self._md_cnt % self.max_duration_period == 0:
            self._check_duration()

        self._md_cnt += 1
        if self._md_cnt > 100:
            self._md_cnt = 1

    def _check_duration(self, verbose=True):
        """
        """
        # check max duration
        manager = self.manager
        if verbose:
            self.info('Check lasing duration')

        # max duration in mins convert to secs for comparison
        if time.time() - self.start_time > self.max_duration * 60.0:
            msg = 'Max duration {} (min) exceeded'.format(self.max_duration)
            self.warning(msg)
            manager.emergency_shutoff(reason=msg)


#============= EOF ====================================
