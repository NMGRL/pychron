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
# from pyface.action.action import Action
# from pyface.tasks.action.task_action import TaskAction
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.envisage.tasks.actions import PAction as Action, PTaskAction as TaskAction


class AddMolecularWeightAction(Action):
    name = 'Add/Edit Molecular Weight'
    dname = 'Add/Edit Molecular Weight'

    def perform(self, event):
        app = event.task.window.application
        s = app.get_service('pychron.entry.editors.molecular_weight_editor.MolecularWeightEditor')
        s.add_molecular_weight()


class AddFluxMonitorAction(Action):
    name = 'Add/Edit Flux Monitors'
    dname = 'Add/Edit Flux Monitors'

    def perform(self, event):
        app = event.task.window.application
        s = app.get_service('pychron.entry.editors.flux_monitor_editor.FluxMonitorEditor')
        s.add_flux_monitor()


class LabnumberEntryAction(Action):
    name = 'Labnumber Entry'
    dname = 'Labnumber Entry'
    # accelerator = 'Ctrl+Shift+l'
    id = 'pychron.labnumber_entry'

    def perform(self, event):
        pid = 'pychron.entry.irradiation.task'
        app = event.task.window.application
        app.get_task(pid)


class SensitivityEntryAction(Action):
    name = 'Sensitivity'
    dname = 'Sensitivity'
    # accelerator = 'Ctrl+Shift+\\'
    id = 'pychron.sensitivity'

    def perform(self, event):
        pid = 'pychron.entry.sensitivity.task'
        app = event.task.window.application
        app.get_task(pid)


class SaveSensitivityAction(TaskAction):
    name = 'Save'
    dname = 'Save'
    image = icon('database_save')
    method = 'save'


class AddSensitivityAction(TaskAction):
    name = 'Add'
    dname = 'Add'
    image = icon('database_add')
    method = 'add'


class SavePDFAction(TaskAction):
    name = 'Save PDF'
    dname = 'Save PDF'
    image = icon('file_pdf')

    method = 'save_pdf'


class SaveLabbookPDFAction(TaskAction):
    name = 'Save Labbook'
    dname = 'Save Labbook'
    image = icon('file_pdf')

    method = 'save_labbook_pdf'


class GenerateLabnumbersAction(TaskAction):
    name = 'Generate Labnumbers'
    dname = 'Generate Labnumbers'
    image = icon('table_lightning')

    method = 'generate_labnumbers'

    ddescription = 'Automatically generate labnumbers (aka identifiers) for each irradiation position in the ' \
                   'currently selected irradiation.'


class PreviewGenerateLabnumbersAction(TaskAction):
    name = 'Preview Generate Labnumbers'
    dname = 'Preview Generate Labnumbers'
    image = icon('table_lightning')

    method = 'preview_generate_labnumbers'


class ImportIrradiationAction(TaskAction):
    name = 'Import Irradiation...'
    dname = 'Import Irradiation'
    method = 'import_irradiation'


class GenerateTrayAction(TaskAction):
    name = 'Generate Tray'
    dname = 'Generate Tray'
    image = icon('table_lightning')

    method = 'generate_tray'
    ddescription = 'Make a irradiation tray image from an irradiation tray text file.'


class ImportIrradiationFileAction(TaskAction):
    name = 'Import Irradiation File'
    dname = 'Import Irradiation File'
    image = icon('file_xls')

    method = 'import_irradiation_load_xls'
    ddescription = 'Import irradiation information from an Excel file. Use "Irradiation Template" ' \
                   'to generate a boilerplate irradiation template'


class MakeIrradiationTemplateAction(TaskAction):
    name = 'Irradiation Template'
    dname = 'Irradiation Template'
    image = icon('file_xls')

    method = 'make_irradiation_load_template'
    ddescription = 'Make an Excel irradiation template that can be used to import irradiation information.'


class ImportSamplesAction(TaskAction):
    name = 'Import Sample File'
    dname = 'Import Sample File'
    method = 'import_sample_from_file'


class ImportSampleMetadataAction(TaskAction):
    name = 'Import Sample Metadata...'
    dname = 'Import Sample Metadata'
    method = 'import_sample_metadata'


class ExportIrradiationAction(TaskAction):
    name = 'Export Irradiation...'
    dname = 'Export Irradiation'
    method = 'export_irradiation'


class GenerateIrradiationTableAction(Action):
    name = 'Generate Irradiation Table'
    dname = 'Generate Irradiation Table'
    accelerator = 'Ctrl+0'

    ddescription = 'Do not use!'

    def perform(self, event):
        from pychron.entry.irradiation_table_writer import IrradiationTableWriter

        a = IrradiationTableWriter()
        a.make()


class ImportIrradiationHolderAction(Action):

    name = 'Import Irradiation Holder'
    dname = 'Import Irradiation Holder'

    def perform(self, event):
        from pychron.entry.loaders.irradiation_holder_loader import IrradiationHolderLoader
        from pychron.database.isotope_database_manager import IsotopeDatabaseManager

        man = IsotopeDatabaseManager()
        db = man.db
        if db.connect():
            a = IrradiationHolderLoader()
            a.do_import(db)


class TransferJAction(TaskAction):
    name = 'Transfer J Data...'
    dname = 'Transfer J Data'
    method = 'transfer_j'
# ============= EOF =============================================
