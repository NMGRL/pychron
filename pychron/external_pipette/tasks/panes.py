# ===============================================================================
# Copyright 2014 Jake Ross
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
from traitsui.api import View, UItem, VGroup, HGroup, spring, EnumEditor, Item

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor


class ExternalPipettePane(TraitsTaskPane):
    def traits_view(self):
        command_entry = HGroup(UItem('test_command'),
                               UItem('test_button', enabled_when='test_enabled'),
                               UItem('test_command',
                                     editor=EnumEditor(values={'100': '01:List blanks',
                                                               '101': '02:List airs',
                                                               '102': '03:Last runid',
                                                               '103': '04:Get record',
                                                               '104': '05:Status',
                                                               '105,': '06:Load blank',
                                                               '106,': '07:Load air',
                                                               '107': '08:Cancel',
                                                               '108': '09:Set external pumping', })))

        response = VGroup(UItem('test_command_response', style='custom'),
                          HGroup(UItem('test_script_button',
                                       enabled_when='not testing'), spring),
                          HGroup(icon_button_editor('clear_test_response_button',
                                                    'clear', tooltip='Clear console'),
                                 Item('display_response_info', label='Display Debug Info.'),
                                 spring))

        connection_grp = Item('object.controller.connection_url', style='readonly', label='URL')
        v = View(VGroup(connection_grp,
                        command_entry,
                        response))

        # testing_grp = VGroup(HGroup(UItem('test_load_1', ),
        #                             UItem('test_script_button', ),
        #                             enabled_when='not testing'),
        #                      Item('test_result',
        #                           style='readonly',
        #                           label='Test Result'),)
        # canvas_button_grp = HGroup(UItem('reload_canvas_button'), spring)
        # v = View(VGroup(testing_grp,
        #                 canvas_button_grp,
        #                 UItem('canvas', style='custom',
        #                       editor=ComponentEditor())))
        return v

# ============= EOF =============================================

