# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Property, Int
from traitsui.api import View, Item, InstanceEditor, UItem, HGroup, VGroup
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.tabular_editor import myTabularEditor


class SensitivityAdapter(TabularAdapter):
    columns = [
        ('Spectrometer', 'mass_spectrometer'),
        ('Sensitivity', 'sensitivity'),
        ('Units', 'units'),
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
    # def _set_create_date_text(self, v):
    #     pass
    #
    def _get_create_date_text(self, *args, **kw):
        return str(self.item.create_date or '')

    #         return self.item.create_date or ''
    #
    # def get_can_edit(self, obj, trait, row):
    #     item = getattr(obj, trait)[row]
    #     return item.primary_key is None or item.editable


SVIEW = View(HGroup(Item('mass_spectrometer'), Item('sensitivity'), Item('units')),
             HGroup(UItem('note', style='custom'), label='Note', show_border=True))


class SensitivityPane(TraitsTaskPane):
    id = 'pychron.entry.sensitivity'

    def traits_view(self):
        v = okcancel_view(VGroup(UItem('records',
                                       editor=myTabularEditor(adapter=SensitivityAdapter(),
                                                              editable=False,
                                                              auto_update=True,
                                                              selected='selected')),
                                 UItem('selected', style='custom', editor=InstanceEditor(view=SVIEW))),
                          width=600,
                          title='Sensitivity')
        return v

    def readonly_view(self):
        v = okcancel_view(Item('records',
                               editor=myTabularEditor(adapter=SensitivityAdapter(),
                                                      editable=False,
                                                      selected='selected'),
                               show_label=False),
                          width=600,
                          title='Sensitivity')
        return v

# ============= EOF =============================================
