# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
from traitsui.api import Controller, View, UItem, Item, HGroup, VGroup, EnumEditor


# ============= local library imports  ==========================


class ProjectOptionalsView(Controller):
    def traits_view(self):
        lc_grp = HGroup(UItem('lock_project_lab_contact',
                              label='Lab Contact',
                              tooltip='Prevent Lab Contact from being automatically cleared'),
                        Item('project_lab_contact',
                             editor=EnumEditor(name='lab_contacts')))

        i_grp = HGroup(UItem('lock_project_institution',
                             tooltip='Prevent Institution from being automatically cleared'),
                       Item('project_institution', label='Institution'))

        c_grp = HGroup(UItem('lock_project_comment',
                             tooltip='Prevent Comment from being automatically cleared'),
                       VGroup(UItem('project_comment', style='custom'), label='Comment', show_border=True))
        v = View(VGroup(lc_grp, i_grp, c_grp),
                 buttons=['OK', 'Cancel'],
                 resizable=True,
                 title='Set Optional Project Values')
        return v

# ============= EOF =============================================
