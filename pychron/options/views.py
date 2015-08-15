# ===============================================================================
# Copyright 2015 Jake Ross
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
from traitsui.api import View, UItem, Item, HGroup, VGroup, EnumEditor, ListStrEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor

agrp = HGroup(Item('selected', show_label=False,
                   editor=EnumEditor(name='names'),
                   tooltip='List of available plot options'),
              icon_button_editor('controller.add_options',
                                 'add',
                                 tooltip='Add new plot options', ),
              icon_button_editor('controller.delete_options',
                                 'delete',
                                 tooltip='Delete current plot options',
                                 enabled_when='object.plotter_options.name!="Default"', ),
              icon_button_editor('controller.save_options', 'disk',
                                 tooltip='Save changes to options'),
              icon_button_editor('controller.factory_default', 'edit-bomb',
                                 tooltip='Apply factory defaults')),
# sgrp = VGroup(UItem('selected_subview',
#                     editor=ListStrEditor(name='subview_names')))
sgrp = UItem('subview_names',
             width=0.1,
             editor=ListStrEditor(editable=False,
                                  selected='selected_subview'))
ogrp = UItem('subview',
             width=0.9,
             style='custom')
bgrp = HGroup(sgrp, ogrp)
IdeogramOptionsView = View(VGroup(agrp, bgrp),
                           # width=800,
                           height=700,
                           resizable=True,
                           title='Ideogram Options',
                           buttons=['OK', 'Cancel'])
# ============= EOF =============================================
