#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, DelegatesTo, Button
from traitsui.api import Item, VGroup, HGroup, spring, Group, UItem
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.bakeout.bakeout_graph_viewer import BakeoutGraphViewer
from pychron.database.records.sqlite_record import SQLiteRecord

class BakeoutRecord(SQLiteRecord):
    viewer = Instance(BakeoutGraphViewer)
    graph = DelegatesTo('viewer')
    summary = DelegatesTo('viewer')
    export_button = Button

    window_width = 800
    window_height = 0.85
    def _export_button_fired(self):
        self.viewer.export()

    def create(self, dbrecord):
        self._dbrecord = dbrecord
        return True

    def load_graph(self, *args, **kw):
        self.viewer = BakeoutGraphViewer(title=self.title)
        self.viewer.load(self.path)

    def traits_view(self):
        readonly = lambda x, **kw: Item(x, style='readonly', ** kw)

        info_grp = VGroup(
                          readonly('record_id', label='ID'),
                          readonly('rundate', label='Date'),
                          readonly('runtime', label='Time'),
                          readonly('path', label='Path'),
                          UItem('summary', style='custom'),
                          label='Info'
                          )
        graph_grp = UItem('graph', style='custom')

        grp = Group(
                  graph_grp,
                  info_grp,
                  layout='tabbed'
                  )
        button_grp = HGroup(spring,
                            UItem('export_button')
                            )
        v = self.view_factory(VGroup(grp,
                                     button_grp
                                     ))
        return v
#============= EOF =============================================
