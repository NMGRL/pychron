#===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import HasTraits, Str, Bool, Float, List, on_trait_change, \
     Range, Instance
from traitsui.api import View, Item, VGroup, TableEditor, Group, HGroup
from apptools.preferences.ui.api import PreferencesPage
from traitsui.table_column import ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn
#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.initialization_parser import InitializationParser


class CItem(HasTraits):
    enabled = Bool
    name = Str

class ManagerPreferencesPage(PreferencesPage):
    '''
        abstract class. should not be used directly
        
        ensure subclass sets plugin_name
        
    '''
    devices = List(transient=True)
    managers = List(transient=True)
    plugin_name = None

    open_on_startup = Bool
    enable_close_after = Bool
    close_after = Range(0, 60, 60)

    width = Float(-1)
    height = Float(0.85)
    x = Float(10)
    y = Float(20)

    parser = Instance(InitializationParser, (), transient=True)


    @on_trait_change('managers:enabled')
    def _managers_changed(self, obj, name, old, new):
        if new:
            self.parser.enable_manager(obj.name, self.plugin_name)
        else:
            self.parser.disable_manager(obj.name, self.plugin_name)

    @on_trait_change('devices:enabled')
    def _devices_changed(self, obj, name, old, new):
        if new:
            self.parser.enable_device(obj.name, self.plugin_name)
        else:
            self.parser.disable_device(obj.name, self.plugin_name)

    def _managers_default(self):

        r = []
        # get the plugin this manager belongs to
        plugin = self.parser.get_plugin(self.plugin_name)
        mans = self.parser.get_managers(plugin, element=True, all_=True)
        if mans is not None:
            r = [CItem(enabled=True if m.get('enabled').lower() == 'true' else False,
                       name=m.text.strip()
                        )
                        for m in mans]
        return r

    def _devices_default(self):
        r = []

        # get the plugin this manager belongs to
        plugin = self.parser.get_plugin(self.plugin_name)

        devs = self.parser.get_devices(plugin, element=True, all_=True)
        if devs is not None:
            r = [CItem(enabled=True if d.get('enabled').lower() == 'true' else False,
                       name=d.text.strip()
                        )
                        for d in devs]
        return r

    def get_additional_groups(self):
        return []

    def get_general_group(self):
        window_grp = Group('width',
                          'height',
                          'x', 'y')
        return Group(Item('open_on_startup'),
                     HGroup(
                            Item('close_after', enabled_when='enable_close_after'),
                            Item('enable_close_after', show_label=False)
                            ),
                     window_grp

                    )

#============= views ===================================
    def traits_view(self):
        '''
        '''

        cols = [CheckboxColumn(name='enabled',
                             ),
                ObjectColumn(name='name', editable=False)
                             ]
        table_editor = TableEditor(columns=cols)

        devices_group = VGroup(Item('devices', show_label=False,
                                    editor=table_editor,
                                    height=400
                                    ),
                                label='Devices'
                              )
        manager_group = VGroup(Item('managers', show_label=False,
                                    editor=table_editor,
                                    height=400
                                    ),
                                label='Managers'
                              )


        grp = Group(
                  manager_group,
                  devices_group,
                  layout='tabbed')
        ggrp = self.get_general_group()
        if ggrp is not None:
            ggrp.label = 'General'
            grp.content.insert(0, ggrp)
        for ag in self.get_additional_groups():
            grp.content.append(ag)

        v = View(
                 grp
                 )
        return v
#============= EOF ==============================================
