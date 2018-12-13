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
from traits.api import HasTraits, Str, Int, Enum, Property, Bool
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
import math


# ============= local library imports  ==========================


class LayoutItem(HasTraits):
    row = Int
    column = Int
    kind = Str
    identifier = Str


class FigureLayout(HasTraits):
    rows = Int(1)
    columns = Int(2)
    fixed = Enum('column', 'row', 'square')

    row_enabled = Property(depends_on='fixed')
    column_enabled = Property(depends_on='fixed')

    # def __init__(self, *args, **kw):
    #     super(FigureLayout, self).__init__(*args, **kw)
    #     self._fixed_changed()

    def _get_row_enabled(self):
        return self.fixed == 'row'

    def _get_column_enabled(self):
        return self.fixed == 'column'

    def __call__(self, n):
        return self.calculate(n)

    def calculate(self, n):
        r = self.rows
        c = self.columns

        if n <= 1:
            r = c = 1
        elif self.fixed == 'square':
            s = int(math.ceil(n ** 0.5))
            r, c = s, s

            while (r * c) - n > r:
                r -= 1

        else:
            while n > r * c:
                if self.fixed == 'column':
                    r += 1
                else:
                    c += 1

            while n < r or n < c:
                if self.fixed == 'column':
                    c -= 1
                    if c < 1:
                        c = 1
                        r -= 1
                else:
                    r -= 1
                    if r < 1:
                        r = 1
                        c -= 1

        return r, c

    def add_item(self, kind):
        self.items.append(LayoutItem(kind=kind))

    def traits_view(self):
        rc_grp = VGroup(HGroup(Item('rows',
                                    enabled_when='row_enabled'),
                               Item('columns',
                                    enabled_when='column_enabled'
                                    ),
                               Item('fixed')),
                        label='Layout', show_border=True)
        v = View(rc_grp, resizable=True)
        return v


if __name__ == '__main__':
    f = FigureLayout(rows=4, columns=1, fixed='square')
    f.calculate(5)
    # for i in range(20):
    #     print(i + 1, f(i + 1))
    # f.configure_traits()
# ============= EOF =============================================
