# ===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from pyface.action.menu_manager import MenuManager
from traits.api import HasTraits, List, Int, Any
from traitsui.api import View, UItem, TabularEditor, VGroup, Heading, VSplit, Handler, InstanceEditor
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

#============= standard library imports ========================
#============= local library imports  ==========================


class ChangeAdapter(TabularAdapter):
    font = 'arial 10'
    create_date_width = Int(120)


class BlankHistoryAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'), ('Summary', 'summary')]

    def get_menu(self, obj, trait, row, column):
        return MenuManager(Action(name='Show Time Series', action='show_blank_time_series'))


class FitAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'), ('Summary', 'summary')]


class BlankAdapter(TabularAdapter):
    font = 'arial 10'
    columns = [('Isotope', 'isotope'), ('Fit', 'fit')]


class HistoryHandler(Handler):
    def show_blank_time_series(self, info, obj):
        obj.show_blank_time_series()


class HistoryView(HasTraits):
    name = 'History'

    blank_changes = List
    fit_changes = List

    blank_selected = Any
    blank_right_clicked = Any

    def __init__(self, an, *args, **kw):
        super(HistoryView, self).__init__(*args, **kw)
        self._load(an)

    def show_blank_time_series(self):
        print 'asfdsdfsadf', self.blank_selected

    def _load(self, an):
        self.blank_changes = an.blank_changes
        self.fit_changes = an.fit_changes
        self.blank_selected = self.blank_changes[-1]

    def traits_view(self):
        v = View(VSplit(VGroup(Heading('Blanks'),
                               UItem('blank_changes', editor=TabularEditor(adapter=BlankHistoryAdapter(),
                                                                           selected='blank_selected',

                                                                           editable=False)),
                               UItem('object.blank_selected.histories', editor=TabularEditor(adapter=BlankAdapter()))
        ),

                        VGroup(Heading('Fits'),
                               UItem('fit_changes', editor=TabularEditor(adapter=FitAdapter(),
                                                                         editable=False)))),
                 handler=HistoryHandler()
        )
        return v

#============= EOF =============================================

