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
from traits.api import HasTraits, List, Any, Str
from traitsui.api import View, Item, TabularEditor, UItem, HGroup, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.browser.adapters import ProjectAdapter


class SaveGroupDialog(HasTraits):
    name = Str
    projects = List
    selected_project = Any

    def traits_view(self):
        v = View(VGroup(HGroup(Item('name')),
                        UItem('projects',
                              editor=TabularEditor(adapter=ProjectAdapter(),
                                                   selected='selected_project',
                                                   editable=False))),
                 buttons=['OK', 'Cancel'], resizable=True,
                 title='Save Interpreted Age Group')
        return v

#============= EOF =============================================

