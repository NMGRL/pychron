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
from traits.api import HasTraits, Str, Color, List, Property, Bool
from traitsui.api import View, Item
#============= standard library imports ========================
#============= local library imports  ==========================
class Layer(HasTraits):
    name = Str
    color = Color
    components = List
    label = Property(depends_on='name')
    visible = Bool(True)

    def destroy(self):
        del self.components

    def pop_item(self, idx, klass=None):
        if self.components:
            if klass is not None:
                if isinstance(self.components[idx], klass):
                    self.components.pop(idx)
            else:
                self.components.pop(idx)

    def remove_klass(self, k):
        if self.components:
            for c in self.components:
                if isinstance(c, k):
                    self.components.remove(c)

    def remove_item(self, v):
        if self.components:
            self.components.remove(v)

    def add_item(self, v):
        self.components.append(v)

    def _get_label(self):
        return 'Layer {}'.format(self.name)

    def traits_view(self):
        v = View(Item('name'),
                 Item('color'),
                 Item('visible')
                 )
        return v
# ============= EOF =============================================
