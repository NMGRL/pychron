# ===============================================================================
# Copyright 2016 Jake Ross
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
from pyface.action.menu_manager import MenuManager
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Int, Property
from traitsui.api import View, UItem, Item, HGroup, VGroup, TabularEditor, EnumEditor, spring, Tabbed, Handler
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.resources import icon

IMAGE_ICON = icon('image')


class SamplesAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Material', 'material'),
               ('Grainsize', 'grainsize')]
    font = 'arial 10'
    odd_bg_color = '#d6f5f5'

    def get_menu(self, obj, trait, row, column):
        # item = getattr(obj, trait)[row]
        actions = [Action(name='Move', action='move_to_session')]
        menu = MenuManager(*actions)
        return menu


class SimpleSampleAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Material', 'material'),
               ('Grainsize', 'grainsize')]
    font = 'arial 10'
    odd_bg_color = '#d6f5f5'


class PrepStepAdapter(TabularAdapter):
    columns = [('Date', 'timestamp'),
               ('Crush', 'crush'),
               ('Sieve', 'sieve'),
               ('Wash', 'wash'),
               ('Frantz', 'frantz'),
               ('Acid', 'acid'),
               ('Heavy_liquid', 'heavy_liquid'),
               ('Pick', 'pick'),
               ('Image', 'nimages'),
               ('Comments', 'comment')]
    font = 'arial 10'
    odd_bg_color = '#f5f5d6'
    timestamp_width = Int(100)
    crush_width = Int(75)
    sieve_width = Int(75)
    wash_width = Int(75)
    frantz_width = Int(75)
    acid_width = Int(75)
    heavy_liquid_width = Int(80)
    frantz_width = Int(125)

    timestamp_text = Property
    nimages_text = Property
    nimages_image = Property

    # def get_image(self, obj, trait, row, column):
    #     name = self.column_map[column]
    #     if name == 'nimages':
    #         item = getattr(obj, trait)[row]
    #         if item.nimages:
    #             return IMAGE_ICON

    def _get_nimages_image(self):
        im = self.item.nimages
        return IMAGE_ICON if im else None

    def _get_nimages_text(self):
        ret = ''
        if self.item.nimages:
            ret = str(self.item.nimages)
        return ret

    def _get_timestamp_text(self):
        t = self.item.timestamp
        return t.strftime('%Y-%d-%m %H:%M')


class SamplePrepHandler(Handler):
    def move_to_session(self, info, obj):
        obj.move_to_session()


class SamplePrepPane(TraitsTaskPane):
    def traits_view(self):
        hgrp = VGroup(UItem('object.active_sample.steps', editor=TabularEditor(adapter=PrepStepAdapter(),
                                                                               selected='selected_step',
                                                                               dclicked='dclicked',
                                                                               editable=False)),
                      label='History')

        ngrp = VGroup(HGroup(Item('object.prep_step.crush',
                                  enabled_when='not object.prep_step.flag_crush'),
                             UItem('object.prep_step.flag_crush')),
                      HGroup(Item('object.prep_step.sieve',
                                  enabled_when='not object.prep_step.flag_sieve'),
                             UItem('object.prep_step.flag_sieve')),
                      HGroup(Item('object.prep_step.wash',
                                  enabled_when='not object.prep_step.flag_wash'),
                             UItem('object.prep_step.flag_wash')),
                      HGroup(Item('object.prep_step.frantz',
                                  enabled_when='not object.prep_step.flag_frantz'),
                             UItem('object.prep_step.flag_frantz')),
                      HGroup(Item('object.prep_step.heavy_liquid',
                                  enabled_when='not object.prep_step.flag_heavy_liquid'),
                             UItem('object.prep_step.flag_heavy_liquid')),
                      HGroup(Item('object.prep_step.acid',
                                  enabled_when='not object.prep_step.flag_acid'),
                             UItem('object.prep_step.flag_acid')),
                      HGroup(Item('object.prep_step.pick',
                                  enabled_when='not object.prep_step.flag_pick'),
                             UItem('object.prep_step.flag_pick')),
                      Item('object.prep_step.status'),
                      HGroup(Item('object.prep_step.comment'),
                             icon_button_editor('object.prep_step.edit_comment_button', 'cog')),
                      label='New')

        agrp = VGroup(HGroup(icon_button_editor('add_step_button', 'add',
                                                enabled_when='object.active_sample.name',
                                                tooltip='Add a sample prep step'),
                             icon_button_editor('upload_image_button', 'camera',
                                                tooltip='Add image'),
                             icon_button_editor('view_camera_button', 'camera1',
                                                tooltip='Take a picture'),
                             icon_button_editor('view_image_button', 'camera2',
                                                tooltip='View Associated Image'),
                             spring,
                             UItem('object.active_sample.name', style='readonly'),
                             spring),
                      Tabbed(hgrp, ngrp),
                      enabled_when='object.active_sample.name')

        fgrp = HGroup(Item('fcrush', label='Crush'),
                      spring,
                      Item('fsieve', label='Sieve'),
                      spring,
                      Item('fwash', label='Wash'),
                      spring,
                      Item('facid', label='Acid', ),
                      spring,
                      Item('fheavy_liquid', label='Heavy Liquid', ),
                      spring,
                      Item('fpick', label='Pick'),
                      spring,
                      Item('fstatus', label='Status'))

        v = View(VGroup(fgrp,
                        UItem('session_samples', editor=TabularEditor(adapter=SamplesAdapter(),
                                                                      editable=False,
                                                                      selected='active_sample')),
                        agrp),
                 handler=SamplePrepHandler())
        return v


class SamplePrepSessionPane(TraitsDockPane):
    name = 'Session'
    id = 'pychron.entry.sample.session'
    closable = False

    def traits_view(self):
        wgrp = HGroup(UItem('worker', editor=EnumEditor(name='workers')),
                      icon_button_editor('add_worker_button', 'add', tooltip='Add a new worker'),
                      show_border=True, label='Worker')
        sgrp = HGroup(UItem('session', editor=EnumEditor(name='sessions')),
                      icon_button_editor('add_session_button', 'add',
                                         tooltip='Add a new session for this worker'),
                      icon_button_editor('edit_session_button', 'application-form-edit',
                                         enabled_when='session',
                                         tooltip='Edit session'),
                      enabled_when='worker',
                      show_border=True, label='Session')
        v = View(VGroup(wgrp, sgrp))
        return v


class SamplePrepFilterPane(TraitsDockPane):
    name = 'Filter'
    id = 'pychron.entry.sample.filter'
    closable = False

    def traits_view(self):
        pigrp = VGroup(UItem('principal_investigator', editor=EnumEditor(name='principal_investigators')),
                       label='Principal Investigator',
                       show_border=True)
        pgrp = VGroup(UItem('project', editor=EnumEditor(name='projects')),
                      label='Project',
                      show_border=True)
        sgrp = VGroup(icon_button_editor('add_selection_button', 'add',
                                         enabled_when='selected',
                                         tooltip='Add selection to current Sample Prep Session'),
                      UItem('samples', editor=TabularEditor(adapter=SimpleSampleAdapter(),
                                                            multi_select=True,
                                                            selected='selected')))
        v = View(VGroup(pigrp, pgrp, sgrp))
        return v

# ============= EOF =============================================
