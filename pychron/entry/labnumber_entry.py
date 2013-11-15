#===============================================================================
# Copyright 2012 Jake Ross
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
from apptools.preferences.preference_binding import bind_preference
from pyface.constant import YES, CANCEL
from traits.api import Property, Str, cached_property, \
    List, Event, Any, Button, Instance, Bool, on_trait_change
from traitsui.api import Image
from pyface.image_resource import ImageResource

#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.entry.irradiation_loader import XLSIrradiationLoader
from pychron.entry.irradiation_pdf_writer import IrradiationPDFWriter, LabbookPDFWriter
from pychron.entry.irradiation_table_view import IrradiationTableView
from pychron.entry.labnumber_generator import LabnumberGenerator
from pychron.paths import paths
from pychron.entry.irradiation import Irradiation
from pychron.entry.level import Level, load_holder_canvas, iter_geom
from pychron.pychron_constants import NULL_STR, ALPHAS
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.entry.irradiated_position import IrradiatedPosition
from pychron.database.orms.isotope.gen import gen_ProjectTable, gen_SampleTable


class LabnumberEntry(IsotopeDatabaseManager):
    irradiation_tray = Str
    trays = Property

    edit_irradiation_button = Button('Edit')
    edit_level_enabled = Property(depends_on='level')
    edit_irradiation_enabled = Property(depends_on='irradiation')

    tray_name = Str
    irradiation_tray_image = Property(Image, depends_on='level, irradiation, saved')
    irradiated_positions = List(IrradiatedPosition)

    add_irradiation_button = Button('Add Irradiation')
    add_level_button = Button('Add Level')
    edit_level_button = Button('Edit')

    load_file_button = Button('Load File')
    generate_labnumbers_button = Button('Generate Labnumbers')
    #===========================================================================
    # irradiation positions table events
    #===========================================================================
    selected = Any
    refresh_table = Event

    #===========================================================================
    #
    #===========================================================================
    canvas = Instance(IrradiationCanvas, ())
    show_canvas = Bool(True)

    selected_sample = Any
    irradiation_prefix = Str

    dirty = False
    initialized = False

    #labnumber_generator = Instance(LabnumberGenerator)
    monitor_name = Str

    def __init__(self, *args, **kw):
        super(LabnumberEntry, self).__init__(*args, **kw)

        #self.labnumber_generator = LabnumberGenerator(db=self.db)

        bind_preference(self, 'irradiation_prefix',
                        'pychron.experiment.irradiation_prefix')
        bind_preference(self, 'monitor_name',
                        'pychron.experiment.monitor_name')

    #    self.populate_default_tables()
    def set_selected_sample(self, new):
        self.selected_sample = new
        #self.canvas.selected_samples=new

    def make_labbook(self, out):
        """
            assemble a pdf of irradiations
            ask user for list of irradiations
        """

        db = self.db
        with db.session_ctx():
            irrads = db.get_irradiations(order_func='asc')
            irrads = [irrad.name for irrad in irrads]
            table = IrradiationTableView(irradiations=irrads)
            info = table.edit_traits()
            if info.result:
                if table.selected:
                    w = LabbookPDFWriter()
                    irrads = db.get_irradiations(names=table.selected,
                                                 order_func='asc')

                    n = sum([len(irrad.levels) for irrad in irrads])
                    prog = self.open_progress(n=n)

                    w.build(out, irrads, progress=prog)

    def save_pdf(self, out):
        db = self.db
        with db.session_ctx():
            name = self.irradiation
            irrad = db.get_irradiation(name)
            if irrad:
                w = IrradiationPDFWriter()
                w.build(out, irrad)

    def save(self):
        self._save_to_db()

    def generate_labnumbers(self):
        ok = True
        ok = self.confirmation_dialog('Are you sure you want to generate the labnumbers for this irradiation?')
        if ok:
            ret = YES
            ret = self.confirmation_dialog('Overwrite existing labnumbers?', return_retval=True, cancel=True)
            if ret != CANCEL:
                overwrite = ret == YES
                lg = LabnumberGenerator(monitor_name=self.monitor_name,
                                        db=self.db)
                prog = self.open_progress()
                lg.generate_labnumbers(self.irradiation, prog, overwrite)
                self._update_level()

    def make_irradiation_load_template(self, p):
        loader = XLSIrradiationLoader()
        n = len(self.irradiated_positions)
        loader.make_template(p, n, self.level)

    def import_irradiation_load_xls(self, p):
        loader = XLSIrradiationLoader(db=self.db,
                                      monitor_name=self.monitor_name)
        prog = self.open_progress()
        loader.progress = prog
        loader.canvas = self.canvas

        loader.load(p, self.irradiated_positions,
                    self.irradiation, self.level)

        self.refresh_table = True

    def _load_holder_canvas(self, holder):
        geom = holder.geometry
        if geom:
            canvas = IrradiationCanvas()
            load_holder_canvas(canvas, geom)
            self.canvas = canvas

    def _load_holder_positions(self, holder):
        self.irradiated_positions = []
        geom = holder.geometry
        if geom:
            self.initialized = False
            self.irradiated_positions = [IrradiatedPosition(hole=c + 1, pos=(x, y))
                                         for c, (x, y, r) in iter_geom(geom)]
            self.initialized = True


        elif holder.name:
            self._load_holder_positons_from_file(holder.name)

    def _load_holder_positons_from_file(self, name):
        p = os.path.join(self._get_map_path(), name)
        self.irradiated_positions = []
        with open(p, 'r') as f:
            line = f.readline()
            nholes, _diam = line.split(',')
            self.initialized = False
            self.irradiated_positions = [IrradiatedPosition(hole=ni + 1)
                                         for ni in range(int(nholes))]
            self.initialized = True

    def _save_to_db(self):
        db = self.db

        with db.session_ctx():
            n = len(self.irradiated_positions)
            prog = self.open_progress(n)

            for irs in self.irradiated_positions:
                ln = irs.labnumber

                sam = irs.sample
                proj = irs.project
                mat = irs.material
                if proj:
                    proj = db.add_project(proj)

                if mat:
                    mat = db.add_material(mat)

                if sam:
                    sam = db.add_sample(sam,
                                        project=proj,
                                        material=mat)
                if ln:
                    dbln = db.get_labnumber(ln)
                    if dbln:
                        pos = dbln.irradiation_position
                        if pos is None:
                            pos = db.add_irradiation_position(irs.hole, dbln, self.irradiation, self.level)
                        else:
                            lev = pos.level
                            irrad = lev.irradiation
                            if self.irradiation != irrad.name:
                                self.warning_dialog(
                                    'Labnumber {} already exists in Irradiation {}'.format(ln, irrad.name))
                                return
                            if irs.hole != pos.position:
                                pos = db.add_irradiation_position(irs.hole, dbln, self.irradiation, self.level)

                    else:
                        dbln = db.add_labnumber(ln, sample=sam, )
                        pos = db.add_irradiation_position(irs.hole, dbln, self.irradiation, self.level)

                    def add_flux():
                        hist = db.add_flux_history(pos)
                        dbln.selected_flux_history = hist
                        f = db.add_flux(irs.j, irs.j_err)
                        f.history = hist

                    if dbln.selected_flux_history:
                        tol = 1e-10
                        flux = dbln.selected_flux_history.flux
                        if abs(flux.j - irs.j) > tol or abs(flux.j_err - irs.j_err) > tol:
                            add_flux()
                    else:
                        add_flux()
                else:
                    dbpos = db.get_irradiation_position(self.irradiation, self.level, irs.hole)
                    if not dbpos or not dbpos.labnumber:
                        dbln = db.add_labnumber('',
                                                unique=False,
                                                sample=sam,
                                                note=irs.note)

                        db.add_irradiation_position(irs.hole, dbln, self.irradiation, self.level)
                    else:
                        dbln = dbpos.labnumber

                if sam:
                    dbln.sample = sam

                dbln.note = irs.note
                prog.change_message('Saving {}{}{} labnumber={}'.format(self.irradiation,
                                                                        self.level,
                                                                        irs.hole,
                                                                        dbln.identifier))

        self.dirty = False
        self.info('chang saved to database')

    def _increment(self, name):
        """
            convert name into an integer and add 1

            potential forms
            NM-001
            NM001
            NM-ABC-001

        """

        if '-' in name:
            args = name.split('-')
            last = args[-1]
            head = '-'.join(args[:-1])
            j = '-'
        else:
            j = ''
            #remove leading chars
            last = name
            head = ''
            while last:
                try:
                    last = int(last)
                    break
                except ValueError:
                    head += last[0]
                    last = last[1:]

        try:
            return j.join((head, '{:03n}'.format(int(last) + 1)))
        except ValueError:
            return name


            #===============================================================================
            # handlers
            #===============================================================================

    @on_trait_change('canvas:selected')
    def _handle_canvas_selected(self, new):
        if new:
            self.selected = [next((ir for ir in self.irradiated_positions
                                   if ir.hole == int(new.name)), None)]
            if self.selected:
                fill = self._set_selected_values(self.selected[0])
                new.fill = fill

    def _set_selected_values(self, new):
        sam = self.selected_sample
        if sam:
            ok = True
            if new.labnumber:
                ok = self.confirmation_dialog('This position already has a labnumber. \
Are you sure you want to change the Sample info? \
THIS CHANGE CANNOT BE UNDONE')

            if ok:
                if new.sample == sam.name:
                    new.sample = ''
                    new.project = ''
                    new.material = ''
                    fill = False
                else:
                    new.sample = sam.name
                    new.project = sam.project
                    new.material = sam.material
                    fill = True

                self.refresh_table = True
                return fill

    def _load_file_button_fired(self):
        p = self.open_file_dialog()
        if p:
            self._load_positions_from_file(p)

    def _add_irradiation_button_fired(self):

        lastname = self.irradiations[0]
        #try to auto increment the irrad
        if self.irradiation_prefix:
            db = self.db
            with db.session_ctx():
                def f(table):
                    return (table.name.startswith(self.irradiation_prefix),)

                dbirrad = db.get_irradiations(names=f,
                                              order_func='desc',
                                              limit=1)
                if dbirrad:
                    lastname = dbirrad[0].name
                    #try to increment lastname
                    lastname = self._increment(lastname)

        irrad = Irradiation(db=self.db,
                            trays=self.trays,
                            name=lastname
        )
        while 1:
            info = irrad.edit_traits(kind='livemodal')
            if info.result:
                result = irrad.save_to_db()
                if result is True:
                    self.irradiation = irrad.name
                    self.dirty = True
                    #self.saved = True

                    break
                elif result is False:
                    break
            else:
                break

    def _edit_irradiation_button_fired(self):
        irrad = Irradiation(db=self.db,
                            trays=self.trays,
                            name=self.irradiation
        )
        irrad.load_production_name()
        irrad.load_chronology()

        info = irrad.edit_traits(kind='livemodal')
        if info.result:
            irrad.edit_db()

    def _edit_level_button_fired(self):
        _prev_tray = self.tray_name
        irradiation = self.irradiation
        level = Level(db=self.db,
                      name=self.level,
                      trays=self.trays
        )
        level.load(irradiation)
        info = level.edit_traits(kind='livemodal')
        if info.result:

            self.info('saving level. Irradiation={}, Name={}, Tray={}, Z={}'.format(irradiation,
                                                                                    level.name,
                                                                                    level.tray,
                                                                                    level.z))
            level.edit_db()

            self.saved = True
            self.irradiation = irradiation
            self.level = level.name

            if _prev_tray != level.tray:
                if not self.confirmation_dialog('Irradiation Tray changed. Copy labnumbers to new tray'):
                    self._load_holder_positions(level.tray)

    def _add_level_button_fired(self):
        irrad = self.irradiation
        db = self.db
        with db.session_ctx():
            irrad = db.get_irradiation(irrad)
            try:
                level = irrad.levels[-1]
                lastlevel = level.name
                lastz = level.z
                nind = list(ALPHAS).index(lastlevel) + 1
            except IndexError:
                nind = 0
                lastz = 0

            try:
                t = Level(name=ALPHAS[nind],
                          z=lastz if lastz is not None else 0,
                          tray=self.tray_name,
                          trays=self.trays)
            except IndexError:
                self.warning_dialog('Too many Trays')
                return

            info = t.edit_traits(kind='livemodal')
            if info.result:
                #irrad = self.db.get_irradiation(irrad)
                if not next((li for li in irrad.levels if li.name == t.name), None):
                    db.add_irradiation_level(t.name, irrad, t.tray, t.z)
                    #self.db.commit()
                    self.level = t.name
                    self.dirty = True
                else:
                    self.warning_dialog('Level {} already exists for Irradiation {}'.format(self.irradiation))

    def _level_changed(self):
        self.debug('level changed')
        self.irradiated_positions = []
        if self.level:
            self._update_level(debug=True)

    # @simple_timer()
    def _update_level(self, name=None, debug=False):

        if name is None:
            name = self.level

        db = self.db
        with db.session_ctx():
            level = db.get_irradiation_level(self.irradiation, name)

            if not level:
                self.debug('no level for {}'.format(name))
                return

            if level.holder:
                self.debug('holder {}'.format(level.holder.name))
                self._load_holder_positions(level.holder)
                self._load_holder_canvas(level.holder)
                #if debug:
            #    return

            positions = level.positions
            n = len(self.irradiated_positions)
            self.debug('positions in level {}.  \
available holder positions {}'.format(n, len(self.irradiated_positions)))
            if positions:
                self.initialized = False
                self._make_positions(n, positions)
                self.initialized = True

    # @simple_timer()
    def _make_positions(self, n, positions):
        for pi in positions:
            hi = pi.position - 1
            if hi < n:
                ir = self.irradiated_positions[hi]
                self._sync_position(pi, ir)
            else:
                self.debug('extra irradiation position for this tray {}'.format(hi))

    def _sync_position(self, dbpos, ir):
        ln = dbpos.labnumber
        if ln:
            position = int(dbpos.position)

            labnumber = ln.identifier if ln else ''
            ir.trait_set(labnumber=str(labnumber), hole=position)

            item = self.canvas.scene.get_item(str(position))
            item.fill = ln.sample

            #         ir = IrradiatedPosition(labnumber=str(labnumber), hole=position)
            #         if labnumber:
            selhist = ln.selected_flux_history
            if selhist:
                flux = selhist.flux
                if flux:
                    ir.j = flux.j
                    ir.j_err = flux.j_err
                    #
            sample = ln.sample
            if sample:
                ir.sample = sample.name
                material = sample.material
                project = sample.project
                if project:
                    ir.project = project.name
                if material:
                    ir.material = material.name

            if dbpos.weight:
                ir.weight = str(dbpos.weight)

            note = ln.note
            if note:
                ir.note = note


                #===============================================================================
                # property get/set
                #===============================================================================

    @cached_property
    def _get_projects(self):
        order = gen_ProjectTable.name.asc()
        projects = [''] + [pi.name for pi in self.db.get_projects(order=order)]
        return projects

    @cached_property
    def _get_samples(self):
        order = gen_SampleTable.name.asc()
        samples = [''] + [si.name for si in self.db.get_samples(order=order)]
        return samples

    @cached_property
    def _get_materials(self):
        materials = [''] + [mi.name for mi in self.db.get_materials()]
        return materials

    def _get_irradiation_tray_image(self):
        p = self._get_map_path()
        db = self.db
        with db.session_ctx():
            level = db.get_irradiation_level(self.irradiation,
                                             self.level)
            holder = None
            if level:
                holder = level.holder
                holder = holder.name if holder else None
            holder = holder if holder is not None else NULL_STR
            self.tray_name = holder
            im = ImageResource('{}.png'.format(holder),
                               search_path=[p]
            )
            return im

    @cached_property
    def _get_trays(self):
        db = self.db
        with db.session_ctx():
            hs = db.get_irradiation_holders()
            ts = [h.name for h in hs]

            #p = os.path.join(self._get_map_path(), 'images')
            #if not os.path.isdir(p):
            #    self.warning_dialog('{} does not exist'.format(p))
            #    return Undefined
            #
            #ts = [os.path.splitext(pi)[0] for pi in os.listdir(p) if not pi.startswith('.')
            #      #                    if not (pi.endswith('.png')
            #      #                            or pi.endswith('.pct')
            #      #                            or pi.startswith('.'))
            #]
            #if ts:
            self.tray = ts[-1]

        return ts

    def _get_map_path(self):
        return os.path.join(paths.setup_dir, 'irradiation_tray_maps')

    def _get_edit_irradiation_enabled(self):
        return self.irradiation is not None

    def _get_edit_level_enabled(self):
        return self.level is not None


    @on_trait_change('irradiated_positions:+')
    def _set_dirty(self, name, new):
        if self.initialized:
            self.dirty = True


if __name__ == '__main__':
    from pychron.helpers.logger_setup import logging_setup

    paths.build('_experiment')

    logging_setup('runid')
    m = LabnumberEntry()
    m.configure_traits()
#============= EOF =============================================
#@on_trait_change('project, sample')
#def _edit_handler(self, name, new):
#    if self.selected:
#
#        for si in self.selected:
#            setattr(si, name, new)
#
#        if name == 'sample':
#            sample = self.db.get_sample(new)
#            material = sample.material
#            material = material.name if material else ''
#
#            for si in self.selected:
#                setattr(si, 'material', material)
#
#
#    self.refresh_table = True

#     def _set_auto_params(self, s, rid):
#         s.labnumber = rid
#         s.sample = self.auto_sample
#         s.project = self.auto_project
#         s.material = self.auto_material
#         s.j = self.auto_j
#         s.j_err = self.auto_j_err
#    def _save_button_fired(self):
#        self._save_to_db()

#     def _freeze_button_fired(self):
#         for si in self.selected:
#             si.auto_assigned = False
#
#     def _thaw_button_fired(self):
#         for si in self.selected:
#             si.auto_assigned = True
#
#
#     @on_trait_change('auto+')
#     def _auto_update(self, obj, name, old, new):
#         cnt = 0
# #        print name, old, new
#         if self.auto_assign:
#             for s in self.irradiated_positions:
#                 rid = str(self.auto_startrid + cnt)
#                 if s.labnumber:
#                     if self.auto_assign_overwrite or s.auto_assigned:
#                         self._set_auto_params(s, rid)
#                         s.auto_assigned = True
#                         cnt += 1
#                 else:
#                     self._set_auto_params(s, rid)
#                     s.auto_assigned = True
#                     cnt += 1
#
#
# #                if self.auto_assign:
# #                if s.labnumber:
# #                    if self.auto_assign_overwrite or name != 'auto_assign':
# #                        self._set_auto_params(s, rid)
# #                        cnt += 1
# #                else:
# #                    self._set_auto_params(s, rid)
# #                    cnt += 1
#
#         self._update_sample_table = True
#     auto_assign = Bool
#     auto_startrid = Int(19999)
#     auto_assign_overwrite = Bool(False)
#     auto_project = Str('Foo')
#     auto_sample = Str('FC-2')
#     auto_material = Str('sanidine')
#     auto_j = Float(1e-4)
#     auto_j_err = Float(1e-7)
#     freeze_button = Button('Freeze')
#     thaw_button = Button('Thaw')

#     _update_sample_table = Event

#    save_button = Button('Save')

#     def traits_view(self):
#         irradiation = Group(
#                             HGroup(
#                                    VGroup(HGroup(Item('irradiation',
#                                                       editor=EnumEditor(name='irradiations')
#                                                       ),
#                                                  Item('edit_irradiation_button',
#                                                       enabled_when='edit_irradiation_enabled',
#                                                       show_label=False)
#                                                  ),
#                                           HGroup(Item('level', editor=EnumEditor(name='levels')),
#                                                  spring,
#                                                  Item('edit_level_button',
#                                                       enabled_when='edit_level_enabled',
#                                                       show_label=False)
#                                                  ),
#                                           Item('add_irradiation_button', show_label=False),
#                                           Item('add_level_button', show_label=False),
# #                                        Item('irradiation_tray',
# #                                             editor=EnumEditor(name='irradiation_trays')
# #                                             )
#                                           ),
#                                    spring,
#                                    VGroup(
#                                           Item('tray_name', style='readonly', show_label=False),
#                                           Item('irradiation_tray_image',
#                                                editor=ImageEditor(),
#                                                height=200,
#                                                width=200,
#                                                style='custom',
#                                                show_label=False),
#                                           ),
#                                         ),
#                             label='Irradiation',
#                             show_border=True
#                             )
#
#         auto = Group(
#                     Item('auto_assign', label='Auto-assign Labnumbers'),
#                     Item('auto_startrid', label='Start Labnumber',
#                          enabled_when='auto_assign'
#                          ),
#                     Item('auto_project', label='Project',
#                          enabled_when='auto_assign'
#                          ),
#                     Item('auto_sample', label='Sample',
#                          enabled_when='auto_assign'
#                          ),
#                     Item('auto_material', label='Material',
#                          enabled_when='auto_assign'
#                          ),
#                      Item('auto_j', format_str='%0.2e', label='Nominal J.'),
#                      Item('auto_j_err', format_str='%0.2e', label='Nominal J Err.'),
#                     Item('auto_assign_overwrite', label='Overwrite exisiting Labnumbers',
#                          enabled_when='auto_assign'
#                          ),
#                       HGroup(Item('freeze_button', show_label=False), Item('thaw_button', show_label=False),
#                               enabled_when='selected'),
#                       show_border=True,
#                       label='Auto-Assign'
#
#                       )
#
#         samples = Group(
#
#                         Item('irradiated_positions',
#                              editor=TabularEditor(adapter=IrradiatedPositionAdapter(),
#                                                   update='_update_sample_table',
#                                                   multi_select=True,
#                                                   selected='selected',
#                                                   operations=['edit']
#                                                   ),
#                              show_label=False
#                              ),
#                         label='Lab Numbers',
#                         show_border=True
#                         )
# #        flux = Group(
# #                     HGroup(
# #                            Item('flux_monitor', show_label=False, editor=EnumEditor(name='flux_monitors')),
# #                            Item('edit_monitor_button', show_label=False)),
# #                     Item('flux_monitor_age', format_str='%0.3f', style='readonly', label='Monitor Age (Ma)'),
# #                     Spring(height=50, springy=False),
# #                     Item('calculate_flux_button',
# #                          enabled_when='calculate_flux_enabled',
# #                          show_label=False),
# #                     label='Flux',
# #                     show_border=True
# #                     )
#         v = View(VGroup(
#                         HGroup(auto, irradiation,
# #                               flux
#                                ),
#                         samples,
#                         HGroup(spring, Item('save_button', show_label=False))
#                         ),
#                  resizable=True,
#                  width=0.75,
#                  height=600,
#                  title='Labnumber Entry'
#                  )
#         return v
