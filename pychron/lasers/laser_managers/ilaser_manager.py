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
from pychron.lasers.laser_managers.extraction_device import IExtractionDevice
#============= standard library imports ========================
#============= local library imports  ==========================

class ILaserManager(IExtractionDevice):
    def trace_path(self, *args, **kw):
        pass
    def drill_point(self, *args, **kw):
        pass
    def take_snapshot(self, *args, **kw):
        pass
#    def extract(self, *args, **kw):
#        pass
#    def end_extract(self, *args, **kw):
#        pass
#    def move_to_position(self, *args, **kw):
#        pass
# ============= EOF =============================================
