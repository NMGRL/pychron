# ===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.tasks.action.task_action import TaskAction
from traits.api import HasTraits, Button
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon


class SnapshotAction(TaskAction):
    name = 'Snapshot'
    image = icon('camera')
    method = 'save_file_snapshot'


class DBSnapshotAction(TaskAction):
    name = 'DB Snapshot'
    image = icon('camera')
    method = 'save_db_snapshot'

# ============= EOF =============================================



