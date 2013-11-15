#===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.action.action import Action
from pyface.tasks.action.task_action import TaskAction
from pyface.image_resource import ImageResource
from pychron.paths import paths
#============= standard library imports ========================
#============= local library imports  ==========================

class LabnumberEntryAction(Action):
    name = 'Labnumber Entry'
    accelerator = 'Ctrl+Shift+l'

    def perform(self, event):
        pid = 'pychron.entry.labnumber'
        app = event.task.window.application
        app.get_task(pid)


class SensitivityEntryAction(Action):
    name = 'Sensitivity'
    accelerator = 'Ctrl+Shift+\\'

    def perform(self, event):
        pid = 'pychron.entry.sensitivity'
        app = event.task.window.application
        app.get_task(pid)


class SaveSensitivityAction(TaskAction):
    name = 'Save'
    image = ImageResource(name='database_save.png',
                          search_path=paths.icon_search_path)
    method = 'save'


class AddSensitivityAction(TaskAction):
    name = 'Add'
    image = ImageResource(name='database_add.png',
                          search_path=paths.icon_search_path)
    method = 'add'


class SavePDFAction(TaskAction):
    name = 'Save PDF'
    image = ImageResource(name='file_pdf.png',
                          search_path=paths.icon_search_path)
    method = 'save_pdf'


class SaveLabbookPDFAction(TaskAction):
    name = 'Save Labbook'
    image = ImageResource(name='file_pdf.png',
                          search_path=paths.icon_search_path)
    method = 'save_labbook_pdf'


class GenerateLabnumbersAction(TaskAction):
    name = 'Generate Labnumbers'
    image = ImageResource(name='table_lightning.png',
                          search_path=paths.icon_search_path)
    method = 'generate_labnumbers'


class ImportIrradiationLevelAction(TaskAction):
    name = 'Import Level'
    image = ImageResource(name='file_xls.png',
                          search_path=paths.icon_search_path)
    method = 'import_irradiation_load_xls'


class MakeIrradiationTemplateAction(TaskAction):
    name = 'Irradiation Template'
    image = ImageResource(name='file_xls.png',
                          search_path=paths.icon_search_path)
    method = 'make_irradiation_load_template'

#============= EOF =============================================
