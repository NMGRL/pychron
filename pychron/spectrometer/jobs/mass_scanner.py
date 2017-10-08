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
from traits.api import Float
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.spectrometer.jobs.base_scanner import BaseScanner


class MassScanner(BaseScanner):
    start_mass = Float
    stop_mass = Float

    pattributes = ('step', 'start_mass', 'stop_mass')

    # private
    def _setup_graph(self, graph, plot):
        graph.new_series()
        graph.set_x_title('Mass (AMU)')
        graph.set_y_title('Intensity')

    # scan methods
    def _do_step(self, magnet, step):
        magnet.mass = step

    def _get_limits(self):
        return self.start_mass, self.stop_mass

    def _calculate_steps(self, l, h):
        self.debug('scan limits: start_mass={}, stop_mass={}'.format(l, h))
        step_size = self.step

        if l > h:
            step_size *= -1

        si = l
        while 1:
            yield si
            si += step_size
            if si > h:
                yield h
                raise StopIteration

# ============= EOF =============================================
