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
from traitsui.api import View, Item, HGroup, VGroup
from traitsui.item import Label

from pychron.core.ui.qt.custom_label_editor import CustomLabel


# ============= standard library imports ========================


# ============= local library imports  ==========================


class LayoutItem(HasTraits):
    row = Int
    column = Int
    kind = Str
    identifier = Str


def filled_grid(n):
    """

    n = 2  1x2
    0 1

    n = 3  2x2
    0 1
    2 x

    n = 4  2x2
    0 1
    2 3

    n = 5  2x3
    0 1 2
    3 4 x

    n = 6 2x3

    n=7 3x3

    :param n:
    :return:
    """

    i = 0
    r, c = 1, 1
    while r * c < n:
        if i % 2:
            r += 1
        else:
            c += 1

        i += 1

    return r, c


class FigureLayout(HasTraits):
    rows = Int(1)
    columns = Int(2)
    fixed = Enum("column", "row", "filled_grid")
    fixed_width = Int(0)
    fixed_height = Int(0)

    stretch_vertical = Bool
    row_enabled = Property(depends_on="fixed")
    column_enabled = Property(depends_on="fixed")

    remake_label = Str(
        "You must remake the figure if you edit Fixed Width or Fixed Height. The figure "
        "will not automatically resize"
    )
    # def __init__(self, *args, **kw):
    #     super(FigureLayout, self).__init__(*args, **kw)
    #     self._fixed_changed()

    def _get_row_enabled(self):
        return self.fixed == "row"

    def _get_column_enabled(self):
        return self.fixed == "column"

    def __call__(self, n):
        return self.calculate(n)

    def calculate(self, n):
        r = self.rows
        c = self.columns

        if n <= 1:
            r = c = 1
        elif self.fixed == "filled_grid":
            r, c = filled_grid(n)
        else:
            while n > r * c:
                if self.fixed == "column":
                    r += 1
                else:
                    c += 1

            while n < r or n < c:
                if self.fixed == "column":
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
        rc_grp = VGroup(
            CustomLabel("remake_label", color="red"),
            HGroup(
                Item(
                    "fixed_width",
                    tooltip="You must remake the figure if you edit this value. The figure "
                    "will not automatically resize",
                ),
                Item(
                    "fixed_height",
                    tooltip="You must remake the figure if you edit this value. The figure "
                    "will not automatically resize",
                ),
            ),
            HGroup(
                Item("rows", enabled_when="row_enabled"),
                Item("columns", enabled_when="column_enabled"),
                Item("fixed"),
                # enabled_when="not fixed_width",
            ),
            # HGroup(
            #     Item(
            #         "stretch_vertical",
            #         label="Vertical Stretch",
            #         tooltip="Resize the main plot to fill the vertical space. "
            #         "Best used when only using either a single figure or a single row of figures",
            #     )
            # ),
            label="Layout",
            show_border=True,
        )
        v = View(rc_grp, resizable=True)
        return v


if __name__ == "__main__":
    # f = FigureLayout(rows=4, columns=1, fixed='square')
    # f.calculate(5)
    # for i in range(20):
    #     print(i + 1, f(i + 1))
    # f.configure_traits()

    for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        print(i, filled_grid(i))

# ============= EOF =============================================
