#===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================
#============= local library imports  ==========================

#============= EOF =============================================
from pychron.envisage.resources import icon


class SavePDFTablesAction(TaskAction):
    name = 'Save PDF Tables'
    method = 'save_pdf_tables'
    image = icon('file_pdf')


class SaveInterpretedAgeGroupAction(TaskAction):
    name = 'Save Group'
    method = 'save_interpreted_age_group'
    image = icon('database_add')


class OpenInterpretedAgeGroupAction(TaskAction):
    name = 'Open Group'
    method = 'open_interpreted_age_group'
    image = icon('database_go')


# class OpenTableAction(TaskAction):
#     name = 'Open Table'
#     method = 'open_table'
#     image = icon('database_go')
