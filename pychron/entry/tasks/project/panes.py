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

from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Property
from traitsui.api import View, UItem, HGroup, VGroup, EnumEditor, VSplit, spring, Item
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class ProjectAdapter(TabularAdapter):
    columns = [('ProjectID', 'unique_id'),
               ('Name', 'name'),
               ('Lab Contact', 'lab_contact'),
               ('PI', 'principal_investigator'),
               ('Checkin', 'checkin_date'),
               ('Comment', 'comment')]

    checkin_date_text = Property

    def _get_checkin_date_text(self):
        ret = ''
        if self.item.checkin_date:
            ret = self.item.checkin_date
        return str(ret)


class ProjectPane(TraitsTaskPane):
    def traits_view(self):
        fgrp = HGroup(UItem('filter_attr', editor=EnumEditor(name='filter_attrs')), UItem('filter_str'))
        tgrp = VGroup(UItem('items', height=600, editor=myTabularEditor(adapter=ProjectAdapter(),
                                                                        editable=False,
                                                                        selected='selected',
                                                                        multi_select=True,
                                                                        refresh='refresh',
                                                                        scroll_to_row='scroll_to_row')))
        edit_grp = VGroup(Item('project_name', label='Project Name'),
                          VGroup(UItem('comment', style='custom'),
                                 enabled_when='selected',
                                 label='Comment', show_border=True),
                          HGroup(spring, icon_button_editor('save_button', 'database_save', tooltip='Save changes to '
                                                                                                    'database')))
        bgrp = VSplit(tgrp, edit_grp)
        g = VGroup(fgrp, bgrp)
        v = View(g)
        return v

# ============= EOF =============================================
