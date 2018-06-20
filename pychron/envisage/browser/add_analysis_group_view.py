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

from __future__ import absolute_import

from pyface.message_dialog import warning
from traits.api import Str, HasTraits, Dict, Any
from traitsui.api import View, Item, EnumEditor


# ============= standard library imports ========================
# ============= local library imports  ==========================


class AddAnalysisGroupView(HasTraits):
    name = Str
    project = Any
    projects = Dict

    def save(self, ans, db):
        append = False
        if not self.name:
            warning(None, 'Please specify a name for the analysis group')
            return

        if not self.project:
            warning(None, 'Please specify an associated project for the analysis group')
            return

        gdb = db.get_analysis_groups_by_name(self.name, self.project)
        ok = True
        if gdb:
            gdb = gdb[-1]
            if db.confirmation_dialog('"{}" already exists? Would you like to append your selection'.format(gdb.name)):
                append = True
            else:
                ok = False

        if append:
            db.append_analysis_group(gdb, ans)
        elif ok:
            db.add_analysis_group(ans, self.name, self.project)

        return True

    def traits_view(self):
        v = View(Item('name'),
                 Item('project', editor=EnumEditor(name='projects')),
                 resizable=True,
                 buttons=['OK', 'Cancel'],
                 title='Add Analysis Group')
        return v

# ============= EOF =============================================
