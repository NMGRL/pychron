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
from traits.api import Str
from traitsui.api import View, Item, VGroup, HGroup, EnumEditor, spring, \
    Label, Spring, ListEditor, Group, InstanceEditor, UItem, TableEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.table_column import ObjectColumn, TableColumn
from pychron.envisage.tasks.pane_helpers import spacer


class ColorColumn(TableColumn):
    cell_color_name = Str

    def get_cell_color(self, object):
        if self.cell_color_name:
            return getattr(object, self.cell_color_name)
        return self.cell_color_

    def get_value(self, *args, **kw):
        return


class ScanPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('graph', style='custom'))
        return v


class ReadoutPane(TraitsDockPane):
    id = 'pychron.spectrometer.readout'
    name = 'Readout'

    def traits_view(self):
        v = View(Group(UItem('readout_view', style='custom'), show_border=True))
        return v


class IntensitiesPane(TraitsDockPane):
    id = 'pychron.spectrometer.intensities'
    name = 'Intensities'

    def traits_view(self):
        cols = [ColorColumn(cell_color_name='color', label='Color'),
                ObjectColumn(name='name', width=175),
                ObjectColumn(name='intensity', width=100),
                ObjectColumn(name='std', label=u'\u00b11\u03c3')]
        g = UItem('detectors', editor=TableEditor(columns=cols,
                                                  sortable=False,
                                                  editable=False))
        v = View(g)
        return v


class ControlsPane(TraitsDockPane):
    id = 'pychron.spectrometer.controls'
    name = 'Controls'
    closable = False
    movable = False
    floatable = False

    def traits_view(self):
        # def hitem(n, l, **kw):
        #     return HGroup(Label(l), spring, Item(n, show_label=False, **kw),
        #                   Spring(springy=False, width=275))

        magnet_grp = VGroup(
            HGroup(
                UItem('detector',
                      editor=EnumEditor(name='detectors')),
                UItem('isotope',
                      editor=EnumEditor(name='isotopes'))),
            UItem('magnet', style='custom'),
            UItem('scanner', style='custom'),
            label='Magnet')
        detector_grp = VGroup(
            HGroup(
                spring,
                Label('Deflection'),
                Spring(springy=False, width=70)),
            Item('detectors',
                 show_label=False,
                 editor=ListEditor(style='custom', mutable=False, editor=InstanceEditor())),
            label='Detectors')

        rise_grp = UItem('rise_rate', style='custom')
        source_grp = UItem('source', style='custom')

        graph_cntrl_grp = VGroup(
            Item('graph_scan_width', label='Scan Width (mins)'),
            Item('graph_scale', label='Scale'),
            Item('graph_y_auto', label='Autoscale Y'),
            Item('graph_ymax', label='Max', format_str='%0.3f'),
            Item('graph_ymin', label='Min', format_str='%0.3f'),
            # UItem('record_button', editor=ButtonEditor(label_value='record_label'))
            HGroup(
                UItem('record_button'),
                # icon_button_editor('record_button','media-record',
                #                       tooltip='Start/stop scan recording'),
                Item('add_marker_button',
                        show_label=False,
                        enabled_when='_recording')),
            label='Graph')

        control_grp = Group(
            graph_cntrl_grp,
            detector_grp,
            rise_grp,
            magnet_grp,
            source_grp,
            layout='tabbed')

        v = View(
            VGroup(
                HGroup(spacer(10),
                       Item('integration_time',
                            label='Integration Time(s)')),
                control_grp))
        return v


#============= EOF =============================================
