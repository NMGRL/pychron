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
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Property
from traitsui.api import View, UItem, HGroup, VGroup, EnumEditor, VSplit, Item
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class IRAdapter(TabularAdapter):
    columns = [('IR', 'ir'),
               ('Lab Contact', 'lab_contact'),
               ('PI', 'principal_investigator_name'),
               ('Checkin', 'checkin_date'),
               ('Comment', 'comment')]

    checkin_date_text = Property

    def _get_checkin_date_text(self):
        ret = ''
        if self.item.checkin_date:
            ret = self.item.checkin_date
        return str(ret)


class IRPane(TraitsTaskPane):
    def traits_view(self):
        fgrp = HGroup(UItem('filter_attr', editor=EnumEditor(name='filter_attrs')), UItem('filter_str'))
        add_grp = VGroup(HGroup(Item('ir'),
                                Item('lab_contact', editor=EnumEditor(name='lab_contacts')),
                                Item('pi', editor=EnumEditor(name='pis'))),
                         Item('institution'),
                         VGroup(UItem('comment', style='custom'), label='Comment', show_border=True),
                         HGroup(icon_button_editor('add_button', 'add', enabled_when='ir')))
        tgrp = VGroup(UItem('items', height=600, editor=myTabularEditor(adapter=IRAdapter(),
                                                                        editable=False,
                                                                        scroll_to_row='scroll_to_row')))
        bgrp = VSplit(tgrp, add_grp)
        g = VGroup(fgrp, bgrp)
        v = View(g)
        return v

# ============= EOF =============================================
