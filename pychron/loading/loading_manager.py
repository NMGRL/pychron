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

import os
import time
from datetime import datetime

from chaco.data_range_1d import DataRange1D
from chaco.default_colormaps import color_map_name_dict, color_map_dict
from numpy import linspace
from traits.api import (
    HasTraits,
    cached_property,
    List,
    Str,
    Instance,
    Property,
    Int,
    Any,
    Bool,
    Button,
    Float,
    on_trait_change,
    Enum,
    RGBColor,
    Event,
)
from traitsui.api import Item, EnumEditor, UItem, ListStrEditor

from pychron.canvas.canvas2D.calibration_canvas import CalibrationCanvas
from pychron.canvas.canvas2D.loading_canvas import LoadingCanvas, group_position
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
from pychron.canvas.utils import load_holder_canvas
from pychron.core.helpers.filetools import view_file
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pdf.pdf_graphics_context import PdfPlotGraphicsContext
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.preference_binding import bind_preference
from pychron.dvc.dvc_irradiationable import DVCIrradiationable
from pychron.dvc.meta_object import MetaObjectException
from pychron.envisage.view_util import open_view
from pychron.hardware.jss57 import STP_MTRD
from pychron.loading.foot_pedal import FootPedal
from pychron.loading.loading_pdf_writer import LoadingPDFWriter
from pychron.paths import paths

# ============= enthought library imports =======================
from pychron.pychron_constants import NULL_STR
from pychron.regex import LOAD_REGEX


def make_bound(st):
    if len(st) > 1:
        s = "{}-{}".format(st[0], st[-1])
    else:
        s = "{}".format(st[0])
    return s


def make_position_str(pos):
    s = ""
    if pos:
        pos = [p.position for p in pos]
        ss = group_position(pos, make_bound)
        s = ",".join(ss)
    return s


class LoadSelection(HasTraits):
    loads = List
    selected = List

    def traits_view(self):
        v = okcancel_view(
            UItem(
                "loads",
                editor=ListStrEditor(
                    selected="selected", multi_select=True, editable=False
                ),
            ),
            width=300,
            title="Select Loads to Unarchive",
        )
        return v


class NamedPosition(HasTraits):
    name = Str


class LoadPosition(HasTraits):
    identifier = Str
    sample = Str
    project = Str
    position = Int
    weight = Float
    note = Str
    nxtals = Int
    material = Str
    packet = Str

    level = Str
    irradiation = Str
    irrad_position = Int

    irradiation_str = Property
    level_str = Property

    color = RGBColor

    def _get_level_str(self):
        return "{}{}".format(self.level, self.irrad_position)

    def _get_irradiation_str(self):
        return "{} {}".format(self.irradiation, self.level_str)


class GroupedPosition(LoadPosition):
    positions = List
    position_str = Property(depends_on="positions[]")

    color = Property
    sample = Property
    material = Property
    project = Property
    packet = Property

    def _get_level_str(self):
        return self.meta_position.level_str

    def _get_irradiation_str(self):
        return self.meta_position.irradiation_str

    def _get_project(self):
        return self.meta_position.project

    def _get_packet(self):
        return self.meta_position.packet

    def _get_sample(self):
        return self.meta_position.sample

    def _get_material(self):
        return self.meta_position.material

    def _get_color(self):
        return self.meta_position.color

    def _get_position_str(self):
        return make_position_str(self.positions)


class Load(HasTraits):
    name = Str
    create_date = Str


class LoadingManager(DVCIrradiationable):
    _pdf_writer = Instance(LoadingPDFWriter, ())
    dirty = Bool(False)
    username = Str

    available_user_names = List

    identifier = Str
    identifiers = List

    weight = Float
    note = Str
    nxtals = Int
    save_directory = Str

    """
        when a hole is selected npositions defines the number of 
        total positions to apply the current information i.e identifier
    """
    npositions = Int(1)
    auto_increment = Bool(False)

    positions = List
    grouped_positions = Property(depends_on="positions")

    # table signal/events
    scroll_to_row = Int
    selected_positions = List

    loads = List
    load_instance = Any
    selected_instances = List

    canvas = Any
    mv_canvas = Any

    add_button = Button
    delete_button = Button
    archive_button = Button
    unarchive_button = Button

    new_load_name = Str
    tray = Str
    trays = List

    sample_info = Property(depends_on="identifier")
    sample = Str
    project = Str
    irradiation_hole = Int
    packet = Str
    material = Str

    retain_weight = Bool(False)
    retain_note = Bool(False)
    retain_nxtals = Bool(False)

    show_samples = Bool(False)
    show_identifiers = Bool(False)
    show_weights = Bool(False)
    show_hole_numbers = Bool(False)
    show_nxtals = Bool(False)

    cmap_name = Enum(sorted(list(color_map_name_dict.keys())))
    use_cmap = Bool(True)
    interaction_mode = Enum("Entry", "Info", "Edit", "Goto", "GotoEntry", "FootPedal")
    suppress_update = False

    use_measured = Bool(False)

    _suppress_edit = Bool(False)

    stage_manager = Instance(
        "pychron.lasers.stage_managers.video_stage_manager.VideoStageManager"
    )

    use_stage = Bool(False)
    foot_pedal = Instance(FootPedal, ())
    interaction_mode_enabled = Bool(False)
    focus_motor = Instance(STP_MTRD)
    focus_position_entry = Float(enter_set=True, auto_set=False)
    focus_position_readback = Float
    focus_stepsperdata = Int(964)
    focus_scalar = Float(15.5)
    zoom_level = Enum(
        "1",
        (
            "0.8",
            "1",
            "2",
            "3",
            "4",
            "6",
            "8",
        ),
    )

    loading_level_button = Button("Loading Level")
    checking_level_button = Button("Checking Level")
    up_button = Button("Up")
    down_button = Button("Down")
    home_button = Button("Home")
    scan_tray_button = Button("Scan Tray")
    refresh_table = Event
    mode = "normal"

    tray_checker = Instance("pychron.loading.tray_checker.TrayChecker")

    use_image_shift = True

    def __init__(self, *args, **kw):
        super(LoadingManager, self).__init__(*args, **kw)
        self.dvc.create_session()

        pref_id = "pychron.loading"
        bind_preference(self, "use_stage", "{}.use_stage".format(pref_id))

        if self.use_stage:
            from pychron.lasers.stage_managers.video_stage_manager import (
                VideoStageManager,
            )
            from pychron.loading.tray_checker import TrayChecker

            pxpermm = 55
            self.stage_manager = VideoStageManager(
                parent=self,
                name="loader",
                pxpermm=pxpermm,
                # root=os.path.join(paths.meta_root, 'load_holders'),
                stage_controller_klass="ZaberMotion",
            )
            self.stage_manager.autocenter_manager.use_autocenter = True
            self.stage_manager.autocenter_manager.pxpermm = pxpermm
            self.stage_manager.load()
            self.stage_manager.initialize_video()
            self.stage_manager.canvas.padding = 10
            self.stage_manager.canvas.show_axes = False
            self.stage_manager.stage_controller.bootstrap()
            self.stage_manager.stage_controller.update_axes()
            self.tray_checker = TrayChecker(self)
            self.focus_motor = STP_MTRD(name="focusmotor")
            self.focus_motor.bootstrap()
            self.focus_motor.stepsperdata = self.focus_stepsperdata
            self.focus_motor.nominal_home_position = 12
            self.stage_manager.set_zoom_manually(pxpermm)
            # self.stage_manager.canvas.set_mapper_limits('x', (-10,10))
            # self.stage_manager.canvas.set_mapper_limits('y', (-10,10))
            self.stage_manager.bind_preferences("pychron.loading")

            self._update_focus_position()
            self.focus_position_entry = round(self.focus_position_readback, 2)

    def scan_tray(self):
        classify_now = False
        if self.confirmation_dialog("Would you like to classify each image"):
            classify_now = True
        self.tray_checker.scan(classify_now)

    def check_tray(self):
        self.tray_checker.check()

    def map_tray(self):
        self.tray_checker.map()

    def set_loaded_runs(self, runs):
        pass

    def load(self):
        if self.canvas:
            self.canvas.editable = True
            self.clear()
        return True

    def clear(self):
        if self.canvas:
            self.canvas.clear_all()

    def get_load_position_by_position(self, pos):
        for p in self.positions:
            if p.position == pos:
                return p

    def get_selection(self):
        from pychron.loading.load_view_selection import (
            LoadViewSelectionModel,
            LoadViewSelectionController,
        )

        self.setup()
        if self.loads:
            self.use_measured = True
            self.load_instance = self.loads[-1]
            oeditable = self.canvas.editable
            self.canvas.editable = False
            lvsm = LoadViewSelectionModel(manager=self)
            lvc = LoadViewSelectionController(model=lvsm)
            info = open_view(lvc)
            self.canvas.editable = oeditable
            self.use_measured = False
            if info.result:
                return lvsm.selected_positions
        else:
            self.warning_dialog("No Loads available")

    def get_positions_for_load(self, name):
        self.debug('get positions for load "{}"'.format(name))
        with self.dvc.session_ctx():
            loadtable = self.dvc.get_loadtable(name)
            if loadtable:
                return [
                    (p.identifier, str(p.position))
                    for p in loadtable.loaded_positions
                    if p.identifier and p.position
                ]
            else:
                self.warning_dialog('No Positions specified in load "{}"'.format(name))

    def set_load_by_name(self, name):
        self.load_instance = next((l for l in self.loads if l.name == name), None)
        self.load_load_by_name()

    def load_load_by_name(self):
        self.interaction_mode_enabled = False
        self.tray = ""
        if not self.load_instance:
            return

        load_name = self.load_instance.name
        self.canvas = self.make_canvas(load_name)
        self.mv_canvas = self.make_canvas(load_name, klass=CalibrationCanvas)

        loadtable = self.dvc.db.get_loadtable(load_name)
        self.positions = []
        if not loadtable:
            return

        # self.load_instance.create_date = NULL_STR
        # try:
        #     self.load_instance.create_date = loadtable.create_date.strftime('%m/%d/%Y')
        # except BaseException:
        #     self.debug_exception()
        #     self.debug('failed reading LoadTbl create_date from database')

        pos = []
        for ln, poss in groupby_key(loadtable.loaded_positions, "identifier"):
            dbpos = self.dvc.db.get_identifier(ln)
            sample = ""
            project = ""
            material = ""
            if dbpos.sample:
                sample = dbpos.sample.name
                if dbpos.sample.project:
                    project = dbpos.sample.project.name
                if dbpos.sample.material:
                    material = dbpos.sample.material.name

            dblevel = dbpos.level
            irrad = dblevel.irradiation.name
            level = dblevel.name
            irradpos = dbpos.position
            packet = dbpos.packet

            for pi in poss:
                item = self.canvas.scene.get_item(str(pi.position))
                if item:
                    item.fill = True
                    item.add_identifier_label(ln, visible=self.show_identifiers)
                    item.add_sample_label(sample, visible=self.show_samples)

                    oy = (
                        -10 if not (self.show_identifiers or self.show_samples) else -20
                    )
                    wt = "" if pi.weight is None else str(pi.weight)
                    item.add_weight_label(wt, oy=oy, visible=self.show_weights)

                    nxtals = "" if pi.nxtals is None else str(pi.nxtals)
                    item.add_nxtals_label(nxtals, oy=oy, visible=self.show_nxtals)

                    item.nxtals = pi.nxtals
                    item.weight = pi.weight

                    p = LoadPosition(
                        identifier=ln,
                        sample=sample,
                        material=material,
                        weight=pi.weight or 0.0,
                        nxtals=pi.nxtals or 0,
                        project=project,
                        irradiation=irrad,
                        level=level,
                        irrad_position=int(irradpos),
                        position=pi.position,
                        packet=packet or "",
                    )
                    pos.append(p)

        self.positions = pos
        self._set_group_colors()
        self.canvas.request_redraw()
        self.interaction_mode_enabled = True

        if self.stage_manager:
            for hole in self.stage_manager.stage_map.sample_holes:
                self._update_mv_canvas(hole)

    def _update_mv_canvas(self, hole):
        if self.mv_canvas:
            hole = self.stage_manager.stage_map.get_hole(hole)
            pos = hole.corrected_position
            if pos[0] or pos[1]:
                unmapped_pos = self.stage_manager.get_uncalibrated_xy(pos)
                self.mv_canvas.update_hole(hole, unmapped_pos)

    def make_canvas(self, new, editable=True, klass=None, **kw):
        if klass is None:
            klass = LoadingCanvas

        db = self.dvc.db

        lt = db.get_loadtable(new)
        if "view_x_range" not in kw:
            kw["view_x_range"] = (-2, 2)
        if "view_y_range" not in kw:
            kw["view_y_range"] = (-2, 2)
        if "bgcolor" not in kw:
            kw["bgcolor"] = "lightgray"

        c = klass(
            # view_x_range=(-2, 2),
            # view_y_range=(-2, 2),
            # bgcolor="lightgray",
            editable=editable,
            **kw,
        )
        if lt and lt.holderName and lt.holderName != NULL_STR:
            self.tray = lt.holderName
            holes = self.dvc.get_load_holder_holes(lt.holderName)
            load_holder_canvas(c, holes, show_hole_numbers=self.show_hole_numbers)

            for pi in lt.loaded_positions:
                item = c.scene.get_item(str(pi.position))
                if item:
                    item.fill = True
                    item.identifier = pi.identifier
                    item.add_identifier_label(item.identifier)
                    item.add_sample_label(item.sample)

            for pi in lt.measured_positions:
                item = c.scene.get_item(str(pi.position))
                if item:
                    if pi.is_degas:
                        item.degas_indicator = True
                    else:
                        item.measured_indicator = True
        else:
            c.clear_all()

        self._set_group_colors(c)
        return c

    def setup(self):
        db = self.dvc.db
        if db.connected:
            self._refresh_loads(select=False)

            ts = self.dvc.get_load_holders()
            self.debug("Found load holders={}".format(ts))
            if ts:
                ts = self._check_load_holders(ts)
                self.debug("Valid load holders={}".format(ts))
                self.trays = ts

            us = db.get_usernames()
            if us:
                self.available_user_names = us

            return True

    def set_load_name(self, name):
        load_instance = next((i for i in self.loads if i.name == name), None)
        if load_instance:
            self.selected_instances = [load_instance]

    def configure_pdf(self):
        options = self._pdf_writer.options

        options.orientation = "portrait"
        options.left_margin = 0.5
        options.right_margin = 0.5
        options.top_margin = 0.5
        options.bottom_margin = 0.5

        options.load()
        info = options.edit_traits()
        if info.result:
            options.dump()

    def save_pdf(self):
        self.debug("save pdf")

        if self.load_instance:
            ln = self.load_instance.name
            root = self.save_directory
            if not root or not os.path.isdir(root):
                root = paths.loading_dir

            ps = ", ".join({p.project for p in self.grouped_positions})

            un = self.username

            dt = datetime.now()
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            meta = dict(load_name=ln, username=un, load_date=date_str, projects=ps)

            path = os.path.join(root, "{}.pdf".format(ln))

            options = self._pdf_writer.options

            osl = self.show_identifiers
            osw = self.show_weights
            oshn = self.show_hole_numbers
            oss = self.show_samples

            for attr in ("identifiers", "weights", "hole_numbers", "samples"):
                attr = "show_{}".format(attr)
                setattr(self, attr, getattr(options, attr))

            # c = self.canvas.clone_traits()
            self._pdf_writer.build(
                path, self.positions, self.grouped_positions, self.canvas, meta
            )
            if options.view_pdf:
                view_file(path)

            # old refresh code after a save
            # on = self.load_name
            # self.canvas = None
            # self.load_name = ''
            # self.load_name = on
            self._refresh()

            self.show_identifiers = osl
            self.show_weights = osw
            self.show_hole_numbers = oshn
            self.show_samples = oss

        else:
            self.information_dialog("Please select a load")

    def save_tray_pdf(self):
        p = os.path.join(paths.loading_dir, self.tray)
        gc = PdfPlotGraphicsContext(filename=p)
        gc.render_component(self.canvas)
        gc.save()

    def save(self, save_positions=True, inform=False):
        self.debug("saving load to database")
        self._save_load()
        if save_positions:
            self._save_positions(self.load_instance.name)
        self.dirty = False

        if inform:
            msg = "Saved {} to database".format(self.load_instance.name)
            self.information_dialog(msg)

        return True

    def goto(self, hole, block=False, capture=False):
        self.debug("goto {}".format(hole))
        if not self.stage_manager:
            self.warning_dialog("No Stage Manager")
            return

        if not self.stage_manager.moving():
            if isinstance(hole, str):
                hole = int(hole)

            if not isinstance(hole, int):
                hole = int(hole.name)

            self.stage_manager.move_to_hole(hole)
            if block:
                time.sleep(0.05)
                while self.stage_manager.move_thread.isRunning():
                    time.sleep(0.05)

                if capture:
                    name = hole
                    if isinstance(capture, str):
                        name = "{}{}".format(hole, capture)
                    self._capture(name)

                self._update_mv_canvas(hole)

    # private
    def _capture(self, name):
        loadname = self.load_instance.name
        dirpath = os.path.join(paths.loading_dir, loadname)
        self.stage_manager.snapshot(
            name=name, directory=dirpath, render_canvas=False, inform=False
        )

    def _check_load_holders(self, ts):
        ns = []
        for ti in ts:
            try:
                self.dvc.get_load_holder_holes(ti)
                ns.append(ti)
            except MetaObjectException as e:
                self.warning(e)
            except BaseException:
                self.debug_exception()
                self.warning_dialog(
                    '"{}" is an invalid load holder file. '
                    "Holder unavailable until its fixed".format(ti)
                )
        return ns

    def _get_load_instances(self):
        loads = self.dvc.db.get_loads()
        if loads is None:
            loads = []

        return [
            Load(
                name=li.name,
                tray=li.holderName,
                create_date=li.create_date.strftime("%m/%d/%Y"),
            )
            for li in loads
        ]

    # def _get_last_load(self):
    #     lt = self.dvc.db.get_loadtable()
    #     if lt:
    #         self.load_name = lt.name
    #
    #     return self.load_name

    def _set_canvas_hole_selected(self, item):
        item.fill = True

        item.add_identifier_label(
            self.identifier, visible=self.show_identifiers, oy=-10
        )
        item.add_sample_label(self.sample, visible=self.show_samples, oy=-10)
        oy = -10 if not (self.show_identifiers or self.show_samples) else -20
        item.add_weight_label(str(self.weight), visible=self.show_weights, oy=oy)
        item.add_nxtals_label(str(self.nxtals), visible=self.show_nxtals, oy=oy)
        item.weight = self.weight
        item.nxtals = self.nxtals
        item.note = self.note
        item.sample = self.sample
        item.irradiation = "{} {}{}".format(
            self.irradiation, self.level, self.irradiation_hole
        )

    def _deselect_position(self, canvas_hole):
        # remove from position list
        pid = int(canvas_hole.name)
        p = next((p for p in self.positions if p.position == pid), None)
        if p is not None:
            self.positions.remove(p)

        # clear fill
        canvas_hole.fill = False
        canvas_hole.clear_text()
        self.foot_pedal.active_idx = pid

    def _new_position(self, canvas_hole):
        pid = int(canvas_hole.name)
        self._new_position_factory(pid)
        self._set_canvas_hole_selected(canvas_hole)

    def _new_position_factory(self, pid):
        lp = LoadPosition(
            identifier=self.identifier,
            irradiation=self.irradiation,
            level=self.level,
            irrad_position=int(self.irradiation_hole),
            sample=self.sample,
            material=self.material,
            project=self.project,
            position=pid,
            nxtals=self.nxtals,
            weight=self.weight,
            note=self.note,
        )
        self.positions.append(lp)

    def _auto_increment_identifier(self, force=False):
        if (force or self.auto_increment) and self.identifier:
            idx = self.identifiers.index(self.identifier)
            try:
                self.identifier = self.identifiers[idx + 1]
            except IndexError:
                idx = self.levels.index(self.level)
                try:
                    self.level = self.levels[idx + 1]
                    self.identifier = self.identifiers[0]
                    self.debug("increment level {}".format(self.level))
                except IndexError:
                    idx = self.irradiations.index(self.irradiation)
                    try:
                        self.irradiation = self.irradiations[idx + 1]
                        self.level = self.levels[0]
                        self.identifier = self.identifiers[0]
                    except IndexError:
                        print(
                            "lm autoincrement",
                            self.level,
                            self.levels,
                            self.level in self.levels,
                            self.identifier,
                        )

    def _save_load(self):
        db = self.dvc.db
        nln = self.new_load_name
        if not self.username:
            self.warning_dialog("Please select a User")
            return

        if nln:
            self.info("adding load {} {} to database".format(nln, self.tray))

            db.add_load(nln, holder=self.tray, username=self.username)
            db.flush()

            self._refresh_loads()

            # self._get_last_load()
            self.new_load_name = ""

    def _save_positions(self, name):
        db = self.dvc.db
        lt = db.get_loadtable(name=name)

        for li in lt.loaded_positions:
            db.delete(li)

        for pp in self.positions:
            ln = pp.identifier
            self.info(
                "updating positions for load:{}, identifier: {}".format(lt.name, ln)
            )

            self.debug("weight: {} note: {}".format(pp.weight, pp.note))

            i = db.add_load_position(
                ln,
                position=pp.position,
                weight=pp.weight,
                note=pp.note,
                nxtals=pp.nxtals,
            )
            lt.loaded_positions.append(i)
        db.commit()

    def _new_load_view(self):
        v = okcancel_view(
            Item("new_load_name", label="Name"),
            Item("tray", editor=EnumEditor(name="trays")),
            title="New Load Name",
            width=300,
        )
        return v

    def _refresh_loads(self, select=True):
        self.loads = self._get_load_instances()
        if self.loads and select:
            self.selected_instances = self.loads[-1:]

    def _set_group_colors(self, canvas=None):
        if canvas is None:
            canvas = self.canvas

        cs = {}
        if self.use_cmap:
            c = next(
                (k for k, v in color_map_dict.items() if v == self.cmap_name), None
            )
            if c:
                c = c(DataRange1D(low=0.0, high=1.0))

            lns = sorted(list({p.identifier for p in self.positions}))
            nl = len(lns)

            scene = canvas.scene

            vs = c.map_screen(linspace(0, 1, nl))
            cs = dict(zip(lns, [list(vi[:-1]) for vi in vs]))

        for i, p in enumerate(self.positions):
            color = cs.get(p.identifier, (1, 1, 0))
            fcolor = ",".join([str(int(x * 255)) for x in color])
            p.color = color
            # for pp in p.positions:
            pp = scene.get_item(p.position, klass=LoadIndicator)
            if pp is not None:
                pp.fill_color = fcolor

    @cached_property
    def _get_grouped_positions(self):
        gs = []
        for idn, poss in groupby_key(self.positions, "identifier"):
            poss = list(poss)
            gp = GroupedPosition(identifier=idn, meta_position=poss[0], positions=poss)
            gs.append(gp)

        return gs

    def _get_sample_info(self):
        return "{} {}{} {}".format(
            self.identifier, self.level, self.irradiation_hole, self.sample
        )

    # ==========================================================================
    # handlers
    # ==========================================================================
    @on_trait_change("level")
    def _get_identifiers(self):
        db = self.dvc.db
        r = []
        if db.connected:
            level = db.get_irradiation_level(self.irradiation, self.level)
            if level:
                r = sorted(
                    [str(li.identifier) for li in level.positions if li.identifier]
                )
                if r:
                    self.identifier = r[0]

        self.identifiers = r

    def _identifier_changed(self, new):
        if self.dvc.db.connected and new:
            pos = self.dvc.db.get_identifier(new)
            self.irradiation_hole = pos.position
            self.packet = pos.packet or ""
            try:
                dbsample = pos.sample
                if dbsample:
                    self.sample = dbsample.name
                    if dbsample.material:
                        self.material = dbsample.material.name
                    if dbsample.project:
                        self.project = dbsample.project.name

            except AttributeError:
                pass
        else:
            self.sample = ""
            self.packet = ""
            self.material = ""
            self.project = ""
            self.irradiation_hole = 0

    def _archive_button_fired(self):
        # ls = LoadSelection(loads=self.loads)
        # info = ls.edit_traits()
        # if info.result:
        #
        #     db = self.dvc.db
        #     loads = db.get_load_names(names=ls.selected)
        #     for li in loads:
        #         li.archived = True
        #     db.commit()
        #     self.loads = self._get_load_instances()

        if not self.selected_instances:
            self.information_dialog("Please select a set of loads to archive")
            return

        if self.confirmation_dialog(
            "Are you sure you want to Archive the selected Loads?"
        ):
            self.dvc.archive_loads([li.name for li in self.selected_instances])
            self._refresh_loads()

    def _unarchive_button_fired(self):
        db = self.dvc.db
        loads = db.get_load_names(archived_only=True)
        ls = LoadSelection(loads=loads)
        info = ls.edit_traits()
        if info.result:
            db.unarchive_loads(ls.selected)
            self._refresh_loads()

    def _add_button_fired(self):
        db = self.dvc.db
        ln = db.get_latest_load()

        if ln is not None:
            # try to extract an increment from the name
            m = LOAD_REGEX.match(ln.name)
            if m:
                prefix = m.group("prefix")
                inc = m.group("inc")
                nv = "{{:0{}n}}".format(len(inc)).format(int(inc) + 1)
                self.new_load_name = "{}{}".format(prefix, nv)

        info = self.edit_traits(view="_new_load_view")

        if info.result:
            self.save(save_positions=False)
            self._refresh_loads()

    def _delete_button_fired(self):
        if self.load_instance:
            ln = self.load_instance.name
            if not self.confirmation_dialog(
                "Are you sure you want to delete {}?".format(ln)
            ):
                return

            db = self.dvc.db
            # delete the load and any associated records
            dbload = db.get_loadtable(name=ln)
            if dbload:
                for ps in (dbload.loaded_positions, dbload.measured_positions):
                    for pos in ps:
                        db.delete(pos)

                db.delete(dbload)
                db.commit()

            self._refresh_loads()

    # @on_trait_change('load_instance')
    # def _fetch_load(self):
    def _selected_instances_changed(self, new):
        # print('lads', self.load_instance, self.load_instance.name, self.load_instance.create_date)
        if new:
            self.load_instance = new[0]
            self.load_load_by_name()

    def _show_samples_changed(self, new):
        if self.canvas:
            for lp in self.positions:
                item = self.canvas.scene.get_item(str(lp.position))
                item.sample_label.visible = new
                item.weight_label.oy = -20 if new else -10
                item.nxtals_label.oy = -20 if new else -10
                item.sample_label.request_layout()

            self.canvas.request_redraw()

    def _show_identifiers_changed(self, new):
        if self.canvas:
            for lp in self.positions:
                item = self.canvas.scene.get_item(str(lp.position))
                item.identifier_label.visible = new
                item.weight_label.oy = -20 if new else -10
                item.nxtals_label.oy = -20 if new else -10
                item.identifier_label.request_layout()

            self.canvas.request_redraw()

    def _show_weights_changed(self, new):
        if self.canvas:
            for lp in self.positions:
                item = self.canvas.scene.get_item(str(lp.position))
                item.weight_label.visible = new
                item.weight_label.request_layout()

            self.canvas.request_redraw()

    def _show_hole_numbers_changed(self, new):
        if self.canvas:
            for item in self.canvas.scene.get_items(LoadIndicator):
                item.name_visible = new

            self.canvas.request_redraw()

    def _show_nxtals_changed(self, new):
        if self.canvas:
            for lp in self.positions:
                item = self.canvas.scene.get_item(str(lp.position))
                item.nxtals_label.visible = new
                item.nxtals_label.request_layout()
            self.canvas.request_redraw()

    def _cmap_name_changed(self):
        self._set_group_colors()
        self.canvas.request_redraw()
        self.refresh_table = True

    def _note_changed(self):
        if self.canvas:
            sel = self.canvas.selected
            if sel:
                sel.note = self.note
                # pos = next((p for p in self.positions if int(sel.name) in p.positions))
                # pos.note = self.note

    def _weight_changed(self):
        if self._suppress_edit:
            return

        if self.canvas:
            sel = self.canvas.selected
            if sel:
                sel.weight = self.weight
                sel.weight_label.text = self.weight

    def _tray_changed(self, new):
        if self.use_stage and new:
            self.stage_manager.stage_map_name = new

    def _nxtals_changed(self):
        if self._suppress_edit:
            return

        if self.canvas:
            sel = self.canvas.selected
            if sel:
                sel.nxtals = self.nxtals
                sel.nxtals_label.text = self.nxtals

    @on_trait_change("stage_map:stage_map_name")
    def _handle_stage_map_changed(self):
        self.stage_manager.stage_map.zoom_level = self.zoom_level

    @on_trait_change("canvas:increment_event")
    def _increment(self):
        """
        First this after the crystal is loaded into the hole.
        take a picture then move to the next hole

        """
        self.debug("increment")
        idx = self.foot_pedal.active_idx
        item = self.canvas.scene.get_item(idx)
        if item:
            # check to see if sample actually loaded
            if not self.tray_checker.check_frame():
                if self.confirmation_dialog(
                    "It does not appear that a grain is in the hole. Is this correct?"
                ):
                    result = True
                else:
                    result = False
                self.tray_checker.validate_result(result)

                if result:
                    if not self.confirmation_dialog(
                        "Would you like to skip loading this hole?"
                    ):
                        return

            item.fill = True
            self._capture("{}.loaded".format(idx))

            self._new_position_factory(idx)
            self._set_group_colors()
            self.canvas.request_redraw()
            self.goto(idx + 1, block=True, capture=".empty")

            if self.foot_pedal.increment():
                if self.confirmation_dialog("Max count reached. Increment Identifier?"):
                    self._auto_increment_identifier(force=True)

    @on_trait_change("canvas:selected")
    def _update_selected(self, new):
        if not new:
            return

        if not self.load_instance:
            self.warning_dialog("Select a load")
            return

        if self.interaction_mode == "Goto":
            self.goto(new)
        else:
            self._interact(new)

    def set_interaction_mode(self, mode):
        if self.interaction_mode == mode:
            self.interaction_mode = "Entry"
        else:
            self.interaction_mode = mode

    def _interaction_mode_changed(self, new):
        self.debug("interaction mode {}".format(new))
        if self.canvas:
            self.canvas.mode_overlay.mode = new
            if new == "FootPedal":
                info = self.foot_pedal.edit_traits()
                if info.result:
                    self.goto(self.foot_pedal.active_idx, block=True, capture=".empty")
                    self.canvas.set_foot_pedal_mode(new == "FootPedal")
            self.canvas.request_redraw()
        else:
            self.information_dialog("Please select a load")

    def _interact(self, new):
        if not self.canvas.editable:
            if self.use_measured:
                if new.measured_indicator:
                    p = next(
                        (
                            p
                            for p in self.selected_positions
                            if int(new.name) in p.positions
                        ),
                        None,
                    )
                    if p:
                        self.selected_positions.remove(p)
                    else:
                        self.selected_positions.append(
                            LoadPosition(
                                positions=[int(new.name)], identifier=new.identifier
                            )
                        )
            else:
                pp = []
                ps = self.canvas.get_selection()
                for p in ps:
                    po = next(
                        (ppp for ppp in self.positions if int(p.name) == ppp.position),
                        None,
                    )
                    if po:
                        pp.append(po)

                self.selected_positions = pp
            return

        if not self.username:
            self.warning_dialog("Set a username")
            return

        if self.canvas.event_state in ("edit", "info"):
            self.note = new.note
            self.weight = new.weight or 0

        else:
            if new.fill:
                self._deselect_position(new)
            else:
                if not self.identifier:
                    self.warning_dialog("Select a Labnumber")
                else:
                    for i in range(self.npositions):
                        if not new:
                            continue

                        item = self.canvas.scene.get_item(new.name)
                        if item.fill:
                            continue

                        self._new_position(new)
                        new = self.canvas.scene.get_item(str(int(new.name) + 1))
                        if new:
                            self.canvas.set_last_position(int(new.name))

                    self._suppress_edit = True
                    if not self.retain_weight:
                        self.weight = 0
                    if not self.retain_note:
                        self.note = ""
                    if not self.retain_nxtals:
                        self.nxtals = 0
                    self._suppress_edit = False

                    self._auto_increment_identifier()
                    # self._update_span_indicators()
        self._set_group_colors()
        # self.refresh_table = True
        self.dirty = True
        self.canvas.request_redraw()

    def _scan_tray_button_fired(self):
        self.scan_tray()

    def _zoom_level_changed(self, new):
        self.stage_manager.stage_map.zoom_level = new
        with open(os.path.join(paths.appdata_dir, "zoom_level.csv")) as rfile:
            for line in rfile:
                zoom, pxpermm = line.split(",")
                if float(zoom) == float(new):
                    pxpermm = float(pxpermm)
                    break
            else:
                pxpermm = 55
                self.debug(f"no zoom found for {new}. defaulting to {pxpermm}")
        self.stage_manager.set_zoom_manually(pxpermm)
        self.stage_manager.autocenter_manager.pxpermm = pxpermm

    def _focus_stepsperdata_changed(self, new):
        self.focus_motor.stepsperdata = new

    def _focus_position_entry_changed(self, new):
        if new is not None:

            def update(pos):
                self.focus_position_readback = pos

            self.focus_motor.set_position(
                new, use_absolute=True, block=False, update=update
            )
            dev = new - 18

            self.stage_manager.canvas.set_offset(self.get_focus_scalar() * dev)

    def get_focus_scalar(self):
        return self.stage_manager.pxpermm / self.focus_scalar

    def _up_button_fired(self):
        pos = self.focus_motor.data_position
        self.debug(f"up pos={pos}")
        if self.focus_position_readback < 52:
            self.focus_motor.set_position(0.25)
            if self.use_image_shift:
                self.stage_manager.canvas.shift_right(self.get_focus_scalar() / 4.0)
            self._update_focus_position()

    def _down_button_fired(self):
        pos = self.focus_motor.data_position
        self.debug(f"down pos={pos}")
        if self.focus_position_readback > 0:
            self.focus_motor.set_position(-0.25)
            if self.use_image_shift:
                self.stage_manager.canvas.shift_left(self.get_focus_scalar() / 4.0)
            self._update_focus_position()

    def _update_focus_position(self):
        self.focus_position_readback = self.focus_motor.get_position()

    def _home_button_fired(self):
        self._update_focus_position()
        self.focus_motor.home()


# ============= EOF =============================================

# actions
# def generate_results(self):
#     self.debug('generate results')
#     dvc = self.dvc
#     db = dvc.db
#
#     positions = sorted([pp for p in self.positions
#                         for pp in p.positions])
#
#     wb = Workbook()
#     sh = wb.add_sheet('Results')
#
#     for i, attr in enumerate(('Analysis', 'Position', 'Age',
#                               'Error', 'Weight', 'Note')):
#         wb.sheet(0, i, attr)
#
#     wb.nrows = 1
#
#     def func(x, prog, i, n):
#         dbmps = db.get_measured_positions(self.load_name, x)
#         dbpos = db.get_load_position(self.load_name, x)
#
#         weight, note = dbpos.weight, dbpos.note
#
#         for dbmp in dbmps:
#             rid = dbmp.analysis.record_id
#             # rid = 1
#             if prog:
#                 prog.change_message('Write results for {},{}'.format(rid, x))
#
#             # ai = dvc.make_analyses((rid,))
#             age, error = 0, 0
#
#             sh.write(wb.nrows, 0, rid)
#             sh.write(wb.nrows, 1, x)
#             sh.write(wb.nrows, 2, age)
#             sh.write(wb.nrows, 3, error)
#             sh.write(wb.nrows, 4, weight)
#             sh.write(wb.nrows, 5, note)
#             wb.nrows += 1
#
#     progress_iterator(positions, func, threshold=1)
#
#     path, _ = unique_path(paths.load_results_dir, self.load_name, extension='.xls')
#     wb.save(path)
