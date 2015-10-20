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
from traits.api import HasTraits, Float, Property, List, Str, Int, Instance
from traitsui.api import View, TabularEditor, UItem, VGroup, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
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

    name_width = Int(80)
    left_width = Int(200)
    right_width = Int(200)
    diff_width = Int(160)

    def get_bg_color(self, object, trait, row, column=0):
        color = 'white'
        if abs(self.item.diff) > 1e-7:
            color = '#FF9999'
        return color


class BlankDiffView(HasTraits):
    values = List(BlankDiffValue)
    adapter=Instance(BlankDiffAdapter, ())
    left_summary = Str
    right_summary =Str

    def load(self, left, right):
        values=[]
        names = []
        for liso in left.isotopes:
            ison=liso.isotope
            isoerr='{}Err'.format(ison)

            riso=next((ri for ri in right.isotopes if ri.isotope==ison), None)
            rv,re = (0,0) if not riso else (riso.value, riso.error)

            values.append(BlankDiffValue(name=ison, left=liso.value, right=rv))
            values.append(BlankDiffValue(name=isoerr, left=liso.error, right=re))
            names.append(ison)

        for riso in right.isotopes:
            ison=riso.isotope
            if ison in names:
                continue

            isoerr='{}Err'.format(ison)
            liso=next((li for li in left.isotopes if li.isotope==ison), None)
            lv,le = (0,0) if not liso else (liso.value, liso.error)

            values.append(BlankDiffValue(name=ison, left=lv, right=riso.value))
            values.append(BlankDiffValue(name=isoerr, left=le, right=riso.error))

        values.append(BlankDiffValue(name='Age', left=left.age, right=right.age))
        self.values=values
        ln=left.create_date.strftime('%m/%d/%Y %H:%M')
        rn=right.create_date.strftime('%m/%d/%Y %H:%M')

        self.adapter.columns[1]=('Left ({})'.format(ln), 'left')
        self.adapter.columns[2]=('Right ({})'.format(rn), 'right')

        self.left_summary=left.summary
        self.right_summary=right.summary


    def traits_view(self):
        v = View(VGroup(
            VGroup(Item('left_summary', label='Left', style='readonly'),
                    Item('right_summary', label='Right', style='readonly')),
            UItem('values', editor=TabularEditor(adapter=self.adapter,
                                                      editable=False))),
                 kind='modal',
                 title='Blank Diff',
                 width=700,
                 height=400,
                 resizable=True)
        return v

# ============= EOF =============================================



