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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traits.api import HasTraits, Dict, Str, List, Float

MARKS = {'1': '100 000 000',
         '2': '110 000 000',
         '3': '110 100 000',
         '4': '100 110 000',
         '5': '110 010 000',
         '6': '111 010 000',
         '7': '110 110 000',
         'UL': '100 011 010',
         'LR': '111 001 000',}

KEYS = {'1': '3:1',
        '2': '4:2',
        '3': '5:3',
        '4': '6:4',
        '5': '7:5',
        '6': '8:6',
        '7': '9:7',
        'UL': '1:UL',
        'LR': '2:LR'}


class ReferenceMarks(HasTraits):
    marks = Dict(MARKS)
    mark = Str
    mark_display = Str
    mark_ids = Dict(KEYS)
    spacing = Float(0.75)
    _made_marks = List

    def get_mark(self):
        return self.marks[self.mark]

    def set_made(self):
        self._made_marks.append(self.mark)

    def check_mark(self):
        return self.mark not in self._made_marks

    def make_mark(self):
        m = self.marks[self.mark]
        m = m.replace(' ', '')
        sp = self.spacing

        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                if m[idx] == '1':
                    yield i * sp, j * sp

    def reset(self):
        self._made_marks = []

    def _mark_changed(self, new):
        m = MARKS[new]
        m = m.replace(' ', '\n')
        self.mark_display = m


if __name__ == '__main__':
    from traitsui.api import View, UItem, Item, EnumEditor
    from pychron.core.ui.qt.reference_mark_editor import ReferenceMarkEditor

    r = ReferenceMarks()
    # r.mark='UL'
    r.configure_traits(view=View(Item('mark', editor=EnumEditor(name='mark_ids')),
                                 # UItem('mark_display', height=-50,width=-50,
                                 #       style='custom'),
                                 UItem('mark_display', editor=ReferenceMarkEditor()), resizable=True
                                 ), )

# ============= EOF =============================================
