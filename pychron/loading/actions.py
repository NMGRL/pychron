# ===============================================================================
# Copyright 2013 Jake Ross
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

from pychron.envisage.resources import icon


# ============= standard library imports ========================
# ============= local library imports  ==========================

class SaveLoadingDBAction(TaskAction):
    name = 'Save DB'
    method = 'save_loading_db'
    image = icon('database_save')


class SaveLoadingPDFAction(TaskAction):
    name = 'Save PDF'
    method = 'save_loading_pdf'
    image = icon('file_pdf')


class ConfigurePDFAction(TaskAction):
    name = 'Configure PDF'
    method = 'configure_pdf'
    image = icon('cog')


class EntryAction(TaskAction):
    name = 'Entry'
    method = 'set_entry'


class InfoAction(TaskAction):
    name = 'Info'
    method = 'set_info'


class EditAction(TaskAction):
    name = 'Edit'
    method = 'set_edit'

# ============= EOF =============================================
