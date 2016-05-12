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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, Item, HGroup, VGroup, TabularEditor, EnumEditor, spring, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter

from pychron.envisage.icon_button_editor import icon_button_editor


class SamplesAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Material', 'material'),
               ('Grainsize', 'grainsize'),
               # ('Crushed', 'crushed')
               ]


class SimpleSampleAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Material', 'material'),
               ('Grainsize', 'grainsize')]


class PrepStepAdapter(TabularAdapter):
    columns = [('Date', 'timestamp'),
               ('Crush', 'crush'),
               ('Sieve', 'sieve'),
               ('Wash', 'wash'),
               ('Frantz', 'frantz'),
               ('Acid', 'acid'),
               ('Heavy_liquid', 'heavy_liquid'),
               ('Pick', 'pick'),
               ]


class SamplePrepPane(TraitsTaskPane):
    def traits_view(self):
        hgrp = VGroup(UItem('object.active_sample.steps', editor=TabularEditor(adapter=PrepStepAdapter(),
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
                             spring,
                             UItem('object.active_sample.name', style='readonly'),
                             spring),
                      Tabbed(hgrp, ngrp),
                      enabled_when='object.active_sample.name')

        v = View(VGroup(UItem('session_samples', editor=TabularEditor(adapter=SamplesAdapter(),
                                                                      editable=False,
                                                                      selected='active_sample')),
                        agrp))
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
