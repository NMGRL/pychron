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
from traits.api import HasTraits, Float, Property, List, Str
from traitsui.api import View, TabularEditor, UItem
# ============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter


class BlankDiffValue(HasTraits):
    name = Str
    left = Float
    right = Float
    diff = Property(depends_on='left, right')

    def _get_diff(self):
        return self.left - self.right


class BlankDiffAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Left', 'left'),
               ('Right', 'right'), ('Diff', 'diff')]


class BlankDiffView(HasTraits):
    values = List(BlankDiffValue)
    def set_values(self, ks, ls, rs):
        self.values=[BlankDiffValue(nam=n, left=l, right=r) for n,l,r in zip(ks, ls, rs)]

    def traits_view(self):
        v = View(UItem('values', editor=TabularEditor(adapter=BlankDiffAdapter(),
                                                      editable=False)))
        return v

#============= EOF =============================================



