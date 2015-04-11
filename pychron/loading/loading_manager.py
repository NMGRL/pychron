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
import os
from datetime import datetime

from matplotlib.cm import get_cmap, cmap_d
from traits.api import HasTraits, cached_property, List, Str, Instance, \
    Property, Int, Event, Any, Bool, Button, Float, on_trait_change, Enum, RGBColor
from traitsui.api import View, Item, EnumEditor, UItem, ListStrEditor











# ============= standard library imports ========================

from itertools import groupby
# ============= local library imports  ==========================
from pychron.canvas.utils import load_holder_canvas
from pychron.core.helpers.filetools import view_file
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.canvas.canvas2D.loading_canvas import LoadingCanvas, group_position

from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator
from pychron.loading.loading_pdf_writer import LoadingPDFWriter
from pychron.paths import paths


def make_bound(st):
    if len(st) > 1:
        s = '{}-{}'.format(st[0], st[-1])
    else:
        s = '{}'.format(st[0])
    return s


def make_position_str(pos):
    s = ''
    if pos:
        ss = group_position(pos, make_bound)
        # pos = sorted(pos)
        #
        # pp = pos[0]
        # stack = [pp]
        # ss = []
        #
        # for pi in pos[1:]:
        # if not pp + 1 == pi:
        #         ss.append(make_bound(stack))
        #         stack = []
        #
        #     stack.append(pi)
        #     pp = pi
        #
        # if stack:
        #     ss.append(make_bound(stack))

        s = ','.join(ss)
    return s


class LoadSelection(HasTraits):
    loads = List
    selected = List

    def traits_view(self):
        v = View(UItem('loads', editor=ListStrEditor(selected='selected',
                                                     multi_select=True,
                                                     editable=False)),
                 kind='livemodal',
                 width=300,
                 buttons=['OK', 'Cancel'],
                 title='Select Loads to Archive')
        return v


class LoadPosition(HasTraits):
    labnumber = Str
    sample = Str
    project = Str
    positions = List
    weight = Float
    note = Str

    level = Str
    irradiation = Str
    irrad_position = Int

    irradiation_str = Property

    position_str = Property(depends_on='positions[]')
    color = RGBColor

    def _get_position_str(self):
        return make_position_str(self.positions)

    def _get_irradiation_str(self):
        return '{} {}{}'.format(self.irradiation,
                                self.level,
                                self.irrad_position)


maps = [m for m in cmap_d if not m.endswith("_r")]


class LoadingManager(IsotopeDatabaseManager):
    _pdf_writer = Instance(LoadingPDFWriter, ())
    dirty = Bool(False)
    username = Str
    refresh_level = Event
    refresh_irradiation = Event

    available_user_names = List

    labnumber = Str
    labnumbers = Property(depends_on='level')
    weight = Float
    note = Str
    save_directory = Str

    '''
        when a hole is selected npositions defines the number of 
        total positions to apply the current information i.e labnumber
    '''
    npositions = Int(1)
    auto_increment = Bool(False)
    # irradiation_hole = Str
    #     sample = Str

    positions = List

    # table signal/events
    refresh_table = Event
    scroll_to_row = Int
    selected_positions = Any

    load_name = Str
    loads = List

    group_positions = Bool
    show_group_positions = Bool(False)

    canvas = Any

    add_button = Button
    delete_button = Button
    archive_button = Button

    new_load_name = Int
    tray = Str
    trays = List

    sample_info = Property(depends_on='labnumber')
    sample = Property(depends_on='labnumber')
    project = Property(depends_on='labnumber')
    irradiation_hole = Property(depends_on='labnumber')

    retain_weight = Bool(False)
    retain_note = Bool(False)

    show_labnumbers = Bool(False)
    show_weights = Bool(False)
    show_hole_numbers = Bool(False)
    cmap_name = Enum(maps)
    use_cmap = Bool(True)
    interaction_mode = Enum('Entry', 'Info', 'Edit')
    suppress_update = False

    def load(self):
        if self.canvas:
            self.canvas.editable = True
            self.clear()
        return super(LoadingManager, self).load()

    def clear(self):
        self.load_name = ''
        if self.canvas:
            self.canvas.clear_all()

    def load_load_by_name(self, loadtable, group_labnumbers=True):

        self.canvas = self.make_canvas(loadtable)

        with self.db.session_ctx():
            if isinstance(loadtable, (str, unicode)):
                loadtable = self.db.get_loadtable(loadtable)

            self.positions = []
            if not loadtable:
                return

            for ln, poss in groupby(loadtable.loaded_positions,
                                    key=lambda x: x.lab_identifier):
                dbln = self.db.get_labnumber(ln, key='id')
                sample = ''
                if dbln and dbln.sample:
                    sample = dbln.sample.name
                dbirradpos = dbln.irradiation_position
                dblevel = dbirradpos.level

                irrad = dblevel.irradiation.name
                level = dblevel.name
                irradpos = dbirradpos.position
                irradiation = '{} {}{}'.format(irrad, level, irradpos)

                pos = []
                for pi in poss:
                    pid = str(pi.position)
                    item = self.canvas.scene.get_item(pid)
                    if item:
                        item.fill = True
                        item.add_labnumber_label(
                            dbln.identifier,
                            # ox=-10, oy=-10,
                            visible=self.show_labnumbers)

                        oy = -10 if not self.show_labnumbers else -20
                        wt = '' if pi.weight is None else str(pi.weight)
                        item.add_weight_label(wt, oy=oy, visible=self.show_weights)
                        item.weight = pi.weight
                        item.note = pi.note
                        item.sample = sample
                        item.irradiation = irradiation

                    pos.append(pid)

                if group_labnumbers:
                    self._add_position(ln, pos)
                else:
                    for pi in pos:
                        self._add_position(ln, [pi])

        self.positions = sorted(self.positions, key=lambda x: x.positions[0])
        self._set_group_colors()
        self.canvas.request_redraw()

    def make_canvas(self, new, editable=True):
        db = self.db
        with db.session_ctx():

            #         with session(None) as s:
            lt = db.get_loadtable(new)
            c = self.canvas
            if not c:
                c = LoadingCanvas(
                    view_x_range=(-2, 2),
                    view_y_range=(-2, 2),
                    editable=editable)

            if lt and lt.holder_:
                load_holder_canvas(c, lt.holder_.geometry,
                                   show_hole_numbers=self.show_hole_numbers)

                for pi in lt.loaded_positions:
                    item = c.scene.get_item(str(pi.position))
                    if item:
                        item.fill = True
                        item.identifier = pi.labnumber.identifier
                        item.add_labnumber_label(item.identifier)

                for pi in lt.measured_positions:
                    item = c.scene.get_item(str(pi.position))
                    if item:
                        if pi.is_degas:
                            item.degas_indicator = True
                        else:
                            item.measured_indicator = True

        self._set_group_colors(c)
        return c

    def setup(self):
        if self.db.connected:
            ls = self._get_loads()
            if ls:
                self.loads = ls

            ts = self._get_trays()
            if ts:
                self.trays = ts

            us = self._get_users()
            if us:
                self.available_user_names = us

            # ls = self._get_last_load()
            return True

    # actions
    def configure_pdf(self):
        options = self._pdf_writer.options

        options.orientation = 'portrait'
        options.left_margin = 0.5
        options.right_margin = 0.5
        options.top_margin = 0.5
        options.bottom_margin = 0.5

        options.load_yaml()
        info = options.edit_traits()
        if info.result:
            options.dump_yaml()

    def save_pdf(self):
        # p = LoadingPDFWriter()
        ln = self.load_name
        if ln:
            root = self.save_directory
            if not root or not os.path.isdir(root):
                root = paths.loading_dir

            positions = self.positions
            ps = ', '.join({p.project for p in positions})

            un = self.username

            dt = datetime.now()
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            meta = dict(load_name=ln, username=un,
                        load_date=date_str,
                        projects=ps)

            path = os.path.join(root, '{}.pdf'.format(ln))

            options = self._pdf_writer.options

            osl = self.show_labnumbers
            osw = self.show_weights
            oshn = self.show_hole_numbers

            for attr in ('labnumbers', 'weights', 'hole_numbers'):
                attr = 'show_{}'.format(attr)
                setattr(self, attr, getattr(options, attr))

            # c = self.canvas.clone_traits()
            self._pdf_writer.build(path, positions, self.canvas, meta)
            if options.view_pdf:
                view_file(path)
            on = self.load_name
            self.canvas = None
            self.load_name = ''
            self.load_name = on

            self.show_labnumbers = osl
            self.show_weights = osw
            self.show_hole_numbers = oshn

        else:
            self.information_dialog('Please select a load')

    def save(self):
        self.debug('saving load to database')
        with self.db.session_ctx():
            self._save_load()
            self._save_positions(self.load_name)
            self.dirty = False
        return True

    def set_edit(self):
        if self.canvas:
            self.canvas.event_state = 'edit'
        self.interaction_mode = 'Edit'

    def set_entry(self):

        if self.canvas:
            self.canvas.event_state = 'normal'
        self.interaction_mode = 'Entry'

    def set_info(self):

        if self.canvas:
            self.canvas.event_state = 'info'
        self.interaction_mode = 'Info'

    # private
    def _get_users(self):
        with self.db.session_ctx():
            users = self.db.get_users()
            return [u.name for u in users]

    def _get_loads(self):
        with self.db.session_ctx():
            loads = self.db.get_loads()
            if loads:
                return [li.name for li in loads]

    def _get_trays(self):
        with self.db.session_ctx():
            trays = self.db.get_load_holders()
            if trays:
                ts = [ti.name for ti in trays]
                return ts

    def _get_last_load(self, set_tray=True):

        #         with self.db.session_():
        with self.db.session_ctx():
            lt = self.db.get_loadtable()
            if lt:
                self.load_name = lt.name
                #                 if set_tray and lt.holder_:
                #                     self.load_load(lt, set_tray=set_tray)

        return self.load_name

    def _get_pid_pos(self, canvas_hole):
        pos = next((pi for pi in self.positions
                    if pi.labnumber == self.labnumber), None)

        pid = int(canvas_hole.name)
        return pid, pos

    def _select_position(self, canvas_hole):
        pid, pos = self._get_pid_pos(canvas_hole)
        pos.positions.append(pid)
        self._set_canvas_hole_selected(canvas_hole)

    def _set_canvas_hole_selected(self, item):
        item.fill = True

        item.add_labnumber_label(self.labnumber,
                                 visible=self.show_labnumbers,
                                 oy=-10)

        oy = -10 if not self.show_labnumbers else -20
        item.add_weight_label(str(self.weight),
                              visible=self.show_weights,
                              oy=oy)
        item.weight = self.weight
        item.note = self.note
        item.sample = self.sample
        item.irradiation = '{} {}{}'.format(self.irradiation, self.level,
                                            self.irradiation_hole)

    def _deselect_position(self, canvas_hole):

        # pid, pos = self._get_pid_pos(canvas_hole)
        # print canvas_hole,pid, pos
        # if pid in pos.positions:
        #     pos.positions.remove(pid)
        #     canvas_hole.fill = False
        #     canvas_hole.clear_text()
        # else:
        #     npos = next((pi for pi in self.positions
        #                  if pid in pi.positions), None)
        #     print 'fff', npos
        #     if npos:
        #         npos.positions.remove(pid)
        #
        #     pos.positions.append(pid)

        # remove from position list
        pid = int(canvas_hole.name)
        for p in self.positions:
            if pid in p.positions:
                p.positions.remove(pid)
                if not p.positions:
                    self.positions.remove(p)
                break

        # clear fill
        canvas_hole.fill = False
        canvas_hole.clear_text()

    def _new_position_group(self, canvas_hole):
        pid = int(canvas_hole.name)

        lp = LoadPosition(labnumber=self.labnumber,
                          irradiation=self.irradiation,
                          level=self.level,
                          irrad_position=int(self.irradiation_hole),
                          sample=self.sample,
                          project=self.project,
                          positions=[pid],
                          weight=self.weight,
                          note=self.note)
        self.positions.append(lp)

        self._set_canvas_hole_selected(canvas_hole)

    def _auto_increment_labnumber(self):
        if self.auto_increment and self.labnumber:
            idx = self.labnumbers.index(self.labnumber)
            try:
                self.labnumber = self.labnumbers[idx + 1]
            except IndexError:
                idx = self.levels.index(self.level)
                try:
                    self.level = self.levels[idx + 1]
                    self.labnumber = self.labnumbers[0]
                    self.refresh_level = True
                    # print 'increment level', self.level
                except IndexError:
                    idx = self.irradiations.index(self.irradiation)
                    try:
                        self.irradiation = self.irradiations[idx + 1]
                        self.level = self.levels[0]
                        self.labnumber = self.labnumbers[0]
                        self.refresh_irradiation = True
                    except IndexError:
                        pass

                        # print self.level, self.levels, self.level in self.levels, self.labnumber

    def _set_position(self, canvas_hole):

        _, pos = self._get_pid_pos(canvas_hole)
        if pos is not None:
            self._select_position(canvas_hole)
        else:
            self._new_position_group(canvas_hole)

    def _add_position(self, ln, pos):
        pos = map(int, pos)
        ln = self.db.get_labnumber(ln, key='id')
        ip = ln.irradiation_position
        level = ip.level
        irrad = level.irradiation
        sample = ''
        project = ''
        if ln.sample:
            sample = ln.sample.name
            if ln.sample.project:
                project = ln.sample.project.name

        lp = LoadPosition(labnumber=ln.identifier,
                          sample=sample,
                          project=project,
                          irradiation=irrad.name,
                          level=level.name,
                          irrad_position=int(ip.position),
                          positions=pos)

        self.positions.append(lp)

    def _save_load(self):
        db = self.db
        nln = self.new_load_name
        if nln:
            lln = self._get_last_load(set_tray=False)
            if nln == lln:
                return 'duplicate name'
            else:
                self.info('adding load {} {} to database'.format(nln, self.tray))
                db.add_load(nln, holder=self.tray)

                ls = self._get_loads()
                self.loads = ls
                self._get_last_load()
                self.new_load_name = 0

    def _save_positions(self, name):
        db = self.db
        with db.session_ctx() as sess:
            lt = db.get_loadtable(name=name)

            for li in lt.loaded_positions:
                sess.delete(li)

            for pi in self.positions:
                ln = pi.labnumber
                self.info('updating positions for load:{}, labnumber: {}'.format(lt.name, ln))
                scene = self.canvas.scene
                for pp in pi.positions:
                    ip = scene.get_item(str(pp))
                    self.debug('weight: {} note: {}'.format(ip.weight, ip.note))

                    i = db.add_load_position(ln,
                                             position=pp,
                                             weight=ip.weight,
                                             note=ip.note)
                    lt.loaded_positions.append(i)

    @cached_property
    def _get_labnumbers(self):
        db = self.db
        r = []
        if db.connected:
            with db.session_ctx():
                level = db.get_irradiation_level(self.irradiation,
                                                 self.level)
                if level:
                    #             self._positions = [str(li.position) for li in level.positions]
                    r = sorted([li.labnumber.identifier
                                for li in level.positions if li.labnumber])
                    if r:
                        self.labnumber = r[0]
        return r

    def _get_irradiation_position_record(self):
        with self.db.session_ctx():
            level = self.db.get_irradiation_level(self.irradiation,
                                                  self.level)
            if level:
                return next((pi for pi in level.positions
                             if pi.labnumber and pi.labnumber.identifier == self.labnumber), None)

    @cached_property
    def _get_project(self):
        project = ''
        if self.db.connected:
            with self.db.session_ctx():
                pos = self._get_irradiation_position_record()
                try:
                    project = pos.labnumber.sample.project.name
                except AttributeError:
                    pass
        return project

    @cached_property
    def _get_sample(self):
        sample = ''
        if self.db.connected:
            with self.db.session_ctx():
                pos = self._get_irradiation_position_record()
                try:
                    sample = pos.labnumber.sample.name
                except AttributeError:
                    pass
        return sample

    @cached_property
    def _get_sample_info(self):
        return '{}{} {}'.format(self.level, self.irradiation_hole, self.sample)

    @cached_property
    def _get_irradiation_hole(self):
        ir = ''
        if self.db.connected:
            with self.db.session_ctx():
                pos = self._get_irradiation_position_record()
                if pos is not None:
                    ir = pos.position
        return ir

    def _new_load_view(self):
        v = View(Item('new_load_name', label='Name'),
                 Item('tray', editor=EnumEditor(name='trays')),
                 kind='livemodal',
                 title='New Load Name',
                 buttons=['OK', 'Cancel'])
        return v

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _archive_button_fired(self):
        ls = LoadSelection(loads=self.loads)
        info = ls.edit_traits()
        if info.result:
            db = self.db
            with db.session_ctx():
                loads = db.get_loads(names=ls.selected)
                for li in loads:
                    li.archived = True

            self.loads = self._get_loads()

    def _add_button_fired(self):
        db = self.db
        with db.session_ctx():
            ln = db.get_latest_load()
            ln = ln.name

        try:

            nv = int(ln) + 1
        except (ValueError, IndexError), e:
            print 'exception', e
            nv = 1

        self.new_load_name = nv

        info = self.edit_traits(view='_new_load_view')

        if info.result:
            self.save()
            self._refresh_loads()

    def _delete_button_fired(self):
        ln = self.load_name
        if ln:
            if not self.confirmation_dialog('Are you sure you want to delete {}?'.format(ln)):
                return

            with self.db.session_ctx() as sess:
                # delete the load and any associated records
                dbload = self.db.get_loadtable(name=ln)
                if dbload:
                    for ps in (dbload.loaded_positions, dbload.measured_positions):
                        for pos in ps:
                            sess.delete(pos)

                    sess.delete(dbload)
                    sess.commit()

            self._refresh_loads()


    def _refresh_loads(self):
        self.loads = self._get_loads()
        self.load_name = self.loads[0]

    def _load_name_changed(self, new):
        if self.suppress_update:
            return

        if new:
            self.tray = ''
            self.load_load_by_name(new)

    def _show_labnumbers_changed(self, new):
        if self.canvas:
            for lp in self.positions:
                for pid in lp.positions:
                    item = self.canvas.scene.get_item(str(pid))

                    item.labnumber_label.visible = new
                    item.weight_label.oy = -20 if new else -10

            self.canvas.request_redraw()

    def _show_weights_changed(self, new):
        if self.canvas:
            for lp in self.positions:
                for pid in lp.positions:
                    item = self.canvas.scene.get_item(str(pid))
                    item.weight_label.visible = new

            self.canvas.request_redraw()

    def _show_hole_numbers_changed(self, new):
        if self.canvas:
            for item in self.canvas.scene.get_items(LoadIndicator):
                item.name_visible = new

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
        if self.canvas:
            sel = self.canvas.selected
            if sel:
                # pos = next((p for p in self.positions if int(sel.name) in p.positions))
                # pos.weight = self.weight
                sel.weight = self.weight
                sel.weight_label.text = self.weight

    @on_trait_change('canvas:selected')
    def _update_selected(self, new):
        if not self.load_name:
            self.warning_dialog('Select a load')
            return

        if not self.canvas.editable:
            ps = self.canvas.get_selection()
            pp = []
            for p in ps:
                po = next((ppp for ppp in self.positions if int(p.name) in ppp.positions))
                pp.append(po)

            self.selected_positions = pp
            return

        if not self.username:
            self.warning_dialog('Set a username')
            return

        if not new:
            return

        if self.canvas.event_state in ('edit', 'info'):
            self.note = new.note
            self.weight = new.weight

        else:
            if new.fill:
                self._deselect_position(new)
            else:
                if not self.labnumber:
                    self.warning_dialog('Select a Labnumber')
                else:
                    for i in range(self.npositions):
                        if not new:
                            continue

                        item = self.canvas.scene.get_item(new.name)
                        if item.fill:
                            continue

                        self._set_position(new)
                        new = self.canvas.scene.get_item(str(int(new.name) + 1))
                        self.canvas.set_last_position(int(new.name))

                    if not self.retain_weight:
                        self.weight = 0
                    if not self.retain_note:
                        self.note = ''

                    self._auto_increment_labnumber()
                    # self._update_span_indicators()
        self._set_group_colors()
        self.refresh_table = True
        self.dirty = True
        self.canvas.request_redraw()

    def _set_group_colors(self, canvas=None):
        if canvas is None:
            canvas = self.canvas

        if self.use_cmap:
            c = get_cmap(self.cmap_name)
        else:
            c = lambda x: (1, 1, 0, 1)

        # n = len(self.positions)
        nl = len({p.labnumber for p in self.positions})

        scene = canvas.scene
        cs = {}
        cnt = 0
        for i, p in enumerate(self.positions):
            if p.labnumber in cs:
                color = cs[p.labnumber]
            else:
                color = c(cnt / float(nl))
                color = color[:-1]
                cs[p.labnumber] = color
                cnt += 1

            p.color = color
            for pp in p.positions:
                pp = scene.get_item(str(pp), klass=LoadIndicator)
                pp.fill_color = color

# ============= EOF =============================================
