# ===============================================================================
# Copyright 2011 Jake Ross
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

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.core.database_adapter import  PathDatabaseAdapter
from pychron.database.orms.video_orm import VideoTable, VideoPathTable
from pychron.database.selectors.video_selector import VideoSelector
from pychron.paths import paths


class VideoAdapter(PathDatabaseAdapter):
    test_func = None
    selector_klass = VideoSelector
    path_table = VideoPathTable
#==============================================================================
#    getters
#==============================================================================

    def get_video_records(self, **kw):
        return self._get_items(VideoTable, globals(), **kw)
#=============================================================================
#   adder
#=============================================================================
    def add_video_record(self, **kw):
        b = self._add_timestamped_item(VideoTable, **kw)
        return b


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('vid')
    db = VideoAdapter(name=paths.co2laser_db, kind='sqlite')
    db.connect()

    dbs = VideoSelector(_db=db)

#    dbs.criteria = 'vm_recordingii'
#    dbs.parameter = 'VideoTable.rid'
#    dbs.comparator = 'like'
#    dbs._execute_query()
    dbs.load_recent()
#    si = dbs.results[0]
    dbs.configure_traits()
#    print db.get_bakeouts(join_table='ControllerTable',
#                    filter_str='ControllerTable.script="---"'
#                    )
# ============= EOF =============================================

