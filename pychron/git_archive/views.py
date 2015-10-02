# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, Property, Any
from traitsui.api import View, UItem


# ============= standard library imports ========================
# ============= local library imports  ==========================


class NewBranchView(HasTraits):
    name = Property(depends_on='_name')
    branches = Any
    _name = Str

    def traits_view(self):
        v = View(UItem('name'),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 width=200,
                 title='New Branch')
        return v

    def _get_name(self):
        return self._name

    def _set_name(self, v):
        self._name = v

    def _validate_name(self, v):
        if v not in self.branches:
            if ' ' not in v:
                return v

# ============= EOF =============================================
