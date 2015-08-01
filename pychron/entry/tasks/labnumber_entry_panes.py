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
from enable.component_editor import ComponentEditor
from traits.api import Instance, Int
from traitsui.api import View, Item, TabularEditor, VGroup, HGroup, \
    EnumEditor, UItem, Label, VSplit, TextEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.pane_helpers import spacer
from pychron.entry.irradiated_position import IrradiatedPositionAdapter
from pychron.envisage.browser.adapters import ProjectAdapter, SampleAdapter
from pychron.pychron_constants import PLUSMINUS_SIGMA


class LevelInfoPane(TraitsDockPane):
    id = 'pychron.entry.level'
    name = 'Level'

    def traits_view(self):
        v = View(Item('level_production_name', label='Production', style='readonly'),
                 Item('irradiation_tray', label='Irradiation Tray', style='readonly'),
                 VGroup(UItem('level_note', style='custom', editor=TextEditor(read_only=True)),
                        show_border=True, label='Note'))
        return v


class ChronologyAdapter(TabularAdapter):
    columns = [('Start', 'start'), ('End', 'end')]
    start_width = Int(150)
    end_width = Int(150)


class ChronologyPane(TraitsDockPane):
    id = 'pychron.entry.chronology'
    name = 'Chronology'

    def traits_view(self):
        v = View(VGroup(VGroup(Item('estimated_j_value',
                                    style='readonly',
                                    label='Est. J')),
                        VGroup(UItem('chronology_items',
                                     editor=TabularEditor(editable=False,
                                                          adapter=ChronologyAdapter())))))
        return v


class IrradiationEditorPane(TraitsDockPane):
    id = 'pychron.labnumber.editor'
    name = 'Editor'
    labnumber_tabular_adapter = Instance(SampleAdapter, ())

    def traits_view(self):
        tgrp = HGroup(VGroup(icon_button_editor('add_project_button', 'database_add',
                                                tooltip='Add project'),
                             show_border=True,
                             label='Project'),
                      VGroup(icon_button_editor('add_material_button', 'database_add',
                                                tooltip='Add material'),
                             show_border=True,
                             label='Material'),
                      VGroup(icon_button_editor('add_sample_button', 'database_add',
                                                tooltip='Add sample'),
                             show_border=True,
                             label='Sample'),
                      icon_button_editor('generate_identifiers_button',
                                         'table_lightning',
                                         tooltip='Generate Identifiers for this irradiation'),
                      icon_button_editor('preview_generate_identifiers_button',
                                         'document-preview',
                                         tooltip='Preview identifiers generated for this irradiation level'))

        project_grp = VGroup(
            UItem('projects',
                  editor=FilterTabularEditor(editable=False,
                                             selected='selected_projects',
                                             adapter=ProjectAdapter(),
                                             multi_select=True),
                  width=175),
            show_border=True,
            label='Projects')

        sample_grp = VGroup(
            HGroup(
                UItem('sample_filter_parameter',
                      editor=EnumEditor(name='sample_filter_parameters')),
                UItem('sample_filter',
                      editor=ComboboxEditor(name='sample_filter_values'),
                      width=75),
                icon_button_editor('edit_sample_button', 'database_edit',
                                   tooltip='Edit sample in database'),
                icon_button_editor('add_sample_button', 'database_add',
                                   tooltip='Add sample to database')),

            UItem('samples',
                  editor=TabularEditor(
                      adapter=self.labnumber_tabular_adapter,
                      editable=False,
                      selected='selected_samples',
                      multi_select=False,
                      column_clicked='column_clicked',
                      stretch_last_section=False),
                  width=75))
        jgrp = HGroup(UItem('j'), Label(PLUSMINUS_SIGMA), UItem('j_err'),
                      icon_button_editor('estimate_j_button', 'cog'),
                      show_border=True, label='J')
        ngrp = HGroup(UItem('note'),
                      UItem('weight'),
                      show_border=True, label='Note')
        # wgrp = HGroup(UItem('weight'), show_border=True, label='Weight')
        sgrp = HGroup(UItem('invert_flag'),
                      Item('selection_freq', label='Freq'),
                      show_border=True,
                      label='Selection')
        v = View(VSplit(VGroup(tgrp,
                               HGroup(sgrp, jgrp),
                               # wgrp,
                               ngrp,
                               project_grp),
                        sample_grp))
        return v


class LabnumbersPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('irradiated_positions',
                       editor=TabularEditor(adapter=IrradiatedPositionAdapter(),
                                            refresh='refresh_table',
                                            multi_select=True,
                                            selected='selected',
                                            operations=['edit'])), )
        return v


class IrradiationCanvasPane(TraitsDockPane):
    name = 'Canvas'
    id = 'pychron.entry.irradiation_canvas'

    def traits_view(self):
        v = View(VGroup(HGroup(Item('irradiation_tray', style='readonly')),
                        UItem('canvas', editor=ComponentEditor())))
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
                               enabled_when='edit_irradiation_enabled',
                               tooltip='Edit irradiation'),
            icon_button_editor('add_irradiation_button', 'database_add',
                               tooltip='Add irradiation'))

        level = HGroup(
            spacer(),
            Label('Level:'),
            spacer(-23),
            UItem('level',
                  width=-150,
                  editor=EnumEditor(name='levels')),
            icon_button_editor('edit_level_button', 'database_edit',
                               tooltip='Edit level',
                               enabled_when='edit_level_enabled'),
            icon_button_editor('add_level_button', 'database_add',
                               tooltip='Add level'))

        v = View(VGroup(irrad, level))
        return v

# ============= EOF =============================================
