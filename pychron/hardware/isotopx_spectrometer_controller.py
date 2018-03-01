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


# ============= enthought library imports =======================
# from traits.api import HasTraits, on_trait_change, Str, Int, Float, Button
# from traitsui.api import View, Item, Group, HGroup, VGroup

# ============= standard library imports ========================
from __future__ import absolute_import
from __future__ import print_function
from traits.api import Str, HasTraits
# ============= local library imports  ==========================
from apptools.preferences.preference_binding import bind_preference

from pychron.hardware.core.core_device import CoreDevice


class NGXController(CoreDevice):
    username = Str('')
    password = Str('')

    def set(self, *args, **kw):
        print('nacsd', args, kw)
        return HasTraits.set(self, *args, **kw)

    def initialize(self, *args, **kw):
        ret = super(NGXController, self).initialize(*args, **kw)
        if ret:
            resp = self.read()

            bind_preference(self, 'username', 'pychron.spectrometer.ngx.username')
            bind_preference(self, 'password', 'pychron.spectrometer.ngx.password')

            if resp:
                self.info('NGX-{}'.format(resp))
                self.ask('Login {},{}'.format(self.username, self.password))

            return True


# ============= EOF =============================================
