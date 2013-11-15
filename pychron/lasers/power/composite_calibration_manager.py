#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Instance, DelegatesTo, Button, List, Any, \
    Float
from traitsui.api import View, Item, VGroup, HGroup, Group, spring, \
    TabularEditor
#============= standard library imports ========================
import pickle
import os
from numpy import polyval
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.database.selectors.power_calibration_selector import PowerCalibrationSelector
from pychron.database.adapters.power_calibration_adapter import PowerCalibrationAdapter
from pychron.paths import paths
from pychron.graph.graph import Graph
from pychron.hardware.meter_calibration import MeterCalibration

'''
use a dbselector to select data
'''
class BoundsSelector(HasTraits):
    graph = Instance(Graph)
    def traits_view(self):
        v = View(Item('graph', show_label=False, style='custom'),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal'
                 )
        return v


class CompositeCalibrationManager(Manager):
    db = Instance(PowerCalibrationAdapter)
    selector = Instance(PowerCalibrationSelector)

    append = Button
    replace = Button
    load_graph = Button
    save = Button

    selected_calibrations = List
    selected = Any

    results = DelegatesTo('selector')

    graph = Instance(Graph)

    dclicked = Any

    parent_name = 'FusionsDiode'

    power = Float
    input = Float


    def _power_changed(self):
        pc = self._load_calibration()
        pc
        if pc is not None:
            self.input, _ = pc.get_input(self.power)

    def _load_calibration(self):
        try:
            p = self._get_calibration_path()
            with open(p, 'rb') as f:
                pc = pickle.load(f)
        except:
            return

        return pc

    def _dclicked_changed(self):
        s = self.selected
        if s is not None:
            s.bounds = None
            s.load_graph()
            s.graph.add_range_selector()

            bc = BoundsSelector(graph=s.graph)

            info = bc.edit_traits()
            if info.result:
                bounds = s.graph.plots[0].default_index.metadata['selections']
                s.bounds = bounds
                s.calibration_bounds = (polyval(s.coefficients, bounds[0]),
                                        polyval(s.coefficients, bounds[1]))

    def _append_fired(self):
        s = self.selector.selected
        if s is not None:
            for si in s:
                trs = si.traits().keys().remove('graph')
                self.selected_calibrations.append(si.clone_traits(traits=trs))

    def _replace_fired(self):
        s = self.selector.selected
        trs = s.traits().keys().remove('graph')
        self.selected_calibrations = s.clone_traits(traits=trs)

    def _save_fired(self):
        self._dump_calibration()

    def _dump_calibration(self):
        pc = MeterCalibration()
        coeffs = []
        bounds = []
        for s in self.selected_calibrations:
            coeffs.append(s.coefficients)
            bounds.append(s.calibration_bounds)
        pc.coefficients = coeffs
        pc.bounds = bounds

        p = self._get_calibration_path()
        self.info('saving calibration to {}'.format(p))
        with open(p, 'wb') as f:
            pickle.dump(pc, f)

    def _get_calibration_path(self):
        p = os.path.join(paths.hidden_dir, '{}_power_calibration'.format(self.parent_name))
        return p

    def _load_graph_fired(self):

        g = self.graph
        g.clear()
#        g.new_plot(zoom=True, pan=True,
#                   padding=[40, 10, 10, 40]
#                   )
        has_bounds = False
        for i, s in enumerate(self.selected_calibrations):
            if s.bounds:
                has_bounds = True
            elif has_bounds:
                g.clear()
                self._plot_factory(g)
                self.warning_dialog('{} does not have its bounds set'.format(s.rid))
                break

            s.load_graph(graph=g,
                         new_plot=i == 0
                         )

        g.redraw()

    def traits_view(self):
        selector_grp = Group(Item('selector', style='custom', show_label=False))
        transfer_grp = VGroup(spring,
                        VGroup(
                           Item('append', show_label=False),
                           Item('replace', show_label=False)
                           ),
                        spring)
        editor = TabularEditor(adapter=self.selector.tabular_adapter(),
                               editable=False,
                               dclicked='object.dclicked',
                               selected='object.selected'
                               )
        selected_grp = Item('selected_calibrations', editor=editor, show_label=False)
        data_tab = Group(
                         HGroup(
                            selector_grp,
                            transfer_grp,
                            selected_grp
                            ),
                         show_border=True,
                         label='Data')

        process_tab = Group(
                            HGroup(Item('power'), Item('input',
                                                       format_str='    %0.3f   ', style='readonly'),
                                   spring, Item('save', show_label=False),
                                   Item('load_graph', show_label=False)),
                            Item('graph', style='custom', show_label=False),
                            show_border=True,
                            label='Process')

        v = View(
                 VGroup(
                     data_tab,
                     process_tab
                 ),
                 resizable=True,
                 title='Composite {} Power Calibration'.format(self.parent_name)
                 )
        return v

    def _graph_default(self):
        g = Graph(container_dict={
#                                  'fill_padding':True,
#                                  'bgcolor':'red',
                                  'padding':5
                                  })
        self._plot_factory(g)
        return g

    def _plot_factory(self, graph):
        graph.new_plot(zoom=True, pan=True,
                   padding=[50, 10, 10, 40],
                   xtitle='Setpoint (%)',
                    ytitle='Measured Power (W)'
                   )

    def _db_default(self):

        if self.parent_name == 'FusionsDiode':
            name = paths.diodelaser_db
        else:
            name = paths.co2laser_db
        db = PowerCalibrationAdapter(name=name, kind='sqlite')
        db.connect()
        return db

    def _selector_default(self):
        return self.db._selector_factory()
if __name__ == '__main__':
    ccm = CompositeCalibrationManager()
    ccm.configure_traits()
#============= EOF =============================================
