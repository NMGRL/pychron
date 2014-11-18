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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.resources import icon


class AddMolecularWeightAction(Action):
    name = 'Add/Edit Molecular Weight'

    def perform(self, event):
        app = event.task.window.application
        s = app.get_service('pychron.entry.editors.molecular_weight_editor.MolecularWeightEditor')
        s.add_molecular_weight()


class AddFluxMonitorAction(Action):
    name = 'Add/Edit Flux Monitors'

    def perform(self, event):
        app = event.task.window.application
        s = app.get_service('pychron.entry.editors.flux_monitor_editor.FluxMonitorEditor')
        s.add_flux_monitor()


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
    image = icon('database_save.png')
    method = 'save'


class AddSensitivityAction(TaskAction):
    name = 'Add'
    image = icon(name='database_add.png')
    method = 'add'


class SavePDFAction(TaskAction):
    name = 'Save PDF'
    image = icon('file_pdf.png')

    method = 'save_pdf'


class SaveLabbookPDFAction(TaskAction):
    name = 'Save Labbook'
    image = icon('file_pdf.png')

    method = 'save_labbook_pdf'


class GenerateLabnumbersAction(TaskAction):
    name = 'Generate Labnumbers'
    image = icon('table_lightning.png')

    method = 'generate_labnumbers'

class GenerateTrayAction(TaskAction):
    name = 'Generate Tray'
    image = icon('table_lightning.png')

    method = 'generate_tray'

class ImportIrradiationLevelAction(TaskAction):
    name = 'Import Level'
    image = icon('file_xls.png')

    method = 'import_irradiation_load_xls'


class MakeIrradiationTemplateAction(TaskAction):
    name = 'Irradiation Template'
    image = icon('file_xls.png')

    method = 'make_irradiation_load_template'


class ImportSampleMetadataAction(TaskAction):
    name = 'Import Sample Metadata...'
    method = 'import_sample_metadata'


class GenerateIrradiationTableAction(Action):
    name = 'Generate Irradiation Table'
    accelerator = 'Ctrl+0'

    def perform(self, event):
        from pychron.entry.irradiation_table_writer import IrradiationTableWriter

        a = IrradiationTableWriter()
        a.make()


class ImportIrradiationHolderAction(Action):
    name = 'Import Irradiation Holder'

    def perform(self, event):
        from pychron.entry.loaders.irradiation_holder_loader import IrradiationHolderLoader
        from pychron.database.isotope_database_manager import IsotopeDatabaseManager
        man=IsotopeDatabaseManager()
        db=man.db
        if db.connect():
            a = IrradiationHolderLoader()
            a.do_import(db)

#============= EOF =============================================
