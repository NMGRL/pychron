# ===============================================================================
# Copyright 2012 Jake Ross
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
# ===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Float, List, Bool, on_trait_change, Int, \
     Property, Instance, Event, Button
from traitsui.api import View, Item, TabularEditor, HGroup, VGroup, spring
from chaco.api import BasePlotContainer
from traitsui.tabular_adapter import TabularAdapter
from enable.component_editor import ComponentEditor

from pychron.processing.plotters.ideogram import Ideogram
from pychron.processing.analysis import NonDBAnalysis
from pychron.processing.plotter_options_manager import IdeogramOptionsManager

#============= standard library imports ========================
#============= local library imports  ==========================

class DatumAdapter(TabularAdapter):
    columns = [('', 'spacer'),
               ('Status', 'status'),
               ('Age', 'age'),
               ('Error', 'error'),
               ]
    spacer_width = Int(2)
    status_width = Int(25)

    age_width = Int(75)
    error_width = Int(75)
    age_text = Property
    error_text = Property
    status_text = Property
    spacer_text = Property

    def _get_spacer_text(self):
        return ''

    def _set_status_text(self, v):
        if v.lower() == 'x':
            self.item.status = False
        else:
            self.item.status = True

    def _get_status_text(self):
        at = 'X'
        if self.item.status:
            at = ''
        return at

    def _set_age_text(self, v):
        try:
            self.item.age = float(v)
        except ValueError:
            pass

    def _get_age_text(self):
        at = ''
        if self.item.age:
            at = self.item.age
        return at

    def _set_error_text(self, v):
        try:
            self.item.error = float(v)
        except ValueError:
            pass

    def _get_error_text(self):
        at = ''
        if self.item.error:
            at = self.item.error
        return at

class Datum(HasTraits):
    status = Bool(True)
    age = Float
    error = Float

class ManualEntry(HasTraits):
    data = List
    nrows = Int(50)
    def _data_default(self):
        ds = [Datum() for _ in range(self.nrows)]
        ds[0].age = 1.01
        ds[0].error = 0.25
        ds[1].age = 1.02
        ds[1].error = 0.25
        ds[2].age = 1.25
        ds[2].error = 0.25
        ds[3].age = 1.4
        ds[3].error = 0.25
        return ds

    def traits_view(self):
        editor = TabularEditor(adapter=DatumAdapter())
        v = View(Item('data',
                      editor=editor,
                      height=500,
                      show_label=False),
                )
        return v


class ManualEntryManager(HasTraits):
    plotter = Instance(Ideogram, ())
    plotter_options_manager = Instance(IdeogramOptionsManager)
    graph_container = Instance(BasePlotContainer)
    manual_entry = Instance(ManualEntry, ())
    update = Event
    edit_plot_options = Button('Edit Plot Options')

    def _plotter_options_manager_changed(self):
        po = self.plotter_options_manager
        for pi in po.plotter_options_list:
            pi.data_type_editable = False
        return po

    def _edit_plot_options_fired(self):
        info = self.plotter_options_manager.edit_traits(kind='livemodal')
        if info.result:
            self.update = True

    @on_trait_change('update,manual_entry:data:+, manual_entry:data[]')
    def _update_graph(self, obj, name, old, new):
        ans = self._build_analyses()
        po = self.plotter_options_manager.plotter_options
#        po.add_aux_plot(name='analysis_number', x_error=True)
        container, _ = self.plotter.build(ans, plotter_options=po)
        self.graph_container = container
        self.graph_container.request_redraw()

    def _build_analyses(self):
        ans = []
        for di in self.manual_entry.data:
            if di.age:
                ei = di.error
                if not ei:
                    ei = 1e-10

                ai = NonDBAnalysis(age=(di.age, ei),
                                   status=not int(di.status)
                                   )
                ans.append(ai)
        return ans

    def traits_view(self):
        v = View(
                 VGroup(
                        HGroup(Item('graph_container',
                                 show_label=False,
                                 style='custom',
                                 width=0.7,
                                 editor=ComponentEditor()),
                               Item('manual_entry',
                                 width=0.3,
                                 show_label=False, style='custom')
                          ),
                        HGroup(spring,
                               Item('edit_plot_options', show_label=False))
                        ),
               title='Manual Entry Ideogram',
               resizable=True,
               height=500,
               width=700
               )
        return v

if __name__ == '__main__':

    from launchers.helpers import build_version
    build_version('_experiment', set_path=True)

    mem = ManualEntryManager()
    mem.manual_entry.data[0].age = 1.04
    mem.configure_traits()
# ============= EOF =============================================
