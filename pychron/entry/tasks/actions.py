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


class DatabaseSaveAction(TaskAction):
    name = 'Database Save'
    dname = 'Database Save'
    description = 'Save current changes to the database'
    method = 'save_to_db'
    image = icon('database_save')


class ClearSelectionAction(TaskAction):
    name = 'Clear Selection'
    image = icon('table_lightning')
    method = 'clear_selection'


class RecoverAction(TaskAction):
    name = 'Recover'
    method = 'recover'


class SavePDFAction(TaskAction):
    name = 'Save PDF'
    dname = 'Save PDF'
    image = icon('file_pdf')

    method = 'save_pdf'


class MakeIrradiationBookPDFAction(TaskAction):
    name = 'Make Irradiation Book'
    dname = 'Make Irradiation Book'
    image = icon('file_pdf')

    method = 'make_irradiation_book_pdf'


class GenerateIdentifiersAction(TaskAction):
    name = 'Generate Identifiers'
    # dname = 'Generate Labnumbers'
    image = icon('table_lightning')

    method = 'generate_identifiers'

    ddescription = 'Automatically generate labnumbers (aka identifiers) for each irradiation position in the ' \
                   'currently selected irradiation.'


class PreviewGenerateIdentifiersAction(TaskAction):
    name = 'Preview Generate Identifiers'
    # dname = 'Preview Generate Labnumbers'
    image = icon('table_lightning')

    method = 'preview_generate_identifiers'


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


class MakeIrradiationTemplateAction(Action):
    name = 'Irradiation Template'
    dname = 'Irradiation Template'
    image = icon('file_xls')

    ddescription = 'Make an Excel irradiation template that can be used to import irradiation information.'

    def perform(self, event):
        from pyface.file_dialog import FileDialog
        dialog = FileDialog(action='save as', default_filename='IrradiationTemplate.xls')

        from pyface.constant import OK
        if dialog.open() == OK:
            path = dialog.path
            if path:
                from pychron.core.helpers.filetools import add_extension
                path = add_extension(path, '.xls')

                from pychron.entry.loaders.irradiation_template import IrradiationTemplate
                i = IrradiationTemplate()
                i.make_template(path)

                from pyface.confirmation_dialog import confirm
                if confirm(None, 'Template saved to {}.\n\nWould you like to open the template?'):
                    from pychron.core.helpers.filetools import view_file
                    application = 'Microsoft Office 2011/Microsoft Excel'
                    view_file(path, application=application)

                    # from pyface.message_dialog import information
                    # information(None, 'Template saved to {}'.format(path))


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


class GenerateIrradiationTableAction(TaskAction):
    name = 'Generate Irradiation Table'
    dname = 'Generate Irradiation Table'
    accelerator = 'Ctrl+0'

    # ddescription = 'Do not use!'

    def perform(self, event):
        # from pychron.entry.irradiation_table_writer import IrradiationTableWriter
        # a = IrradiationTableWriter()
        # a.make()

        from pychron.entry.irradiation_xls_writer import IrradiationXLSTableWriter
        dvc = self.task.window.application.get_service('pychron.dvc.dvc.DVC')
        if dvc is not None:
            if dvc.db.connect():
                names = dvc.get_irradiation_names()

                a = IrradiationXLSTableWriter(dvc=dvc)
                a.make(names)
        else:
            from pyface.message_dialog import warning
            warning(None, 'DVC Plugin is required. Please enable')


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


class GetIGSNAction(TaskAction):
    name = 'Get IGSNs'
    dname = 'Get IGSNs'
    method = 'get_igsns'


class GenerateStatusReportAction(TaskAction):
    name = 'Status Report...'
    dname = 'Status Report...'
    method = 'generate_status_report'
# ============= EOF =============================================
