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

# ============= enthought library imports =======================
from traits.api import HasTraits, List, Int, Property, Str
from traitsui.api import Controller, View, UItem, TabularEditor, VGroup

from pychron.entry.irradiated_position import IrradiatedPositionAdapter


class IrradiationPositionStatus(HasTraits):
    n = Int
    sample = Str
    project = Str
    principal_investigator = Str

    def __init__(self, dbpos, *args, **kw):
        super(IrradiationPositionStatus, self).__init__(*args, **kw)

        ans = dbpos.analyses
        sam = dbpos.sample

        self.n = len(ans)
        self.sample = sam.name
        self.project = sam.project.name
        self.principal_investigator = sam.project.principal_investigator.name


class IrradiationStatusModel(HasTraits):
    positions = List
    filtered_positions = Property(depends_on='positions')

    def _get_filtered_positions(self):
        fp = self.positions
        return fp


class IrradiationStatusView(Controller):
    def traits_view(self):
        v = View(VGroup(UItem('filtered_positions',
                              editor=TabularEditor(adapter=IrradiatedPositionAdapter())),
                        show_border=True,
                        label='Non Analyzed Positions'),
                 resizable=True,
                 kind='modal',
                 buttons=['OK'],
                 title='Irradiation Status Report')
        return v

# ============= EOF =============================================
