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
from traits.api import HasTraits, Str, Instance
from traitsui.api import View, UItem, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.git_archive.diff_editor import DiffEditor


class DiffModel(HasTraits):
    left_text = Str
    right_text = Str


class DiffView(HasTraits):
    model=Instance(DiffModel)
    def traits_view(self):
        return View(
                    VGroup(
                           UItem('model',
                                 # width=1000,
                                 # height=200,
                                 editor=DiffEditor())),
                    title='Diff',
                    width=900,
                    buttons=['OK'],
                    # kind='livemodal',
                    resizable=True)

if __name__ == '__main__':
    a='''a=1
b=1'''
    b='''a=1
b=2'''
    a='''a=1
b=1'''
    b='''a=1
b=1
c=1'''
    a='''a=1
b=1'''
    b='''a=1
b=1
c=1'''
    a='''a
b
c
d
e
f
1
2
2
3
4
4
56
31
13
3
3'''
    b='''
d
ee
f
1
2
2
3
4
4
56
31
13
3
3'''
    a = '''a=1
b=1
c=1
e=1
d=1
f=1'''
    b = '''a=12
b=1
c=1
e=1
f=1'''
    dv=DiffView(model=DiffModel(left_text=b, right_text=a))
    dv.configure_traits()
# ============= EOF =============================================



