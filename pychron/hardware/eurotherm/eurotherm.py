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



"""
Eurotherm 2000 series device abstraction

see 2000 Series Communications Manual - Issue 2
http://eurotherm.com/document-library/?ignoreeveryonegroup=0&assetdetesctl1390419=1833&search=2000+series&searchcontent=0

"""

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.eurotherm.base import BaseEurotherm


class Eurotherm(BaseEurotherm, CoreDevice):
    """
    """


# ============= EOF ====================================
# def __init__(self, *args, **kw):
#        super(Eurotherm, self).__init__(*args, **kw)
#
#        if self.setpoint_recording:
#            self._setup_setpoint_recording()
#
#    def _setup_setpoint_recording(self):
#        root = os.path.join(paths.data_dir, 'streams')
#        base = 'history'
#
#
#        self.setpoint_history_path = p = unique_path(root, base)
#        f = open(p, 'w')
#        f.write('timestamp    setpoint\n')
#        f.close()
#
#    def record_setpoint_history(self, v):
#        f = open(self.setpoint_history_path, 'a')
#        ti = time.time()
#        millisecs = math.modf(ti)[0] * 1000
#        tstamp = '%s +%0.5f' % (time.strftime("%Y-%m-%d %H:%M:%S"), millisecs)
#        line = '%s %s\n' % (tstamp, v)
#        f.write(line)
#        f.close()
