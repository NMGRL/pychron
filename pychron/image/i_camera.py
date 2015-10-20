# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Interface
# ============= standard library imports ========================
# ============= local library imports  ==========================


class ICamera(Interface):
    def retrieve_frame(self):
        pass

    def render_frame(self, src=None):
        pass

    def open(self, owner=None):
        pass

    def save(self, p, src=None):
        pass

    def get_image_data(self, size):
        pass
# ============= EOF =============================================



