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
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter, Tabbed
from traits.api import on_trait_change, Button, Float, Str, Int, Bool, Event, HasTraits
from traitsui.api import View, Item, VGroup, UItem, HGroup

from pychron.entry.graphic_generator import GraphicModel, GraphicGeneratorController
from pychron.entry.labnumber_entry import LabnumberEntry
from pychron.entry.tasks.actions import SavePDFAction, DatabaseSaveAction, PreviewGenerateIdentifiersAction, \
    GenerateIdentifiersAction, ClearSelectionAction, RecoverAction
from pychron.entry.tasks.labnumber.panes import LabnumbersPane, \
    IrradiationPane, IrradiationEditorPane, IrradiationCanvasPane, LevelInfoPane, ChronologyPane
from pychron.envisage.browser.base_browser_model import BaseBrowserModel
from pychron.envisage.browser.record_views import SampleRecordView
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.globals import globalv

ATTRS = (('sample', ''),
         ('material', ''),
         ('project', ''),
         ('weight', 0),
         ('j', 0,),
         ('j_err', 0))


class ClearSelectionView(HasTraits):
    sample = Bool(True)
    material = Bool(True)
    weight = Bool(True)
    project = Bool(True)
    j = Bool(True)
    j_err = Bool(True)

    select_all = Button('Select All')
    clear_all = Button('Clear All')

    def _select_all_fired(self):
        self._apply_all(True)

    def _clear_all_fired(self):
        self._apply_all(False)

    def _apply_all(self, v):
        for a, _ in ATTRS:
            setattr(self, a, v)

    def attributes(self):
        return [(a, v) for a, v in ATTRS if getattr(self, a)]

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('select_all'),
                               UItem('clear_all')),
                        VGroup(Item('sample'),
                        Item('material'),
                        Item('project'),
                        Item('weight'),
                        Item('j', label='J'),
                        Item('j_err', label='J Err.'))),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 title='Clear Selection')
        return v


class LabnumberEntryTask(BaseManagerTask, BaseBrowserModel):
    name = 'Labnumber'
    id = 'pychron.entry.irradiation.task'

    clear_sample_button = Button
    refresh_needed = Event
    dclicked = Event

    principal_investigator = Str
    tool_bars = [SToolBar(SavePDFAction(),
                          DatabaseSaveAction(),
                          image_size=(16, 16)),
                 SToolBar(GenerateIdentifiersAction(),
                          PreviewGenerateIdentifiersAction(),
                          image_size=(16, 16)),
                 SToolBar(ClearSelectionAction()),
                 SToolBar(RecoverAction())]

    invert_flag = Bool
    selection_freq = Int

    estimate_j_button = Button
    j = Float
    j_err = Float
    note = Str
    weight = Float

    include_recent = False
    _suppress_load_labnumbers = True

    def __init__(self, *args, **kw):
        super(LabnumberEntryTask, self).__init__(*args, **kw)
        self.db.create_session()

    def prepare_destroy(self):
        self.db.close_session()

    def activated(self):
        if self.manager.verify_database_connection(inform=True):
            if self.db.connected:
                self.manager.activated()
                self.load_principal_investigators()
                self.load_projects(include_recent=False)

    def generate_status_report(self):
        self.manager.generate_status_report()

    def recover(self):
        self.manager.recover()

    def clear_selection(self):
        cs = ClearSelectionView()
        info = cs.edit_traits()
        if info.result:
            for s in self.manager.selected:
                for attr, value in cs.attributes():
                    setattr(s, attr, value)

            self.manager.refresh_table = True

    def get_igsns(self):
        self.info('Get IGSNs')

        igsn_repo = self.application.get_service('pychron.repo.igsn.IGSNRepository')
        if not igsn_repo.url:
            self.warning_dialog('No IGSN URL set in preferences. '
                                'The url is required before proceeding. ')
            return

        self.manager.get_igsns(igsn_repo)

    def transfer_j(self):
        self.info('Transferring J Data')
        self.manager.transfer_j()

    def import_irradiation(self):
        self.manager.import_irradiation()

    def generate_tray(self):
        # p='/Users/ross/Sandbox/entry_tray'
        p = self.open_file_dialog()
        if p is not None:
            gm = GraphicModel()

            # op='/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/newtrays/26_no_spokes.txt'

            gm.srcpath = p
            # gm.xmlpath=p
            # p = make_xml(p,
            # default_radius=radius,
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
        if globalv.irradiation_pdf_debug:
            p = '/Users/ross/Sandbox/irradiation.pdf'
        else:
            p = self.save_file_dialog()

        if p:
            self.debug('saving pdf to {}'.format(p))
            if self.manager.save_pdf(p):
                self.view_pdf(p)

    def make_irradiation_book_pdf(self):
        if globalv.entry_labbook_debug:
            p = '/Users/ross/Sandbox/irradiation.pdf'
        else:
            p = self.save_file_dialog()

        if p:
            self.manager.make_labbook(p)
            self.view_pdf(p)

    def generate_identifiers(self):
        self.manager.generate_identifiers()

    def preview_generate_identifiers(self):
        self.manager.preview_generate_identifiers()

    def import_irradiation_load_xls(self):
        if globalv.entry_irradiation_import_from_file_debug:
            path = self.open_file_dialog()
        else:
            path = '/Users/ross/Sandbox/template.xls'

        if path:
            self.manager.import_irradiation_load_xls(path)

    # def make_irradiation_load_template(self):
    #     path = self.save_file_dialog()
    #     if path:
    #         #        p = '/Users/ross/Sandbox/irrad_load_template.xls'
    #         path = add_extension(path, '.xls')
    #         self.manager.make_irradiation_load_template(path)
    #
    #         self.information_dialog('Template saved to {}'.format(path))
    #         # self.view_xls(path)

    def import_sample_from_file(self):
        # path = self.open_file_dialog(default_directory=paths.root_dir,
        # wildcard='*.xls')
        path = '/Users/ross/Desktop/sample_import.xls'
        if path:
            from pychron.entry.loaders.xls_sample_loader import XLSSampleLoader

            sample_loader = XLSSampleLoader()
            sample_loader.do_loading(self.manager, self.manager.db, path)

            spnames = []
            if self.selected_projects:
                spnames = [ni.name for ni in self.selected_projects]

            self.load_projects(include_recent=False)

            if spnames:
                sel = [si for si in self.projects if si.name in spnames]
                self.selected_projects = sel

            self._load_associated_samples()

    def import_sample_metadata(self):
        self.warning('Import sample metadata Deprecated')

    #     path = '/Users/ross/Programming/git/dissertation/data/minnabluff/lithologies.xls'
    #     path = '/Users/ross/Programming/git/dissertation/data/minnabluff/tables/TAS.xls'
    #     path = '/Users/ross/Programming/git/dissertation/data/minnabluff/tables/environ.xls'
    #     if not os.path.isfile(path):
    #         path = self.open_file_dialog()
    #
    #     if path:
    #         self.manager.import_sample_metadata(path)

    def export_irradiation(self):
        from pychron.entry.export.export_selection_view import ExportSelectionView

        pref = self.application.preferences
        connection = {attr: pref.get('pychron.massspec.database.{}'.format(attr))
                      for attr in ('name', 'host', 'password', 'username')}
        es = ExportSelectionView(irradiations=self.manager.irradiations,
                                 default_massspec_connection=connection)
        info = es.edit_traits(kind='livemodal')
        if info.result:
            if not es.selected:
                self.warning_dialog('Please select Irradiation(s) to export')
            else:
                from pychron.entry.export.export_util import do_export
                do_export(self.manager.dvc, es.export_type, es.destination_dict, es.selected)

    def _manager_default(self):
        dvc = self.application.get_service('pychron.dvc.dvc.DVC')
        dvc.connect()
        return LabnumberEntry(application=self.application, dvc=dvc)

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
        self.labnumber_tabular_adapter = iep.sample_tabular_adapter
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
        self.save_to_db()

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
            ni = new[0]
            # self.manager.set_selected_attr(new.name, 'sample')
            self.manager.set_selected_attrs((ni.name, ni.material, ni.project, ni.principal_investigator),
                                            ('sample', 'material', 'project', 'principal_investigator'))

    def _load_associated_samples(self, names=None):
        if names is None:
            if self.selected_projects:
                names = [ni.name for ni in self.selected_projects]

        # load associated samples
        sams = self.db.get_samples(project=names)
        sams = [SampleRecordView(si) for si in sams]

        self.samples = sams
        self.osamples = sams

    # handlers
    def _dclicked_fired(self):
        self.selected_samples = []

    def _clear_sample_button_fired(self):
        self.selected_samples = []

    @on_trait_change('extractor:update_irradiations_needed')
    def _update_irradiations(self):
        self.manager.updated = True

    # def _generate_identifiers_button_fired(self):
    #     self.generate_identifiers()
    #
    # def _preview_generate_identifiers_button_fired(self):
    #     self.preview_generate_identifiers()

    # # def _add_project_button_fired(self):
    # #     dvc = self.manager.dvc
    # #     pr = ProjectEntry(dvc=self.manager.dvc)
    # #     pr.available = dvc.get_project_names()
    # #     if pr.do():
    # #         self.load_projects(include_recent=False)
    # #
    # # def _add_sample_button_fired(self):
    # #     project = ''
    # #     if self.selected_projects:
    # #         project = self.selected_projects[0].name
    # #
    # #     mats = self.db.get_material_names()
    # #     sam = SampleEntry(dvc=self.manager.dvc,
    # #                       project=project,
    # #                       projects=[p.name for p in self.projects],
    # #                       materials=mats)
    # #     if sam.do():
    # #         self._load_associated_samples()
    #
    # def _add_material_button_fired(self):
    #     dvc = self.manager.dvc
    #     mat = MaterialEntry(dvc=dvc)
    #     mat.available = dvc.get_material_names()
    #     mat.do()
    #     # self._load_materials()

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
    #
    def _principal_investigator_changed(self, new):
        if new:
            self._load_projects_for_principal_investigators(pis=[new])

    def _selected_projects_changed(self, old, new):
        if new:
            names = [ni.name for ni in new]
            self.debug('selected projects={}'.format(names))

            self._load_associated_samples(names)

    def _prompt_for_save(self):
        self.manager.push_changes()

        if self.manager.dirty:
            message = 'You have unsaved changes. Save changes to Database?'
            ret = self._handle_prompt_for_save(message)
            if ret == 'save':
                return self.manager.save()
            return ret
        return True

# ============= EOF =============================================
