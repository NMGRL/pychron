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
from enable.component_editor import ComponentEditor
from traits.api import Instance
from traitsui.api import View, Item, TabularEditor, VGroup, spring, HGroup, \
    EnumEditor, UItem, Label, VSplit
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor, spacer
from pychron.entry.irradiated_position import IrradiatedPositionAdapter
from pychron.experiment.tasks.browser.adapters import ProjectAdapter, SampleAdapter


class IrradiationEditorPane(TraitsDockPane):
    id = 'pychron.labnumber.editor'
    name = 'Editor'
    sample_tabular_adapter = Instance(SampleAdapter, ())

    def traits_view(self):
        project_grp = VGroup(
            HGroup(spacer(),
                   Label('Filter'),
                   UItem('project_filter',
                         width=75),
                   icon_button_editor('clear_selection_button',
                                      'cross',
                                      tooltip='Clear selected'),
                   icon_button_editor('edit_project_button', 'database_edit',
                                      tooltip='Edit selected project in database'),
                   icon_button_editor('add_project_button', 'database_add',
                                      tooltip='Add project to database')
            ),
            UItem('projects',
                  editor=TabularEditor(editable=False,
                                       selected='selected_projects',
                                       adapter=ProjectAdapter(),
                                       multi_select=False),
                  width=75))

        sample_grp = VGroup(
            HGroup(
                #Label('Filter'),
                UItem('sample_filter_parameter',
                      editor=EnumEditor(name='sample_filter_parameters')),
                UItem('sample_filter',
                      width=75),
                UItem('sample_filter',
                      editor=EnumEditor(name='sample_filter_values'),
                      width=-25),
                #UItem('filter_non_run_samples',
                #      tooltip='Omit non-analyzed samples'),
                icon_button_editor('configure_sample_table',
                                   'cog',
                                   tooltip='Configure Sample Table'),
                icon_button_editor('edit_sample_button', 'database_edit',
                                   tooltip='Edit sample in database'),
                icon_button_editor('add_sample_button', 'database_add',
                                   tooltip='Add sample to database')),

            UItem('samples',
                  editor=TabularEditor(
                      adapter=self.sample_tabular_adapter,
                      editable=False,
                      selected='selected_sample',
                      multi_select=False,
                      column_clicked='column_clicked',
                      stretch_last_section=False
                  ),
                  width=75
            )
        )
        v = View(VSplit(project_grp,
                        sample_grp))
        return v


class LabnumbersPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('irradiated_positions',
                       editor=TabularEditor(adapter=IrradiatedPositionAdapter(),
                                            refresh='refresh_table',
                                            multi_select=True,
                                            selected='selected',
                                            operations=['edit'])),
        )
        return v


class IrradiationCanvasPane(TraitsDockPane):
    name = 'Canvas'
    id = 'pychron.entry.irradiation_canvas'

    def traits_view(self):
        v = View(UItem('canvas',
                       editor=ComponentEditor()))
        return v


class IrradiationPane(TraitsDockPane):
    name = 'Irradiation'
    id = 'pychron.labnumber.irradiation'

    def traits_view(self):
        irrad = HGroup(
            spacer(),
            Item('irradiation',
                 width=-150,
                 editor=EnumEditor(name='irradiations')),
            icon_button_editor('edit_irradiation_button', 'database_edit',
                               enabled_when='edit_irradiation_enabled'),
            icon_button_editor('add_irradiation_button', 'database_add'))

        level = HGroup(
            spacer(),
            Label('Level:'),
            spacer(-23),
            UItem('level',
                  width=-150,
                  editor=EnumEditor(name='levels')),
            icon_button_editor('edit_level_button', 'database_edit',
                               enabled_when='edit_level_enabled'),
            icon_button_editor('add_level_button', 'database_add'))

        v = View(VGroup(irrad, level))
        return v

    def traits_view2(self):
        v = View(
            HGroup(
                VGroup(HGroup(Item('irradiation',
                                   editor=EnumEditor(name='irradiations')
                ),
                              Item('edit_irradiation_button',
                                   enabled_when='edit_irradiation_enabled',
                                   show_label=False)
                ),
                       HGroup(Item('level', editor=EnumEditor(name='levels')),
                              spring,
                              Item('edit_level_button',
                                   enabled_when='edit_level_enabled',
                                   show_label=False)
                       ),
                       #Item('add_irradiation_button', show_label=False),
                       #Item('add_level_button', show_label=False),
                       #                                        Item('irradiation_tray',
                       #                                             editor=EnumEditor(name='irradiation_trays')
                       #                                             )
                ),
                #spring,
                #VGroup(
                #    Item('tray_name', style='readonly', show_label=False),
                #                                  Item('irradiation_tray_image',
                #                                       editor=ImageEditor(),
                #                                       height=100,
                #                                       width=200,
                #                                       style='custom',
                #                                       show_label=False),
                #),
            ),
            #                            label='Irradiation',
            #                            show_border=True
        )
        return v

#     def traits_view(self):
#        irradiation = Group(
#                            HGroup(
#                                   VGroup(HGroup(Item('irradiation',
#                                                      editor=EnumEditor(name='irradiations')
#                                                      ),
#                                                 Item('edit_irradiation_button',
#                                                      enabled_when='edit_irradiation_enabled',
#                                                      show_label=False)
#                                                 ),
#                                          HGroup(Item('level', editor=EnumEditor(name='levels')),
#                                                 spring,
#                                                 Item('edit_level_button',
#                                                      enabled_when='edit_level_enabled',
#                                                      show_label=False)
#                                                 ),
#                                          Item('add_irradiation_button', show_label=False),
#                                          Item('add_level_button', show_label=False),
# #                                        Item('irradiation_tray',
# #                                             editor=EnumEditor(name='irradiation_trays')
# #                                             )
#                                          ),
#                                   spring,
#                                   VGroup(
#                                          Item('tray_name', style='readonly', show_label=False),
#                                          Item('irradiation_tray_image',
#                                               editor=ImageEditor(),
#                                               height=200,
#                                               width=200,
#                                               style='custom',
#                                               show_label=False),
#                                          ),
#                                        ),
#                            label='Irradiation',
#                            show_border=True
#                            )
#
#        auto = Group(
#                    Item('auto_assign', label='Auto-assign Labnumbers'),
#                    Item('auto_startrid', label='Start Labnumber',
#                         enabled_when='auto_assign'
#                         ),
#                    Item('auto_project', label='Project',
#                         enabled_when='auto_assign'
#                         ),
#                    Item('auto_sample', label='Sample',
#                         enabled_when='auto_assign'
#                         ),
#                    Item('auto_material', label='Material',
#                         enabled_when='auto_assign'
#                         ),
#                     Item('auto_j', format_str='%0.2e', label='Nominal J.'),
#                     Item('auto_j_err', format_str='%0.2e', label='Nominal J Err.'),
#                    Item('auto_assign_overwrite', label='Overwrite exisiting Labnumbers',
#                         enabled_when='auto_assign'
#                         ),
#                      HGroup(Item('freeze_button', show_label=False), Item('thaw_button', show_label=False),
#                              enabled_when='selected'),
#                      show_border=True,
#                      label='Auto-Assign'
#
#                      )
#
#        samples = Group(
#
#                        Item('irradiated_positions',
#                             editor=TabularEditor(adapter=IrradiatedPositionAdapter(),
#                                                  update='_update_sample_table',
#                                                  multi_select=True,
#                                                  selected='selected',
#                                                  operations=['edit']
#                                                  ),
#                             show_label=False
#                             ),
#                        label='Lab Numbers',
#                        show_border=True
#                        )
# #        flux = Group(
# #                     HGroup(
# #                            Item('flux_monitor', show_label=False, editor=EnumEditor(name='flux_monitors')),
# #                            Item('edit_monitor_button', show_label=False)),
# #                     Item('flux_monitor_age', format_str='%0.3f', style='readonly', label='Monitor Age (Ma)'),
# #                     Spring(height=50, springy=False),
# #                     Item('calculate_flux_button',
# #                          enabled_when='calculate_flux_enabled',
# #                          show_label=False),
# #                     label='Flux',
# #                     show_border=True
# #                     )
#        v = View(VGroup(
#                        HGroup(auto, irradiation,
# #                               flux
#                               ),
#                        samples,
#                        HGroup(spring, Item('save_button', show_label=False))
#                        ),
#============= EOF =============================================
