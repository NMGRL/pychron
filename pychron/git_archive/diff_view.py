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
from traits.api import HasTraits, Str
from traitsui.api import View, UItem, TextEditor, VGroup, HGroup, HSplit
#============= standard library imports ========================
#============= local library imports  ==========================

def left_group():
    return VGroup(HGroup(UItem('left_message', style='readonly'),
                         UItem('left_date', style='readonly')),
                  UItem('left',
                        style='custom',
                        editor=TextEditor(read_only=True)))


def right_group():
    return VGroup(HGroup(UItem('right_message', style='readonly'),
                         UItem('right_date', style='readonly')),
                  UItem('right',
                        style='custom',
                        editor=TextEditor(read_only=True)))


class DiffView(HasTraits):
    left = Str
    left_date = Str
    left_message =Str
    right = Str
    right_date = Str
    right_message =Str
    diff = Str

    def traits_view(self):
        return View(VGroup(HSplit(left_group(), right_group()),
                           UItem('diff',
                                 style='custom',
                                 editor=TextEditor(read_only=True))),
                    title='Diff',
                    width=900,
                    buttons=['OK'],
                    kind='livemodal',
                    resizable=True)
#============= EOF =============================================



