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
from pyface.action.menu_manager import MenuManager
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Instance, Int
from traitsui.api import View, Item, TabularEditor, VGroup, HGroup, \
    EnumEditor, UItem, Label, VSplit, TextEditor
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.enum_editor import myEnumEditor
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.entry.irradiated_position import IrradiatedPositionAdapter
from pychron.envisage.browser.adapters import SampleAdapter, BrowserAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.stylesheets import load_stylesheet
from pychron.envisage.tasks.pane_helpers import spacer
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class ProjectAdapter(BrowserAdapter):
    columns = [('Name', 'name'),
               ('PI', 'principal_investigator')]

    def get_menu(self, obj, trait, row, column):
        return MenuManager(Action(name='Unselect', action='unselect_projects'))


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
        v = View(VGroup(HGroup(Item('estimated_j_value',
                                    style='readonly', label='Est. J'),
                               Item('total_irradiation_hours',
                                    style='readonly', label='Hours')),
                        UItem('chronology_items', editor=TabularEditor(editable=False,
                                                                       adapter=ChronologyAdapter()))))
        return v
        # v = View(VGroup(VGroup(Item('estimated_j_value',
        #                             style='readonly',
        #                             label='Est. J')),
        #                 VGroup(UItem('chronology_items',
        #                              editor=TabularEditor(editable=False,
        #                                                   adapter=ChronologyAdapter())))))
        # return v

class IrradiationEditorPane(TraitsDockPane):
    id = 'pychron.labnumber.editor'
    name = 'Editor'
    sample_tabular_adapter = Instance(SampleAdapter, ())

    def traits_view(self):
        self.sample_tabular_adapter.columns = [('Sample', 'name'),
                                               ('Material', 'material'),
                                               ('Grainsize','grainsize'),
                                               ('Note', 'note')]

        # tgrp = HGroup(icon_button_editor('clear_button', 'table_lightning',
        #                                  enabled_when='selected',
        #                                  tooltip='Clear contents of selected positions'))
        pi_grp = VGroup(UItem('principal_investigator',
                              editor=EnumEditor(name='principal_investigator_names')),
                        show_border=True,
                        label='Principal Investigator')
        project_grp = VGroup(UItem('projects',
                                   editor=FilterTabularEditor(editable=False,
                                                              use_fuzzy=True,
                                                              selected='selected_projects',
                                                              adapter=ProjectAdapter(),
                                                              multi_select=True),
                                   width=175),
                             show_border=True,
                             label='Projects')

        sample_grp = VGroup(HGroup(UItem('sample_filter_parameter',
                                         editor=EnumEditor(name='sample_filter_parameters')),
                                   UItem('sample_filter',
                                         editor=ComboboxEditor(name='sample_filter_values'),
                                         width=75),
                                   # icon_button_editor('edit_sample_button', 'database_edit',
                                   #                    tooltip='Edit sample in database'),
                                   # icon_button_editor('add_sample_button', 'database_add',
                                   #                    tooltip='Add sample to database')
                                   icon_button_editor('clear_sample_button', 'clear',
                                                      tooltip='Clear selected sample')),

                            UItem('samples',
                                  editor=TabularEditor(adapter=self.sample_tabular_adapter,
                                                       editable=False,
                                                       selected='selected_samples',
                                                       dclicked='dclicked',
                                                       multi_select=True,
                                                       column_clicked='column_clicked',
                                                       stretch_last_section=False),
                                  width=75))
        jgrp = HGroup(UItem('j'), Label(PLUSMINUS_ONE_SIGMA), UItem('j_err'),
                      icon_button_editor('estimate_j_button', 'cog'),
                      show_border=True, label='J')
        ngrp = HGroup(UItem('note'),
                      UItem('weight'),
                      show_border=True, label='Note')
        sgrp = HGroup(UItem('invert_flag'),
                      Item('selection_freq', label='Freq'),
                      show_border=True,
                      label='Selection')
        v = View(VSplit(VGroup(HGroup(sgrp, jgrp),
                               ngrp,
                               pi_grp,
                               project_grp),
                        sample_grp,
                        style_sheet=load_stylesheet('labnumber_entry')))
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
    closable = False

    def traits_view(self):
        irrad = HGroup(
            spacer(),
            Item('irradiation',
                 width=-150,
                 editor=myEnumEditor(name='irradiations')),
            icon_button_editor('edit_irradiation_button', 'database_edit',
                               enabled_when='edit_irradiation_enabled',
                               tooltip='Edit irradiation'),
            icon_button_editor('add_irradiation_button', 'database_add',
                               tooltip='Add irradiation'),
            icon_button_editor('import_irradiation_button', 'database_go',
                               tooltip='Import irradiation'))

        level = HGroup(
            spacer(),
            Label('Level:'),
            spacer(-23),
            UItem('level',
                  width=-150,
                  editor=myEnumEditor(name='levels')),
            icon_button_editor('edit_level_button', 'database_edit',
                               tooltip='Edit level',
                               enabled_when='edit_level_enabled'),
            icon_button_editor('add_level_button', 'database_add',
                               tooltip='Add level'))

        v = View(VGroup(irrad, level))
        return v

# ============= EOF =============================================
