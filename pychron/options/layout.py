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
from __future__ import absolute_import
from __future__ import print_function
import math
from traits.api import HasTraits, Str, Int, Enum
from six.moves import range


# ============= standard library imports ========================
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

    def __call__(self, n):
        return self.calculate(n)

    def calculate(self, n):
        r = self.rows
        c = self.columns

        if n == 1:
            r = c = 1
        elif self.fixed == 'square':
            s = int(math.ceil(n ** 0.5))
            r, c = s, s
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


if __name__ == '__main__':
    f = FigureLayout(rows=4, columns=1, fixed='square')
    for i in range(20):
        print(i + 1, f(i + 1))
# ============= EOF =============================================
