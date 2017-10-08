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
from traitsui.api import View, UItem, HGroup, VGroup
from traitsui.editors import EnumEditor
from traitsui.handler import Controller
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor


class NewBranchView(Controller):
    def traits_view(self):
        v = View(UItem('new_branch_name'),
                 title='New Branch Name',
                 width=300,
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v


class ManageBranchView(Controller):
    def traits_view(self):
        v = View(
            VGroup(
                VGroup(HGroup(UItem('branch', editor=EnumEditor(name='all_branches')),
                              # icon_button_editor('build_button', 'bricks',
                              #                    tooltip='Build selected branch and set as current application'),
                              icon_button_editor('checkout_branch_button', 'bricks',
                                                 tooltip='Checkout selected branch'),
                              icon_button_editor('pull_button', 'arrow_down',
                                                 tooltip='Update Branch'),
                              show_border=True,
                              label='Current Branch'))),
            # VGroup(UItem('edit_branch', editor=EnumEditor(name='branches')),
            #        UItem('delete_button', enabled_when='delete_enabled'),
            #        show_border=True)),
            title='Manage Branch View',
            buttons=['OK', 'Cancel'])
        return v

# ============= EOF =============================================
