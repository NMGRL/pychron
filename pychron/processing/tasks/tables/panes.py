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
from traitsui.api import View, Item, VGroup, EnumEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane

#============= standard library imports ========================
#============= local library imports  ==========================

class TableEditorPane(TraitsDockPane):
    name = 'Table Editor'
    def traits_view(self):
        v = View(
                 VGroup(
                        Item('use_auto_title'),
                        Item('title'),
                        Item('table_num'),
                        Item('subtitle_font_size'),
                        Item('use_alternating_background'),
                        Item('notes_template', editor=EnumEditor(name='notes_templates')),
                        Item('age_kind', editor=EnumEditor(name='age_kinds')),
#                         constants_grp,
                        )

                 )
        return v
#============= EOF =============================================
