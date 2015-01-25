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

from pyface.tasks.action.schema import SToolBar
from traits.api import on_trait_change, Button, Float, Str, Int, Bool
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter, Tabbed

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================

from pychron.entry.graphic_generator import GraphicModel, GraphicGeneratorController
from pychron.entry.tasks.importer_view import ImporterView
from pychron.envisage.browser.record_views import SampleRecordView
from pychron.entry.tasks.importer import ImporterModel
from pychron.envisage.browser.base_browser_model import BaseBrowserModel
from pychron.entry.entry_views.project_entry import ProjectEntry
from pychron.entry.entry_views.sample_entry import SampleEntry
from pychron.entry.labnumber_entry import LabnumberEntry
from pychron.entry.tasks.actions import SavePDFAction
# from pychron.entry.tasks.importer_panes import ImporterPane
from pychron.entry.tasks.labnumber_entry_panes import LabnumbersPane, \
    IrradiationPane, IrradiationEditorPane, IrradiationCanvasPane, LevelInfoPane, ChronologyPane
from pychron.processing.tasks.actions.edit_actions import DatabaseSaveAction
from pychron.envisage.tasks.base_task import BaseManagerTask


class LabnumberEntryTask(BaseManagerTask, BaseBrowserModel):
    name = 'Labnumber'
    # importer = Instance(ImportManager)

    add_sample_button = Button
    add_material_button = Button
    add_project_button = Button

    edit_project_button = Button
    edit_sample_button = Button

    generate_identifiers_button = Button
    preview_generate_identifiers_button = Button

    tool_bars = [SToolBar(SavePDFAction(),
                          DatabaseSaveAction(),
                          image_size=(16, 16))]
                 # SToolBar(GenerateLabnumbersAction(),
                 #          PreviewGenerateLabnumbersAction(),
                 #          ImportIrradiationLevelAction(),
                 #          image_size=(16, 16))]

    invert_flag = Bool
    selection_freq = Int

    estimate_j_button = Button
    j = Float
    j_err = Float
    note = Str
    weight = Float

    def activated(self):
        self.load_projects(include_recent=False)

    def transfer_j(self):
        self.info('Transferring J Data')
        self.manager.transfer_j()

    def import_irradiation(self):
        mod = ImporterModel(db=self.manager.db)
        ev = ImporterView(model=mod)
        ev.edit_traits()

    def generate_tray(self):
        # p='/Users/ross/Sandbox/entry_tray'
        p = self.open_file_dialog()
        if p is not None:
            gm = GraphicModel()

            # op='/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/newtrays/26_no_spokes.txt'

            gm.srcpath = p
            # gm.xmlpath=p
            # p = make_xml(p,
            #              default_radius=radius,
            #              default_bounds=bounds,
            #              convert_mm=convert_mm,
            #              use_label=use_label,
            #              make=make,
            #              rotate=rotate)
            #
            # #    p = '/Users/ross/Sandbox/graphic_gen_from_csv.xml'
            # gm.load(p)
            gcc = GraphicGeneratorController(model=gm)
            info = gcc.edit_traits(kind='livemodal')
            if info.result:
                if self.confirmation_dialog(
                        'Do you want to save this tray to the database. Saving tray as "{}"'.format(gm.name)):
                    self.manager.save_tray_to_db(gm.srcpath, gm.name)

    def save_pdf(self):
        p = '/Users/ross/Sandbox/irradiation.pdf'
        #p=self.save_file_dialog()

        self.debug('saving pdf to {}'.format(p))
        #self.manager.make_labbook(p)
        self.manager.save_pdf(p)
        self.view_pdf(p)

    def save_labbook_pdf(self):
        p = '/Users/ross/Sandbox/irradiation.pdf'
        #p=self.save_file_dialog()

        self.manager.make_labbook(p)
        self.view_pdf(p)

    def generate_identifiers(self):
        self.manager.generate_identifiers()

    def preview_generate_identifiers(self):
        self.manager.preview_generate_identifiers()

    def import_irradiation_load_xls(self):
        path = self.open_file_dialog()
        if path:
            #p = '/Users/ross/Sandbox/irrad_load_template.xls'
            self.manager.import_irradiation_load_xls(path)

    def make_irradiation_load_template(self):
        path = self.open_file_dialog()
        if path:
            #        p = '/Users/ross/Sandbox/irrad_load_template.xls'
            self.manager.make_irradiation_load_template(path)
            #self.information_dialog('Template saved to {}'.format(p))
            self.view_xls(path)

    def import_sample_metadata(self):
        path = '/Users/ross/Programming/git/dissertation/data/minnabluff/lithologies.xls'
        path = '/Users/ross/Programming/git/dissertation/data/minnabluff/tables/TAS.xls'
        path = '/Users/ross/Programming/git/dissertation/data/minnabluff/tables/environ.xls'
        if not os.path.isfile(path):
            path = self.open_file_dialog()

        if path:
            self.manager.import_sample_metadata(path)

    def export_irradiation(self):
        from pychron.entry.export.export_selection_view import ExportSelectionView

        pref = self.application.preferences
        connection = {attr: pref.get('pychron.massspec.database.{}'.format(attr))
                      for attr in ('name', 'host', 'password', 'username')}
        es = ExportSelectionView(irradiations=self.manager.irradiations,
                                 default_massspec_connection=connection)
        info = es.edit_traits(kind='livemodal')
        if info.result:
            from pychron.entry.export.export_util import do_export
            do_export(self.manager, es.export_type, es.destination_dict, es.irradiations)

    def _manager_default(self):
        return LabnumberEntry(application=self.application)

    # def _importer_default(self):
    #     return ImportManager(db=self.manager.db,
    #                          connect=False)

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                PaneItem('pychron.labnumber.irradiation'),
                Tabbed(
                    # PaneItem('pychron.labnumber.extractor'),
                    PaneItem('pychron.labnumber.editor')),
                orientation='vertical'),
            right=Splitter(
                PaneItem('pychron.entry.level'),
                PaneItem('pychron.entry.chronology'),
                PaneItem('pychron.entry.irradiation_canvas'),
                           orientation='vertical'))

    def create_central_pane(self):
        return LabnumbersPane(model=self.manager)

    def create_dock_panes(self):
        iep = IrradiationEditorPane(model=self)
        self.labnumber_tabular_adapter = iep.labnumber_tabular_adapter
        return [
            IrradiationPane(model=self.manager),
            ChronologyPane(model=self.manager),
            LevelInfoPane(model=self.manager),
            # ImporterPane(model=self.importer),
            iep,
            IrradiationCanvasPane(model=self.manager)]
    # ===========================================================================
    # GenericActon Handlers
    # ===========================================================================
    def save_as(self):
        self.save()

    def save(self):
        self.warning_dialog('Please use "Data -> Database Save" to save changes to the database')

    def save_to_db(self):
        self.manager.save()

    def _estimate_j_button_fired(self):
        self.manager.estimate_j()

    @on_trait_change('selection_freq, invert_flag')
    def _handle_selection(self):
        if self.selection_freq:
            self.manager.select_positions(self.selection_freq, self.invert_flag)

    @on_trait_change('j,j_err, note, weight')
    def _handle_j(self, obj, name, old, new):
        if new:
            self.manager.set_selected_attr(new, name)

    def _selected_samples_changed(self, new):
        if new:
            self.manager.set_selected_attr(new.name, 'sample')

    def _load_associated_samples(self, names):
        db = self.db
        with db.session_ctx():
            # load associated samples
            sams = db.get_samples(project=names)
            sams = [SampleRecordView(si) for si in sams]

        self.samples = sams
        self.osamples = sams

    # handlers
    @on_trait_change('extractor:update_irradiations_needed')
    def _update_irradiations(self):
        self.manager.updated = True

    def _generate_identifiers_button_fired(self):
        self.generate_identifiers()

    def _preview_generate_identifiers_button_fired(self):
        self.preview_generate_identifiers()

    def _add_project_button_fired(self):
        pr = ProjectEntry(db=self.manager.db)
        if pr.do():
            self.load_projects(include_recent=False)

    def _add_sample_button_fired(self):
        project = ''
        if self.selected_projects:
            project = self.selected_projects[0].name

        mats = self.db.get_material_names()
        sam = SampleEntry(db=self.manager.db,
                          project=project,
                          projects = [p.name for p in self.projects],
                          materials = mats)
        if sam.do():
            self._load_associated_samples([si.name for si in self.selected_projects])

    # def _add_material_button_fired(self):
    #     mat = MaterialEntry(db=self.manager.db)
    #     if mat.do():
    #         self._load_materials()

    # def _edit_project_button_fired(self):
    #     pr = ProjectEntry(db=self.manager.db)
    #     pr.edit_project(self.selected_projects)
    #
    # def _edit_sample_button_fired(self):
    #     se = SampleEntry(db=self.manager.db)
    #     sam = self.selected_samples
    #
    #     se.edit_sample(sam.name,
    #                    self.selected_projects,
    #                    sam.material)

    def _selected_projects_changed(self, old, new):
        if new and self.project_enabled:

            names = [ni.name for ni in new]
            self.debug('selected projects={}'.format(names))

            self._load_associated_samples(names)
            self._selected_projects_change_hook(names)
            # self.dump_browser_selection()

    def _prompt_for_save(self):
        if self.manager.dirty:
            message = 'You have unsaved changes. Save changes to Database?'
            ret = self._handle_prompt_for_save(message)
            if ret == 'save':
                return self.manager.save()
            return ret
        return True

# ============= EOF =============================================
