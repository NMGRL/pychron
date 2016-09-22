# ===============================================================================
# Copyright 2016 ross
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

from traitsui.api import View, Item, TabularEditor, HGroup, Controller
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================


class SampleHoleAdapter(TabularAdapter):
    columns = [('ID', 'id'),
               ('X', 'x'), ('Y', 'y'),
               ('XCor', 'x_cor'), ('YCor', 'y_cor'),
               ('Render', 'render')]

    def set_text(self, obj, trait, row, column, txt):
        if column in [3, 4]:
            try:
                txt = float(txt)
            except:
                txt = '0'

        setattr(getattr(obj, trait)[row], self.columns[column][1], txt)



class StageMapView(Controller):
    # ============= views ===========================================
    def traits_view(self):
        editor = TabularEditor(adapter=SampleHoleAdapter())
        v = View(
            HGroup(Item('clear_corrections', show_label=False)),
            HGroup(Item('g_shape'),
                   Item('g_dimension'), show_labels=False),

            Item('sample_holes',
                 show_label=False, editor=editor),
            height=500, width=250,
            resizable=True,
            title=self.model.name)
        return v

# ============= EOF =============================================
