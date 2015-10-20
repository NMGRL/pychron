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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, List, Instance
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.offline_bridge import OfflineBridge
from pychron.processing.export.destinations import SQLiteDestination
from pychron.processing.export.exporter import Exporter


class SQLiteAnalysisExporter(Exporter):
    analyses = List
    iso_manager = Any

    destination = Instance(SQLiteDestination, ())
    history_limit = Int(1)

    def add(self, analysis):
        self.analyses.append(analysis)

    def edit_view(self):
        v = View(VGroup(Item('destination', style='custom', label='Destination'),
                        Item('history_limit', label='History Limit',
                             tooltip='Only export the last N data reduction history entries')),
                 width=500,
                 buttons=['OK', 'Cancel'],
                 title='Export Options',
                 kind='livemodal')
        return v

    def export(self, *args, **kw):
        info = self.edit_traits(view='edit_view')
        if info.result:
            db = self.iso_manager.db

            bridge = OfflineBridge()
            bridge.init(self.destination.destination, overwrite=True)

            progress = self.iso_manager.open_progress(len(self.analyses))
            with db.session_ctx():
                bridge.add_analyses(db, self.analyses, progress)

            progress.close()

# ============= EOF =============================================



