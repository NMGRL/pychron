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
from traits.api import HasTraits, cached_property, List, Str, \
    Property, Int, Event, Any, Bool, Button, Float, on_trait_change
from traitsui.api import View, Item, EnumEditor
#============= standard library imports ========================

from itertools import groupby
#============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.canvas.canvas2D.loading_canvas import LoadingCanvas, group_position

from pychron.database.orms.isotope.loading import loading_LoadTable
from pychron.canvas.canvas2D.scene.primitives.primitives import LoadIndicator


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
        #     if not pp + 1 == pi:
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



class LoadPosition(HasTraits):
    labnumber = Str
    sample = Str
    positions = List
    weight = Float
    note = Str

    level = Str
    irradiation = Str
    irrad_position = Int

    irradiation_str = Property

    position_str = Property(depends_on='positions[]')

    def _get_position_str(self):
        return make_position_str(self.positions)

    def _get_irradiation_str(self):
        return '{} {}{}'.format(self.irradiation,
                                self.level,
                                self.irrad_position)


class LoadingManager(IsotopeDatabaseManager):
    dirty = Bool(False)
    loader_name = Str('Foo')

    labnumber = Str
    labnumbers = Property(depends_on='level')
    weight = Float
    note = Str

    '''
        when a hole is selected npositions defines the number of 
        total positions to apply the current information i.e labnumber
    '''
    npositions = Int(1)
    auto_increment = Bool(False)
    #     irradiation_hole = Str
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

    add_button = Button('+')
    delete_button = Button('-')

    new_load_name = Str
    tray = Str
    trays = List

    sample_info = Property(depends_on='labnumber')
    sample = Property(depends_on='labnumber')
    irradiation_hole = Property(depends_on='labnumber')

    retain_weight = Bool(False)
    retain_note = Bool(False)

    show_labnumbers = Bool(False)
    show_weights = Bool(False)
    show_hole_numbers = Bool(False)
    show_spans = Bool(True)

    def save(self):
        self.debug('saving load to database')
        with self.db.session_ctx():
            self._save_load()
            self._save_positions(self.load_name)
            self.dirty=False
        return True

    def setup(self):
        if self.db.connected:
        #             self.populate_default_tables()

            ls = self._get_loads()
            if ls:
                self.loads = ls

            ts = self._get_trays()
            if ts:
                self.trays = ts

            ls = self._get_last_load()
            return True


    def _get_loads(self):
        loads = self.db.get_loads(order=loading_LoadTable.create_date.desc())
        if loads:
            return [li.name for li in loads]

    def _get_trays(self):
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
        pid, pos = self._get_pid_pos(canvas_hole)
        if pid in pos.positions:
            pos.positions.remove(pid)
            canvas_hole.fill = False
            canvas_hole.clear_text()
        else:
            npos = next((pi for pi in self.positions
                         if pid in pi.positions), None)
            print 'fff', npos
            if npos:
                npos.positions.remove(pid)

            pos.positions.append(pid)

        if not pos.positions:
            self.positions.remove(pos)

    def _new_position_group(self, canvas_hole):
        pid = int(canvas_hole.name)

        lp = LoadPosition(labnumber=self.labnumber,
                          irradiation=self.irradiation,
                          level=self.level,
                          irrad_position=int(self.irradiation_hole),
                          sample=self.sample,
                          positions=[pid],
                          weight=self.weight,
                          note=self.note)
        self.positions.append(lp)

        self._set_canvas_hole_selected(canvas_hole)

    def _auto_increment_labnumber(self):
        if self.auto_increment:
            idx=self.labnumbers.index(self.labnumber)
            try:
                self.labnumber=self.labnumbers[idx+1]
            except IndexError:
                idx=self.levels.index(self.level)
                try:
                    self.level=self.levels[idx+1]
                    self.labnumber=self.labnumbers[0]
                except IndexError:
                    idx=self.irradiations.index(self.irradiation)
                    try:
                        self.irradiation=self.irradiations[idx+1]
                        self.level=self.levels[0]
                        self.labnumber=self.labnumbers[0]
                    except IndexError:
                        pass

    def _set_position(self, canvas_hole):

        _, pos = self._get_pid_pos(canvas_hole)
        if pos is not None:
            self._select_position(canvas_hole)
        else:
            self._new_position_group(canvas_hole)

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
                self.canvas = c

            if lt and lt.holder_:
                h = lt.holder_.name
                c.load_scene(h,
                             show_hole_numbers=self.show_hole_numbers)

                for pi in lt.loaded_positions:
                    item = c.scene.get_item(str(pi.position))
                    if item:
                        item.fill = True
                        item.identifier = pi.lab_identifier
                        #                     item.label_item.visible = self.show_labnumbers
                        #                     print item.label_item.visible

                for pi in lt.measured_positions:
                    item = c.scene.get_item(str(pi.position))
                    if item:
                        if pi.is_degas:
                            item.degas_indicator = True
                        else:
                            item.measured_indicator = True
        return c

    def load_load(self, loadtable, group_labnumbers=True, set_tray=True):
        with self.db.session_ctx():
        #         with session(None) as s:
            if isinstance(loadtable, str):
                loadtable = self.db.get_loadtable(loadtable)

            self.positions = []
            if not loadtable:
                return

            if set_tray and loadtable.holder_:
                self.tray = loadtable.holder_.name

            for ln, poss in groupby(loadtable.loaded_positions,
                                    key=lambda x: x.lab_identifier):

                dbln = self.db.get_labnumber(ln)
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
                            ln, ox=-10, oy=-10,
                            visible=self.show_labnumbers
                        )

                        oy = -10 if not self.show_labnumbers else -20
                        wt = '' if pi.weight is None else str(pi.weight)
                        item.add_weight_label(wt, oy=oy,
                                              visible=self.show_weights
                        )
                        item.weight = pi.weight
                        item.note = pi.note
                        item.sample = sample
                        item.irradiation = irradiation
                        #                     print item
                        #                     item.add_text(ln, ox=-10, oy=-10,
                        #                                   visible=self.show_labnumbers
                        #                                   )

                    pos.append(pid)

                if group_labnumbers:
                    self._add_position(ln, pos)
                else:
                    for pi in pos:
                        self._add_position(ln, [pi])
            self._update_span_indicators()

    def _add_position(self, ln, pos):
        pos = map(int, pos)
        ln = self.db.get_labnumber(ln)
        ip = ln.irradiation_position
        level = ip.level
        irrad = level.irradiation

        sample = ln.sample.name if ln.sample else ''

        lp = LoadPosition(labnumber=ln.identifier,
                          sample=sample,
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
                # db.sess.commit()
                #                 sess.commit()
                #                     db.commit()

                ls = self._get_loads()
                self.loads = ls
                self._get_last_load()
                self.new_load_name = ''

    def _save_positions(self, name):
        db = self.db
        with db.session_ctx() as sess:
            lt = db.get_loadtable(name=name)

            #         sess = db.get_session()
            for li in lt.loaded_positions:
                sess.delete(li)

                #         db.flush()
            for pi in self.positions:
                ln = pi.labnumber
                self.info('updating positions for {} {}'.format(lt.name, ln))
                #             self.debug('weight: {} note: {}'.format(pi.weight, pi.note))
                scene = self.canvas.scene
                for pp in pi.positions:
                    ip = scene.get_item(str(pp))
                    self.debug('weight: {} note: {}'.format(ip.weight, ip.note))

                    i = db.add_load_position(ln,
                                             position=pp,
                                             weight=ip.weight,
                                             note=ip.note)
                    lt.loaded_positions.append(i)

            # sess.commit()

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
        return r

    #     def _labnumber_changed(self):
    #         print self.labnumber
    #         level = self.db.get_irradiation_level(self.irradiation, self.level)
    #         if level:
    #             pos = next((pi for pi in level.positions
    #                   if pi.labnumber.identifier == self.labnumber), None)
    #
    #             if pos is not None:
    #                 self.irradiation_hole = str(pos.position)
    #
    #                 sample = pos.labnumber.sample
    #                 if sample:
    #                     self.sample = sample.name

    def _get_irradiation_position_record(self):
        with self.db.session_ctx():
            level = self.db.get_irradiation_level(self.irradiation,
                                                  self.level)
            if level:
                return next((pi for pi in level.positions
                             if pi.labnumber.identifier == self.labnumber), None)

    @cached_property
    def _get_sample(self):
        sample = ''
        if self.db.connected:
            with self.db.session_ctx():
                pos = self._get_irradiation_position_record()
                if pos is not None:
                    dbsample = pos.labnumber.sample
                    sample = dbsample.name if dbsample else ''
        return sample

    @cached_property
    def _get_sample_info(self):
        return '{}{} {}'.format(self.level, self.irradiation_hole, self.sample)

    #         pos = self._get_irradiation_position_record()
    #         if pos is not None:
    #             dbsample = pos.labnumber.sample
    #             sample = dbsample.name if dbsample else ''
    #             return '{}{} {}'.format(self.level, pos.position, sample)

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

    def _update_span_indicators(self):
        canvas=self.canvas
        canvas.clear_spans()
        # for i,p in enumerate(self.positions[:1]):
        for p in self.positions[:1]:
        # for p in self.positions:
            pos=p.positions
            canvas.add_span_indicator(pos, self.show_spans)

    #===============================================================================
    # handlers
    #===============================================================================
    def _add_button_fired(self):
        ln = self.loads[0]
        try:
            self.new_load_name = str(int(ln) + 1)
        except ValueError:
            pass

        info = self.edit_traits(view='_new_load_view')

        if info.result:
            self.save()

    def _delete_button_fired(self):
        ln = self.load_name
        if ln:
            with self.db.session_ctx() as sess:
                # delete the load and any associated records
                dbload = self.db.get_loadtable(name=ln)
                if dbload:
                    for ps in (dbload.loaded_positions, dbload.measured_positions):
                        for pos in ps:
                            sess.delete(pos)

                    sess.delete(dbload)
                    sess.commit()

            self.loads = self._get_loads()
            self.load_name = self.loads[0]

    def _load_name_changed(self, new):
        if new:
            self.tray = ''
            self.load_load(new)

    def _show_spans_changed(self, new):
        if self.canvas:
            self.canvas.set_spans_visibility(new)

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

    @on_trait_change('canvas:selected')
    def _update_selected(self, new):
        if not self.loader_name:
            self.warning_dialog('Set a username')
            return

        if not new:
            return

        if new.fill:
            self._deselect_position(new)
        else:
            if not self.irradiation_hole:
                self.warning_dialog('Select a Labnumber')
            else:
                for i in range(self.npositions):
                    if not new:
                        continue

                    self._set_position(new)
                    new = self.canvas.scene.get_item(str(int(new.name) + 1))

                if not self.retain_weight:
                    self.weight = 0
                if not self.retain_note:
                    self.note = ''

                self._auto_increment_labnumber()
                self._update_span_indicators()

        self.refresh_table = True
        self.dirty=True

        #============= EOF =============================================
