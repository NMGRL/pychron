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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon


class UploadAction(TaskAction):
    name = 'Upload'
    image = icon('image_add')
    method = 'upload_image_from_file'


class SnapshotAction(TaskAction):
    name = 'Snapshot'
    image = icon('camera')
    method = 'save_file_snapshot'


class DBSnapshotAction(TaskAction):
    name = 'DB Snapshot'
    image = icon('camera')
    method = 'save_db_snapshot'


class AssociateAction(TaskAction):
    name = 'Associate Sample'
    method = 'associate_sample'
    enabled_name = 'association_enabled'


class SaveAction(TaskAction):
    name = 'Save'
    method = 'save'
    image = icon('database_save')
    # enabled_name = 'save_enabled'
# ============= EOF =============================================



