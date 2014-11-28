'''
    National Control Devices
    
   http://www.controlanything.com/ 
   
   The Complete ProXR Command Set:
   http://www.controlanything.com/Relay/Device/A0010
   http://assets.controlanything.com/manuals/ProXR.pdf
'''
# ===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
from pychron.hardware.core.core_device import CoreDevice
#============= standard library imports ========================
#============= local library imports  ==========================

class NCDDevice(CoreDevice):
    def initialize(self, *args, **kw):
        super(NCDDevice, self).initialize(*args, **kw)
        self._communicator.write_terminator = None
        return True

    def _make_cmdstr(self, *args):
#        formatter = lambda x:'{:02X}'.format
        formatter = lambda x:chr(x)
        return ''.join(map(formatter, args))

# ============= EOF =============================================
