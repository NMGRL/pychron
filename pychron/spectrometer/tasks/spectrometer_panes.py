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

# ============= enthought library imports =======================
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Str
from traitsui.api import View, Item, VGroup, HGroup, EnumEditor, spring, \
    Label, Spring, ListEditor, Group, InstanceEditor, UItem, TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn, TableColumn

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.pane_helpers import spacer
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class ColorColumn(TableColumn):
    cell_color_name = Str

    def get_cell_color(self, object):
        if self.cell_color_name:
            return getattr(object, self.cell_color_name)
        return self.cell_color_

    def get_value(self, *args, **kw):
        return


# class ScanPane(TraitsTaskPane):
# def traits_view(self):
# # v = View(UItem('graph', style='custom'))
# v = View(UItem('graphs',
# editor=ListEditor(deletable=True,
#                                          use_notebook=True,
#                                          page_name='.name',
#                                          style='custom'),
#                        style='custom'))
#         return v


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
                ObjectColumn(name='std', label=PLUSMINUS_ONE_SIGMA, width=100)]
        g = UItem('detectors', editor=TableEditor(columns=cols,
                                                  sortable=False,
                                                  editable=False))
        v = View(g)
        return v


class RecordControlsPane(TraitsDockPane):
    id = 'pychron.spectrometer.record'
    name = 'Record Scan'

    def traits_view(self):
        cols = [ObjectColumn(name='text', label='Text',
                             width=0.40, ),
                ObjectColumn(name='data_x',
                             format='%0.1f',
                             width=0.22,
                             label='Time(s)', editable=False),
                ObjectColumn(name='data_y',
                             format='%0.4f',
                             width=0.22,
                             label='Intensity', editable=False),
                CheckboxColumn(name='visible', width=0.12)]

        grp = VGroup(HGroup(
            icon_button_editor('start_record_button', 'media-record',
                               tooltip='Start recording',
                               enabled_when='not _recording'),
            icon_button_editor('stop_record_button',
                               'media-playback-stop',
                               tooltip='Stop recording',
                               enabled_when='_recording'),
            icon_button_editor('add_marker_button', 'flag',
                               enabled_when='_recording'),
            show_border=True,
            label='Record Scan'),
            HGroup(
                icon_button_editor('snapshot_button', 'camera'),
                show_border=True, label='Snapshot', ),
            VGroup(HGroup(icon_button_editor('clear_all_markers_button', 'delete',
                                             tooltip='Remove all markers'),
                          icon_button_editor('object.graph.add_visual_marker_button', 'add'),
                          Item('object.graph.marker_text', label='Text'),
                          Item('object.graph.marker_tool.label_with_intensity',
                               tooltip='Label marker with isotopic intensity',
                               label='Intensity')),

                   UItem('object.graph.markers', editor=TableEditor(columns=cols,
                                                                    selection_mode='rows',
                                                                    sortable=False,
                                                                    deletable=True)),
                   show_border=True, label='Markers'))

        v = View(grp)
        return v


class MassScannerPane(TraitsDockPane):
    id = 'pychron.spectrometer.scanner'
    name = 'Mass Scanner'

    def trait_context(self):
        ctx = super(MassScannerPane, self).trait_context()
        ctx['scanner'] = self.model.mass_scanner
        return ctx

    def traits_view(self):
        grp = VGroup(UItem('scanner.new_scanner',
                           tooltip='Open a new magnet scan',
                           enabled_when='scanner.new_scanner_enabled'),
                     HGroup(Item('scanner.step', format_str='%0.5f')),
                     HGroup(Item('scanner.start_mass', format_str='%0.3f'),
                            Item('scanner.stop_mass', format_str='%0.3f')),
                     HGroup(icon_button_editor('scanner.start_scanner', 'start',
                                               tooltip='Start the magnet scan',
                                               enabled_when='scanner.start_scanner_enabled'),
                            icon_button_editor('scanner.stop_scanner', 'stop',
                                               tooltip='Stop the magnet scan',
                                               enabled_when='scanner.stop_scanner_enabled'),
                            icon_button_editor('scanner.clear_graph_button', 'clear')))
        v = View(grp)
        return v


class DACScannerPane(TraitsDockPane):
    id = 'pychron.spectrometer.scanner'
    name = 'DAC Scanner'

    def trait_context(self):
        ctx = super(DACScannerPane, self).trait_context()
        ctx['scanner'] = self.model.dac_scanner
        return ctx

    def traits_view(self):
        grp = VGroup(UItem('scanner.new_scanner',
                           tooltip='Open a new magnet scan',
                           enabled_when='scanner.new_scanner_enabled'),
                     HGroup(icon_button_editor('scanner.start_scanner', 'start',
                                               tooltip='Start the magnet scan',
                                               enabled_when='scanner.start_scanner_enabled'),
                            icon_button_editor('scanner.stop_scanner', 'stop',
                                               tooltip='Stop the magnet scan',
                                               enabled_when='scanner.stop_scanner_enabled'),
                            icon_button_editor('scanner.clear_graph_button', 'clear')),
                     HGroup(Item('scanner.step', format_str='%0.5f'),
                            UItem('scanner.scan_time_length')),
                     HGroup(Item('scanner.min_dac', label='Min', format_str='%0.5f'),
                            Item('scanner.max_dac', label='Max', format_str='%0.5f'),
                            icon_button_editor('scanner.use_mftable_limits', 'foo',
                                               tooltip='Set DAC limits based on the Magnetic Field Table'),
                            show_border=True,
                            label='Limits'),
                     HGroup(Item('scanner.scan_min_dac', label='Min', format_str='%0.5f'),
                            Item('scanner.scan_max_dac', label='max', format_str='%0.5f'),
                            label='Scan Min/Max',
                            show_border=True),
                     show_border=True,
                     label='Scanner')
        v = View(grp)
        return v


class ControlsPane(TraitsDockPane):
    id = 'pychron.spectrometer.controls'
    name = 'Controls'
    closable = False
    movable = False
    floatable = False

    def traits_view(self):

        magnet_pos_grp = HGroup(
                UItem('_detector',
                      editor=EnumEditor(name='detector_names')),
                UItem('isotope',
                      editor=EnumEditor(name='isotopes')),
                icon_button_editor('set_magnet_position_button', 'arrow_left',
                                   tooltip='Apply Detector/Isotope magnet position'))

        magnet_grp = VGroup(magnet_pos_grp,
            UItem('magnet', style='custom'),
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

        # cols = [ObjectColumn(name='text', label='Text',
        # width=0.40, ),
        #         ObjectColumn(name='data_x',
        #                      format='%0.1f',
        #                      width=0.22,
        #                      label='Time(s)', editable=False),
        #         ObjectColumn(name='data_y',
        #                      format='%0.4f',
        #                      width=0.22,
        #                      label='Intensity', editable=False),
        #         CheckboxColumn(name='visible', width=0.12)]

        graph_cntrl_grp = VGroup(
            Item('graph_scan_width', label='Scan Width (mins)'),
            Item('graph_scale', label='Scale'),
            Item('graph_y_auto', label='Autoscale Y'),
            Item('graph_ymax', label='Max', format_str='%0.3f'),
            Item('graph_ymin', label='Min', format_str='%0.3f'),
            HGroup(icon_button_editor('clear_button', 'clear',
                                      tooltip='Clear and reset graph'),
                   spring),
            # HGroup(
            # icon_button_editor('start_record_button','media-record',
            #                        tooltip='Start recording',
            #                        enabled_when='not _recording'),
            #     icon_button_editor('stop_record_button',
            #                        'media-playback-stop',
            #                        tooltip='Stop recording',
            #                        enabled_when='_recording'),
            #     icon_button_editor('add_marker_button', 'flag',
            #                        enabled_when='_recording'),
            #     show_border=True,
            #     label='Record Scan'),
            # HGroup(
            #     icon_button_editor('snapshot_button', 'camera'),
            #     show_border=True, label='Snapshot', ),
            # VGroup(HGroup(icon_button_editor('clear_all_markers_button', 'delete',
            #                                  tooltip='Remove all markers'),
            #               icon_button_editor('object.graph.add_visual_marker_button', 'add'),
            #               Item('object.graph.marker_text', label='Text'),
            #               Item('object.graph.marker_tool.label_with_intensity',
            #                    tooltip='Label marker with isotopic intensity',
            #                    label='Intensity')),
            #
            #        UItem('object.graph.markers', editor=TableEditor(columns=cols,
            #                                                         selection_mode='rows',
            #                                                         sortable=False,
            #                                                         deletable=True)),
            #        show_border=True, label='Markers'),
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
                HGroup(Item('spectrometer_configuration',
                            label='Configuration',
                            editor=EnumEditor(name='spectrometer_configurations')),
                       icon_button_editor('set_spectrometer_configuration',
                                          'brick-go',
                                          tooltip='set selected spectrometer configuration'),
                       spacer(10),
                       Item('integration_time',
                            label='Integration Time(s)')),
                control_grp))
        return v


# ============= EOF =============================================
