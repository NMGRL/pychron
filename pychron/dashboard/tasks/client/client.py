#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
import pickle
import time
from traits.api import HasTraits, List, Float, Property, Str, Bool

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import convert_timestamp
from pychron.messaging.notify.subscriber import Subscriber

CONFIG = '''(lp0
ctraits.traits
__newobj__
p1
(csrc.dashboard.tasks.server.device
ProcessValue
p2
tp3
Rp4
(dp5
S'__traits_version__'
p6
S'4.3.0'
p7
sS'name'
p8
S'IG_pressure'
p9
sS'func_name'
p10
S'get_ion_pressure'
p11
sS'enabled'
p12
I01
sS'period'
p13
S'on_change'
p14
sS'tag'
p15
S'<BoneGauges,IG_pressure>'
p16
sS'last_value'
p17
F0.0
sS'last_time'
p18
F0.0
sbag1
(g2
tp19
Rp20
(dp21
g6
g7
sg8
S'CG1_pressure'
p22
sg10
S'get_convectron_a_pressure'
p23
sg12
I01
sg13
F2.0
sg15
S'<BoneGauges,CG1_pressure>'
p24
sg17
F0.0
sg18
F0.0
sbag1
(g2
tp25
Rp26
(dp27
g6
g7
sg8
S'temperature'
p28
sg10
S'get_temperature'
p29
sg12
I01
sg13
F2.0
sg15
S'<EnvironmentalMonitor,temperature>'
p30
sg17
F0.0
sg18
F0.0
sbag1
(g2
tp31
Rp32
(dp33
g6
g7
sg8
S'humidity'
p34
sg10
S'get_humidity'
p35
sg12
I01
sg13
F10.0
sg15
S'<EnvironmentalMonitor,humidity>'
p36
sg17
F0.0
sg18
F0.0
sba.'''


class DashboardValue(HasTraits):
    name = Str
    value = Float
    last_time = Float
    last_time_str = Property(depends_on='last_time')
    timed_out = Bool

    def _get_last_time_str(self):
        r = ''
        if self.last_time:
            r = convert_timestamp(self.last_time)

        return r

    def handle_update(self, new):
        if new == 'timeout':
            if not self.timed_out:
                self.timed_out = True
                self.last_time = time.time()

        else:
            self.value = float(new)
            self.last_time = time.time()


class DashboardClient(Subscriber):
    values = List

    def load_configuration(self):
        config=self.request('config')
        #config = CONFIG
        if config:
            self._load_configuration(config)

    def _load_configuration(self, config):
        try:
            d = pickle.loads(config)
        except (pickle.PickleError, ImportError):
            self.warning('Could not load configuration: {}'.format(config))
            return

        vs = []
        for di in d:
            pv = DashboardValue(name=di.name)
            vs.append(pv)
            self.values = vs
            self.subscribe(di.tag, pv.handle_update, verbose=True)

#============= EOF =============================================
