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
import os

from pyface.tasks.action.schema import SToolBar
from traits.api import Instance, on_trait_change, Button
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter, Tabbed

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.entry.graphic_generator import GraphicModel, GraphicGeneratorController
from pychron.experiment.importer.import_manager import ImportManager
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.entry.project_entry import ProjectEntry
from pychron.entry.sample_entry import SampleEntry
from pychron.entry.labnumber_entry import LabnumberEntry
from pychron.entry.tasks.actions import SavePDFAction, GenerateLabnumbersAction, ImportIrradiationLevelAction
from pychron.entry.tasks.importer_panes import ImporterPane
from pychron.entry.tasks.labnumber_entry_panes import LabnumbersPane, \
    IrradiationPane, IrradiationEditorPane, IrradiationCanvasPane
from pychron.processing.tasks.actions.edit_actions import DatabaseSaveAction
from pychron.envisage.tasks.base_task import BaseManagerTask


class LabnumberEntryTask(BaseManagerTask, BrowserMixin):
    name = 'Labnumber'
    importer = Instance(ImportManager)

    add_sample_button = Button
    add_material_button = Button
    add_project_button = Button

    edit_project_button = Button
    edit_sample_button = Button

    tool_bars = [SToolBar(SavePDFAction(),
                          DatabaseSaveAction(),
                          image_size=(16, 16)),
                 SToolBar(GenerateLabnumbersAction(),
                          ImportIrradiationLevelAction(),
                          image_size=(16, 16))]

    def _prompt_for_save(self):
        if self.manager.dirty:
            message = 'You have unsaved changes. Save changes to Database?'
            ret = self._handle_prompt_for_save(message)
            if ret == 'save':
                return self.manager.save()
            return ret
        return True

    def activated(self):
        self.load_projects()

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

    def generate_labnumbers(self):
        self.manager.generate_labnumbers()

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

    def _manager_default(self):
        return LabnumberEntry(application=self.application)

    def _importer_default(self):
        return ImportManager(db=self.manager.db,
                             connect=False)

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                PaneItem('pychron.labnumber.irradiation'),
                Tabbed(
                    PaneItem('pychron.labnumber.extractor'),
                    PaneItem('pychron.labnumber.editor')
                ),
                orientation='vertical'
            ),
            right=PaneItem('pychron.entry.irradiation_canvas')
        )

    def create_central_pane(self):
        return LabnumbersPane(model=self.manager)

    def create_dock_panes(self):
        iep = IrradiationEditorPane(model=self)
        self.sample_tabular_adapter = iep.sample_tabular_adapter

        return [
            IrradiationPane(model=self.manager),
            ImporterPane(model=self.importer),
            iep,
            IrradiationCanvasPane(model=self.manager)
        ]

    @on_trait_change('extractor:update_irradiations_needed')
    def _update_irradiations(self):
        self.manager.updated = True

    def _add_project_button_fired(self):
        pr = ProjectEntry(db=self.manager.db)
        pr.add_project()

    def _add_sample_button_fired(self):
        sam = SampleEntry(db=self.manager.db)
        sam.add_sample(self.selected_projects)

    def _add_material_button_fired(self):
        self.manager.add_material()

    def _edit_project_button_fired(self):
        pr = ProjectEntry(db=self.manager.db)
        pr.edit_project(self.selected_projects)

    def _edit_sample_button_fired(self):
        se = SampleEntry(db=self.manager.db)
        sam = self.selected_samples

        se.edit_sample(sam.name,
                       self.selected_projects,
                       sam.material)

    #===========================================================================
    # GenericActon Handlers
    #===========================================================================
    def save_as(self):
        self.save()

    def save(self):
        self.warning_dialog('Please use "Data -> Database Save" to save changes to the database')

    def save_to_db(self):
        self.manager.save()

    def _selected_sample_changed(self, new):
        if new:
            self.manager.set_selected_sample(new)


#============= EOF =============================================
