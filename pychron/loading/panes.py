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
from traits.api import Any, Str, Int
from traitsui.api import View, UItem, Item, EnumEditor, \
    VGroup, TabularEditor, HGroup
from pyface.tasks.traits_task_pane import TraitsTaskPane
from enable.component_editor import ComponentEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================


class PositionsAdapter(TabularAdapter):
    columns = [('Labnumber', 'labnumber'),
               ('Irradiation', 'irradiation_str'),
               ('Sample', 'sample'),
               ('Positions', 'position_str')]
    font = 'arial 10'
    labnumber_width=Int(80)
    irradiation_str_width=Int(80)
    sample_width=Int(80)
    position_str_width=Int(80)


class LoadTablePane(TraitsDockPane):
    name = 'Positions'
    id = 'pychron.loading.positions'

    def traits_view(self):
        v = View(
            UItem('group_positions',
                  visible_when='show_group_positions'),
            UItem('positions',
                  editor=TabularEditor(adapter=PositionsAdapter(),
                                       refresh='refresh_table',
                                       scroll_to_row='scroll_to_row',
                                       selected='selected_positions',
                                       multi_select=True)))
        return v


class LoadPane(TraitsTaskPane):
    component = Any

    def traits_view(self):
        v = View(UItem('component',
                       style='custom',
                       editor=ComponentEditor()))
        return v


class LoadDockPane(TraitsDockPane):
    name = 'Load'
    load_name = Str
    id = 'pychron.loading.load'
    component = Any

    def traits_view(self):
        v = View(
            VGroup(
                UItem('load_name', style='readonly'),
                UItem('component',
                      style='custom',
                      editor=ComponentEditor())))
        return v


class LoadControlPane(TraitsDockPane):
    name = 'Load'
    id = 'pychron.loading.controls'

    def traits_view(self):
        notegrp = VGroup(
            Item('retain_note',
                 tooltip='Retain the Note for the next hole',
                 label='Lock'),
            Item('note', style='custom', show_label=False),
            show_border=True,
            label='Note')
        viewgrp = VGroup(
            Item('show_hole_numbers'),
            Item('show_labnumbers'),
            Item('show_weights'),
            Item('show_spans'),
            show_border=True,
            label='View')

        samplegrp = VGroup(
            Item('loader_name', label='User'),
            HGroup(Item('load_name',
                        editor=EnumEditor(name='loads'),
                        label='Loads'),
                   Item('add_button', show_label=False),
                   Item('delete_button', show_label=False)),
            VGroup(
                Item('irradiation',
                     editor=EnumEditor(name='irradiations')),
                Item('level', editor=EnumEditor(name='levels')),
                Item('labnumber', editor=EnumEditor(name='labnumbers')),
                Item('sample_info', style='readonly'),
                HGroup(
                    Item('weight', label='Weight (mg)'),
                    Item('retain_weight', label='Lock',
                         tooltip='Retain the Weight for the next hole')),
                HGroup(Item('npositions', label='NPositions'),
                       Item('auto_increment')),
                enabled_when='load_name'),
            show_border=True,
            label='Sample')

        v = View(
            VGroup(
                samplegrp,
                notegrp,
                viewgrp))
        return v

#============= EOF =============================================
