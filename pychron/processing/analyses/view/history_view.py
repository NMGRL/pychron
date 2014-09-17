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
# ===============================================================================

#============= enthought library imports =======================
from pyface.action.menu_manager import MenuManager
from traits.api import HasTraits, List, Int, Any
from traitsui.api import View, UItem, TabularEditor, VGroup, VSplit, \
    Handler, InstanceEditor
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.graph.stacked_graph import StackedGraph


class ChangeAdapter(TabularAdapter):
    font = 'arial 10'
    create_date_width = Int(120)


class BlankHistoryAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'), ('Summary', 'summary')]

    def get_menu(self, obj, trait, row, column):
        return MenuManager(Action(name='Show Time Series', action='show_blank_time_series'))


class FitAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'), ('Summary', 'summary')]





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
        g=StackedGraph()
        isotopes=self.blank_selected.isotopes
        keys= sort_isotopes([iso.isotope for iso in isotopes], reverse=False)

        for k in keys:
            iso=next((i for i in isotopes if i.isotope==k))
            # print iso.analyses
            g.new_plot(padding_right=10)
            g.set_time_xaxis()
            g.set_y_title(iso.isotope)

            vs=iso.values
            if vs:
                g.new_series([vi.timestamp for vi in vs],
                             [vi.value for vi in vs])
            g.new_series([self.timestamp], [iso.value], type='scatter')

        g.set_x_limits(self.timestamp-86400, self.timestamp+86400)
        g.set_x_title('Time', plotid=0)
        g.edit_traits()

    def _load(self, an):
        self.blank_changes = an.blank_changes
        self.fit_changes = an.fit_changes
        self.blank_selected = self.blank_changes[-1]
        self.timestamp = an.timestamp

    def traits_view(self):
        v = View(VSplit(VGroup(
                               UItem('blank_changes', editor=TabularEditor(adapter=BlankHistoryAdapter(),
                                                                           selected='blank_selected',

                                                                           editable=False)),
                               UItem('blank_selected', style='custom', editor=InstanceEditor())),
                        label='Blanks'),
                 VGroup(
                        UItem('fit_changes', editor=TabularEditor(adapter=FitAdapter(),
                                                                  editable=False)),
                        label='Iso. Fits'),
                 handler=HistoryHandler())
        return v

#============= EOF =============================================

