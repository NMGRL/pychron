# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Str, Int, Property

# ============= standard library imports ========================
# ============= local library imports  ==========================


class ConnectionSpec(HasTraits):
    host = Str('localhost')
    port = Int(8100)
    system_name = Str('jan')
    url = Property

    def _get_url(self):
        return '{}:{}'.format(self.host, self.port)

    # def traits_view(self):
    # return View(VGroup(VGroup(Item('host'),
    #                               Item('port'),
    #                               Item('system_name',
    #                                    label='Name'))))

    def __repr__(self):
        return self.system_name
        # ============= EOF =============================================
