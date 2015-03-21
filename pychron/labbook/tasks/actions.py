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


class AddNoteAction(TaskAction):
    name = 'Add Note'
    method = 'add_note'
    image = icon('note-add')


class SaveNoteAction(TaskAction):
    name = 'Save Note'
    method = 'save_note'
    image = icon('document-save')


class AddFolderAction(TaskAction):
    name = 'Add Folder'
    method = 'add_folder'
    image = icon('folder-new')


class PushAction(TaskAction):
    name = 'Push'
    method = 'push'
    image = icon('arrow_up')


class PullAction(TaskAction):
    name = 'Pull'
    method = 'pull'
    image = icon('arrow_down')


class NewLabelAction(TaskAction):
    name = 'New Label'
    method = 'new_label'
    image = icon('add')

# ============= EOF =============================================



