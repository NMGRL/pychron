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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.preference_binding import bind_preference, color_bind_preference


class PreferenceMixin(object):
    def _preference_binder(self, prefid, attrs, mod=None, obj=None):
        if mod is None:
            mod=bind_preference
        elif mod=='color':
            mod=color_bind_preference

        if obj is None:
            obj = self

        for attr in attrs:
            mod(obj, attr, '{}.{}'.format(prefid, attr))

#============= EOF =============================================



