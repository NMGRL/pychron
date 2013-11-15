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
from traits.api import Property, Int
from traitsui.api import View, Item
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.tabular_adapter import TabularAdapter

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.ui.tabular_editor import myTabularEditor


class SensitivityAdapter(TabularAdapter):
    columns = [
        #                ('', 'placeholder'),
        ('Spectrometer', 'mass_spectrometer'),
        ('Sensitivity', 'sensitivity'),
        ('User', 'user'),
        ('Date', 'create_date'),
        ('Note', 'note')]

    create_date_text = Property
    create_date_width = Int(175)
    sensitivity_width = Int(125)
    #     placeholder_text = Str('')
    #     placeholder_width = Int(2)

    font = 'arial 11'
    #    mass_spectrometer_width = Int(40)
    def _set_create_date_text(self, v):
        pass

    def _get_create_date_text(self, *args, **kw):
        return str(self.item.create_date or '')

    #         return self.item.create_date or ''

    def get_can_edit(self, obj, trait, row):
        item = getattr(obj, trait)[row]
        return item.primary_key is None or item.editable

#         return TabularAdapter.get_can_edit(self, object, trait, row)
class SensitivityPane(TraitsTaskPane):
    id = 'pychron.entry.sensitivty'

    def traits_view(self):
        v = View(Item('records',
                      editor=myTabularEditor(adapter=SensitivityAdapter(),
                                             paste_function='paste',
                                             #                                               editable=False,
                                             #                                               refresh='refresh_table',
                                             #                                               multi_select=True,
                                             selected='selected',
                                             operations=['edit']
                                             #                                                 operations=[]
                      ),
                      show_label=False
        ),
                 buttons=['OK', 'Cancel'],
                 width=600,
                 resizable=True,
                 title='Sensitivity'
        )
        return v

    def readonly_view(self):
        v = View(Item('records',
                      editor=myTabularEditor(adapter=SensitivityAdapter(),
                                             editable=False,
                                             selected='selected',
                      ),
                      show_label=False
        ),
                 buttons=['OK', 'Cancel'],
                 width=600,
                 resizable=True,
                 title='Sensitivity'
        )
        return v


#============= EOF =============================================
