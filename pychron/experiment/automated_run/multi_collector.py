# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
import time

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.automated_run.data_collector import DataCollector


class MultiCollector(DataCollector):
    def _iter_hook(self, con, i):
        if i % 50 == 0:
            self.info('collecting point {}'.format(i))
            #                mem_log('point {}'.format(i), verbose=True)

        # get the data
        try:
            data = self._get_data()
        except (AttributeError, TypeError, ValueError), e:
            self.debug('failed getting data {}'.format(e))
            return

        con.add_consumable((time.time() - self.starttime, data, i))
        return True

    def _iter_step(self, data):
        x, data, i = data
        #print 'iterstep', x,data, i

        # save the data
        self._save_data(x, *data)
        # plot the data
        self.plot_data(i, x, *data)

        # ============= EOF =============================================
