#===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================

from traits.api import HasTraits, Str, Bool, Either, Float, List, Int
from traitsui.api import View, UItem, VSplit, TabularEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
import yaml
from pychron.core.ui.patch_editor import PatchEditor


class ChangeAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Line','line'),
               ('Before', 'avalue'),
               ('After', 'bvalue')]


class Change(HasTraits):
    name = Str
    avalue = Either(Str, Float)
    bvalue = Either(Str, Float)
    line= Int

class Diff(HasTraits):
    """
        represents a uncommited change
    """
    use = Bool
    name = Str
    patch = Str
    path = Str

    changes=List

    def traits_view(self):
        v = View(VSplit(
            UItem('patch', style='custom', editor=PatchEditor()),
            UItem('changes', editor=TabularEditor(adapter=ChangeAdapter(),
                                                  editable=False))))
        return v

    def _patch_changed(self):
        cs = []
        lines=self.patch.split('\n')
        has_deletion=False
        offset=0
        for idx, li in enumerate(lines[2:]):
            if li.startswith('-'):
                has_deletion = True
                a = li
            if has_deletion and li.startswith('+'):
                b = li

                a=a[1:].strip()
                b=b[1:].strip()

                ad=yaml.load(a)
                bd=yaml.load(b)

                k=ad.keys()[0]

                cs.append(Change(name=k, line=idx-offset,
                                 avalue=ad[k], bvalue=bd[k]))
                offset+=1

                #find diff
                # for i, s in enumerate(ndiff(a, b)):
                #     if s[0] == ' ':
                #         continue
                #     elif s[0] == '-':
                #         if not s[-1] in ('-', '+'):
                #             print 'delete',s[-1], i
                #
                #             # self._set_diff(idx - 2, i, QColor(200, 0, 0))
                #     elif s[0] == '+':
                #         if not s[-1] in ('-', '+'):
                #             print 'add', s[-1], i
                #             # self._set_diff(idx - 1, i, QColor(0, 200, 0))
        self.changes = cs

#============= EOF =============================================

