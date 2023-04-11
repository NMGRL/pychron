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
from traitsui.api import Item, VGroup, UItem, HGroup

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import PacketStr
from pychron.entry.labnumber_entry import LabnumberEntry
from pychron.entry.tasks.actions import (
    SavePDFAction,
    DatabaseSaveAction,
    PreviewGenerateIdentifiersAction,
    GenerateIdentifiersAction,
    ClearSelectionAction,
    RecoverAction,
    SyncMetaDataAction,
    ManualEditIdentifierAction,
    EditMaterialAction,
)
from pychron.entry.tasks.labnumber.panes import (
    LabnumbersPane,
    IrradiationPane,
    IrradiationEditorPane,
    IrradiationCanvasPane,
    LevelInfoPane,
    ChronologyPane,
    FluxHistoryPane,
    IrradiationMetadataEditorPane,
)
from pychron.envisage.browser.base_browser_model import BaseBrowserModel
from pychron.envisage.browser.record_views import SampleRecordView
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.globals import globalv
from pychron.pychron_constants import DVC_PROTOCOL
from pychron.regex import PACKETREGEX

ATTRS = (
    ("sample", ""),
    ("material", ""),
    ("project", ""),
    ("principal_investigator", ""),
    ("weight", 0),
    (
        "j",
        0,
    ),
    ("j_err", 0),
)

MANUAL_EDIT_VIEW = okcancel_view(
    Item("edit_identifier_entry", label="Identifier"), title="Manual Edit Identifier"
)


class ClearSelectionView(HasTraits):
    sample = Bool(True)
    material = Bool(True)
    weight = Bool(True)
    project = Bool(True)
    principal_investigator = Bool(True)
    j = Bool(True)
    j_err = Bool(True)

    select_all = Button("Select All")
    clear_all = Button("Clear All")

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
        v = okcancel_view(
            VGroup(
                HGroup(UItem("select_all"), UItem("clear_all")),
                VGroup(
                    Item("sample"),
                    Item("material"),
                    Item("project"),
                    Item("principal_investigator"),
                    Item("weight"),
                    Item("j", label="J"),
                    Item("j_err", label="J Err."),
                ),
            ),
            title="Clear Selection",
        )
        return v


class LabnumberEntryTask(BaseManagerTask, BaseBrowserModel):
    name = "Package"
    id = "pychron.entry.irradiation.task"

    edit_identifier_entry = Str
    clear_sample_button = Button
    refresh_needed = Event
    dclicked = Event

    principal_investigator = Str
    tool_bars = [
        SToolBar(SavePDFAction(), DatabaseSaveAction(), image_size=(16, 16)),
        SToolBar(
            GenerateIdentifiersAction(),
            PreviewGenerateIdentifiersAction(),
            image_size=(16, 16),
        ),
        SToolBar(ClearSelectionAction()),
        SToolBar(
            RecoverAction(),
            SyncMetaDataAction(),
            ManualEditIdentifierAction(),
            EditMaterialAction(),
        ),
    ]

    invert_flag = Bool
    selection_freq = Int

    estimate_j_button = Button
    j = Float
    j_err = Float
    note = Str
    weight = Float
    sample_search_str = Str
    packet = PacketStr

    set_packet_event = Event
    use_increment_packet = Bool
    include_recent = False
    _suppress_load_labnumbers = True

    # def __init__(self, *args, **kw):
    #     super(LabnumberEntryTask, self).__init__(*args, **kw)
    #     self.db.create_session()

    def prepare_destroy(self):
        self.db.close_session()

    def _opened_hook(self):
        self.db.create_session(force=True)

    def _closed_hook(self):
        self.db.close_session()

    def activated(self):
        self.debug("activated labnumber")
        if self.manager.verify_database_connection(inform=True):
            if self.db.connected:
                self.manager.activated()
                self.load_principal_investigators()
                self.load_projects(include_recent=False)

    def find_associated_identifiers(self):
        ns = [ni.name for ni in self.selected_samples]
        self.info("find associated identifiers {}".format(",".join(ns)))

        self.manager.find_associated_identifiers(self.selected_samples)

    def sync_metadata(self):
        self.info("sync metadata")
        self.manager.sync_metadata()

    def generate_status_report(self):
        self.info("generate status report")
        self.manager.generate_status_report()

    def recover(self):
        self.info("recover")
        self.manager.recover()

    def clear_selection(self):
        self.info("clear selection")
        cs = ClearSelectionView()
        info = cs.edit_traits()
        if info.result:
            for s in self.manager.selected:
                for attr, value in cs.attributes():
                    setattr(s, attr, value)

            self.manager.refresh_table = True

    # def get_igsns(self):
    #     self.info('Get IGSNs')
    #
    #     # if not igsn_repo.url:
    #     #     self.warning_dialog('No IGSN URL set in preferences. '
    #     #                         'The url is required before proceeding. ')
    #     #     return
    #
    #     self.manager.get_igsns()

    def transfer_j(self):
        self.info("Transferring J Data")
        self.manager.transfer_j()

    def manual_edit_material(self):
        if not self.manager.selected:
            self.information_dialog(
                "Please select an existing irradiation position to edit"
            )
            return

        self.manager.edit_material()
        # if self.manager.edit_material():
        #     self.refresh_needed = True

    def manual_edit_identifier(self):
        if not self.manager.selected:
            self.information_dialog(
                "Please select an existing irradiation position to edit"
            )
            return

        if not self.confirmation_dialog(
            "Please be very careful editing identifiers. Serious unintended consequences "
            "may result from changing an identifier. This function should only be used by "
            "users with a deep understanding of how pychron handles irradiations. \n\nAre "
            "you sure you want to continue?"
        ):
            return

        self.info("Manual edit identifier")
        self.edit_identifier_entry = self.manager.selected[0].identifier
        info = self.edit_traits(view=MANUAL_EDIT_VIEW, kind="livemodal")
        if info and self.edit_identifier_entry:
            self.manager.selected[0].identifier = self.edit_identifier_entry

    # def import_irradiation(self):
    #     self.info('Import irradiation')
    #     self.manager.import_irradiation()

    # def import_analyses(self):
    #     self.info('Import analyses')
    #     self.manager.import_analyses()

    # def generate_tray(self):
    #     # p='/Users/ross/Sandbox/entry_tray'
    #     p = self.open_file_dialog()
    #     if p is not None:
    #         gm = GraphicModel()
    #
    #         # op='/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/newtrays/26_no_spokes.txt'
    #
    #         gm.srcpath = p
    #         # gm.xmlpath=p
    #         # p = make_xml(p,
    #         # default_radius=radius,
    #         #              default_bounds=bounds,
    #         #              convert_mm=convert_mm,
    #         #              use_label=use_label,
    #         #              make=make,
    #         #              rotate=rotate)
    #         #
    #         # #    p = '/Users/ross/Sandbox/graphic_gen_from_csv.xml'
    #         # gm.load(p)
    #         gcc = GraphicGeneratorController(model=gm)
    #         info = gcc.edit_traits(kind='livemodal')
    #         if info.result:
    #             if self.confirmation_dialog(
    #                     'Do you want to save this tray to the database. Saving tray as "{}"'.format(gm.name)):
    #                 self.manager.save_tray_to_db(gm.srcpath, gm.name)

    def save_pdf(self):
        if globalv.irradiation_pdf_debug:
            p = "/Users/ross/Sandbox/irradiation.pdf"
        else:
            p = self.save_file_dialog()

        if p:
            self.debug("saving pdf to {}".format(p))
            if self.manager.save_pdf(p):
                self.view_pdf(p)

    def make_irradiation_book_pdf(self):
        if globalv.entry_labbook_debug:
            p = "/Users/ross/Sandbox/irradiation.pdf"
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
            path = "/Users/ross/Sandbox/template.xls"

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

    # def import_sample_from_file(self):
    #     path = self.open_file_dialog(default_directory=paths.root_dir,
    #                                  wildcard_args=('Excel', ('*.xls', '*.xlsx')))
    #     # path = '/Users/ross/Desktop/sample_import.xls'
    #     if path:
    #         # from pychron.entry.loaders.xls_sample_loader import XLSSampleLoader
    #         #
    #         from pychron.entry.sample_loader import XLSSampleLoader
    #         sample_loader = XLSSampleLoader()
    #         sample_loader.load(path)
    #         sample_loader.do_import()
    #
    #         # spnames = []
    #         # if self.selected_projects:
    #         #     spnames = [ni.name for ni in self.selected_projects]
    #         #
    #         # self.load_projects(include_recent=False)
    #         #
    #         # if spnames:
    #         #     sel = [si for si in self.projects if si.name in spnames]
    #         #     self.selected_projects = sel
    #         #
    #         # self._load_associated_samples()

    # def import_sample_metadata(self):
    #     self.warning('Import sample metadata Deprecated')

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
        connection = {
            attr: pref.get("pychron.massspec.database.{}".format(attr))
            for attr in ("name", "host", "password", "username")
        }
        es = ExportSelectionView(
            irradiations=self.manager.irradiations,
            default_massspec_connection=connection,
        )
        info = es.edit_traits(kind="livemodal")
        if info.result:
            if not es.selected:
                self.warning_dialog("Please select Irradiation(s) to export")
            else:
                from pychron.entry.export.export_util import do_export

                do_export(
                    self.manager.dvc, es.export_type, es.destination_dict, es.selected
                )

    def _manager_default(self):
        dvc = self.application.get_service(DVC_PROTOCOL)
        dvc.connect()
        dvc.create_session()
        return LabnumberEntry(application=self.application, dvc=dvc)

    # def _importer_default(self):
    #     return ImportManager(db=self.manager.db,
    #                          connect=False)

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                PaneItem("pychron.labnumber.irradiation"),
                Tabbed(
                    # PaneItem('pychron.labnumber.extractor'),
                    PaneItem("pychron.labnumber.editor")
                ),
                orientation="vertical",
            ),
            right=Splitter(
                PaneItem("pychron.entry.level"),
                PaneItem("pychron.entry.chronology"),
                PaneItem("pychron.entry.irradiation_canvas"),
                PaneItem("pychron.entry.flux_history"),
                orientation="vertical",
            ),
        )

    def create_central_pane(self):
        return LabnumbersPane(model=self.manager)

    def create_dock_panes(self):
        return [
            IrradiationPane(model=self.manager),
            ChronologyPane(model=self.manager),
            LevelInfoPane(model=self.manager),
            FluxHistoryPane(model=self.manager),
            IrradiationEditorPane(model=self),
            IrradiationMetadataEditorPane(model=self),
            IrradiationCanvasPane(model=self.manager),
        ]

    # ===========================================================================
    # GenericActon Handlers
    # ===========================================================================
    def save_as(self):
        self.save()

    def save(self):
        self.save_to_db()

    def save_to_db(self):
        self.manager.save()

    # private
    def _increment_packet(self):
        m = PACKETREGEX.search(self.packet)
        if m:
            v = m.group("prefix")
            if not v:
                v = ""
            a = m.group("number")
            self.packet = "{}{:02n}".format(v, int(a) + 1)

    # handlers
    def _estimate_j_button_fired(self):
        self.manager.estimate_j()

    @on_trait_change("selection_freq, invert_flag")
    def _handle_selection(self):
        if self.selection_freq:
            self.manager.select_positions(self.selection_freq, self.invert_flag)

    @on_trait_change("j,j_err, note, weight")
    def _handle_j(self, obj, name, old, new):
        if new:
            self.manager.set_selected_attr(new, name)

    @on_trait_change("set_packet_event")
    def _handle_packet(self):
        if not self.manager.selected:
            self.warning_dialog(
                "Please select an Irradiation Position before trying to set the Packet"
            )
            return

        for s in self.manager.selected:
            s.packet = self.packet

        self.manager.refresh_table = True
        if self.use_increment_packet:
            self._increment_packet()

    def _sample_search_str_changed(self, new):
        if len(new) >= 3:
            sams = self.db.get_samples(name_like=new)
            self._set_sample_records(sams)

    def _selected_samples_changed(self, new):
        if new:
            ni = new[0]
            self.manager.set_selected_attrs(
                (
                    ni.name,
                    ni.material,
                    ni.grainsize,
                    ni.project,
                    ni.principal_investigator,
                ),
                (
                    "sample",
                    "material",
                    "grainsize",
                    "project",
                    "principal_investigator",
                ),
            )

    def _load_associated_samples(self, names=None):
        if names is None:
            if self.selected_projects:
                names = [ni.name for ni in self.selected_projects]

        # load associated samples
        sams = self.db.get_samples(projects=names)
        self._set_sample_records(sams)

    def _set_sample_records(self, sams):
        sams = [SampleRecordView(si) for si in sams]

        self.samples = sams
        self.osamples = sams

    def _dclicked_fired(self):
        self.selected_samples = []

    def _clear_sample_button_fired(self):
        self.selected_samples = []

    @on_trait_change("extractor:update_irradiations_needed")
    def _update_irradiations(self):
        self.manager.updated = True

    def _principal_investigator_changed(self, new):
        if new:
            self._load_projects_for_principal_investigators(pis=[new])

    def _selected_projects_changed(self, old, new):
        if new:
            names = [ni.name for ni in new]
            self.debug("selected projects={}".format(names))

            self._load_associated_samples(names)
        else:
            self.samples = []

    def _prompt_for_save(self):
        self.manager.push_changes()

        if self.manager.dirty:
            message = "You have unsaved changes. Save changes to Database?"
            ret = self._handle_prompt_for_save(message)
            if ret == "save":
                return self.manager.save()
            return ret
        return True


# ============= EOF =============================================
