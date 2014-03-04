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
from traits.api import HasTraits, List, Int
from traitsui.api import View, UItem, TabularEditor, VGroup, Heading, VSplit
from traitsui.tabular_adapter import TabularAdapter

#============= standard library imports ========================
#============= local library imports  ==========================


class ChangeAdapter(TabularAdapter):
    font='arial 10'
    create_date_width=Int(120)

class BlankAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'),('Summary','summary')]


class FitAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'),('Summary','summary')]


class HistoryView(HasTraits):
    name = 'History'

    blank_changes=List
    fit_changes=List
    def __init__(self, an, *args, **kw):
        super(HistoryView, self).__init__(*args, **kw)
        self._load(an)

    def _load(self, an):
        self.blank_changes=an.blank_changes
        self.fit_changes=an.fit_changes

    def traits_view(self):
        v = View(VSplit(VGroup(Heading('Blanks'),
                               UItem('blank_changes', editor=TabularEditor(adapter=BlankAdapter(),
                                                                           editable=False))),
                        VGroup(Heading('Fits'),
                               UItem('fit_changes', editor=TabularEditor(adapter=FitAdapter(),
                                                                         editable=False)))))
        return v

#============= EOF =============================================

