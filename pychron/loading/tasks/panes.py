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
from traits.api import Int, Property, Instance
from traitsui.api import View, UItem, Item, VGroup, TabularEditor, HGroup, spring, \
    EnumEditor, Tabbed, Handler, CheckListEditor
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.configurable_tabular_adapter import ConfigurableMixin
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.table_configurer import TableConfigurer, TableConfigurerHandler
from pychron.envisage.icon_button_editor import icon_button_editor


class PositionsAdapter(TabularAdapter, ConfigurableMixin):
    columns = [('Identifier', 'identifier'),
               ('Irradiation', 'irradiation_str'),
               ('Sample', 'sample'),
               ('Material', 'material'),
               ('Position', 'position'),
               ('Weight', 'weight'),
               ('N. Xtals', 'nxtals'),
               ('Note', 'note')]
    all_columns = [('Identifier', 'identifier'),
                   ('Irradiation', 'irradiation_str'),
                   ('Sample', 'sample'),
                   ('Material', 'material'),
                   ('Position', 'position'),
                   ('Weight', 'weight'),
                   ('N. Xtals', 'nxtals'),
                   ('Note', 'note')]
    font = 'arial 12'

    def get_menu(self, obj, trait, row, column):
        actions = [Action(name='Configure', action='configure_position_table'), ]
        mm = MenuManager(*actions)
        return mm


class GroupedPositionsAdapter(TabularAdapter, ConfigurableMixin):
    columns = [('Identifier', 'identifier'),
               ('Irradiation', 'irradiation_str'),
               ('Sample', 'sample'),
               ('Material', 'material'),
               ('Positions', 'position_str')]

    all_columns = [('Identifier', 'identifier'),
               ('Irradiation', 'irradiation_str'),
               ('Sample', 'sample'),
               ('Material', 'material'),
               ('Positions', 'position_str')]
    font = 'arial 12'
    identifier_width = Int(80)
    irradiation_str_width = Int(80)
    sample_width = Int(80)
    position_str_width = Int(80)

    def get_menu(self, obj, trait, row, column):
        actions = [Action(name='Configure', action='configure_grouped_position_table'), ]
        mm = MenuManager(*actions)
        return mm

    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        c = item.color
        if hasattr(c, '__iter__'):
            c = [x * 255 for x in c]
        return c

    def get_text_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        color = 'black'
        if hasattr(item.color, '__iter__'):
            if sum(item.color[:3]) < 1.5:
                color = 'white'
        return color


class BaseLoadPane(TraitsDockPane):
    display_load_name = Property(depends_on='model.load_name')
    display_tray_name = Property(depends_on='model.tray')

    def _get_display_load_name(self):
        if self.model.load_name:
            ret = '<font size=12 color="blue"><b>{} ({})</b></font>'.format(self.model.load_name,
                                                                             self.model.tray)
        else:
            ret = ''
        return ret


class PositionTableConfigurer(TableConfigurer):
    id = 'position_table'

    def traits_view(self):
        v = VGroup(UItem('columns',
                         style='custom',
                         editor=CheckListEditor(name='available_columns', cols=3)),
                   Item('font', enabled_when='fontsize_enabled'))
        return okcancel_view(v,
                             # kind='modal',
                             title='Configure Position Table',
                             handler=TableConfigurerHandler())


class GroupedPositionTableConfigurer(TableConfigurer):
    id = 'grouped_position_table'

    def traits_view(self):
        v = VGroup(UItem('columns',
                         style='custom',
                         editor=CheckListEditor(name='available_columns', cols=3)),
                   Item('font', enabled_when='fontsize_enabled'))
        return okcancel_view(v,
                             # kind='modal',
                             title='Configure Grouped Position Table',
                             handler=TableConfigurerHandler())


class LoadTableHandler(Handler):
    def configure_position_table(self, info, obj):
        pane = info.ui.context['pane']
        tb = pane.position_configurer
        tb.edit_traits()

    def configure_grouped_position_table(self, info, obj):
        pane = info.ui.context['pane']
        tb = pane.grouped_position_configurer
        tb.edit_traits()


class LoadTablePane(BaseLoadPane):
    name = 'Positions'
    id = 'pychron.loading.positions'

    position_configurer = Instance(PositionTableConfigurer)
    grouped_position_configurer = Instance(GroupedPositionTableConfigurer)

    position_adapter = Instance(PositionsAdapter)
    grouped_position_adapter = Instance(GroupedPositionsAdapter)

    def __init__(self, *args, **kw):
        super(LoadTablePane, self).__init__(*args, **kw)
        self.position_configurer.load()
        self.grouped_position_configurer.load()

    def _position_configurer_default(self):
        c = PositionTableConfigurer()
        c.set_adapter(self.position_adapter)
        return c

    def _grouped_position_configurer_default(self):
        c = GroupedPositionTableConfigurer()
        c.set_adapter(self.grouped_position_adapter)
        return c

    def _position_adapter_default(self):
        return PositionsAdapter()

    def _grouped_position_adapter_default(self):
        return GroupedPositionsAdapter()

    def traits_view(self):
        a = HGroup(spring, UItem('pane.display_load_name', style='readonly'), spring)

        b = UItem('positions',
                  editor=TabularEditor(adapter=self.position_adapter,
                                       multi_select=True))
        c = UItem('grouped_positions',
                  label='Grouped Positions',
                  editor=TabularEditor(adapter=self.grouped_position_adapter))

        v = View(VGroup(spring, a, Tabbed(b, c)), handler=LoadTableHandler())
        return v


class LoadPane(TraitsTaskPane):
    def traits_view(self):
        v = View(VGroup(UItem('canvas',
                              style='custom',
                              editor=ComponentEditor())))
        return v


class LoadDockPane(BaseLoadPane):
    name = 'Load'
    id = 'pychron.loading.load'

    def traits_view(self):
        a = HGroup(Item('pane.display_load_name', style='readonly', label='Load'), spring)
        b = UItem('canvas',
                  style='custom',
                  editor=ComponentEditor())
        v = View(VGroup(a, b))

        return v


class LoadControlPane(TraitsDockPane):
    name = 'Load'
    id = 'pychron.loading.controls'

    def traits_view(self):
        notegrp = VGroup(Item('retain_note',
                              tooltip='Retain the Note for the next hole',
                              label='Lock'),
                         Item('note', style='custom', show_label=False),
                         show_border=True,
                         label='Note')

        viewgrp = VGroup(HGroup(Item('use_cmap', label='Color Map'),
                                UItem('cmap_name', enabled_when='use_cmap')),
                         Item('show_hole_numbers'),
                         Item('show_identifiers'),
                         Item('show_samples'),
                         Item('show_weights'),
                         Item('show_nxtals'),
                         # Item('show_spans'),
                         show_border=True,
                         label='View')

        load_grp = VGroup(Item('username', label='User', editor=EnumEditor(name='available_user_names')),
                          HGroup(Item('load_name',
                                      editor=EnumEditor(name='loads'),
                                      label='Loads'),
                                 icon_button_editor('add_button', 'add', tooltip='Add a load'),
                                 icon_button_editor('delete_button', 'delete', tooltip='Delete selected load'),
                                 icon_button_editor('archive_button', 'application-x-archive',
                                                    tooltip='Archive a set of loads')),
                          label='Load',
                          show_border=True)
        samplegrp = VGroup(HGroup(UItem('irradiation', editor=EnumEditor(name='irradiations')),
                                  UItem('level', editor=EnumEditor(name='levels')),
                                  UItem('identifier', editor=EnumEditor(name='identifiers'))),
                           Item('sample_info', style='readonly'),
                           Item('packet', style='readonly'),
                           HGroup(Item('weight', label='Weight (mg)', springy=True),
                                  Item('retain_weight', label='Lock',
                                       tooltip='Retain the Weight for the next hole')),
                           HGroup(Item('nxtals', label='N. Xtals', springy=True),
                                  Item('retain_nxtals', label='Lock',
                                       tooltip='Retain the N. Xtals for the next hole')),
                           HGroup(Item('npositions', label='NPositions', springy=True),
                                  Item('auto_increment')),
                           enabled_when='load_name',
                           show_border=True,
                           label='Sample')

        v = View(VGroup(load_grp,
                        samplegrp,
                        notegrp,
                        viewgrp))
        return v

# ============= EOF =============================================
