# ===============================================================================
# Copyright 2012 Jake Ross
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

from apptools.preferences.preference_binding import bind_preference
from pyface.constant import YES, CANCEL
from traits.api import Property, Str, cached_property, \
    List, Event, Button, Instance, Bool, on_trait_change, Float, HasTraits, Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value
from uncertainties import std_dev

from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.formatting import floatfmt
from pychron.core.progress import open_progress
from pychron.database.defaults import load_irradiation_map
from pychron.dvc.dvc_irradiationable import DVCIrradiationable
from pychron.entry.editors.irradiation_editor import IrradiationEditor
from pychron.entry.editors.level_editor import LevelEditor, load_holder_canvas
# from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader
from pychron.entry.irradiation_pdf_writer import IrradiationPDFWriter, LabbookPDFWriter
from pychron.entry.irradiation_table_view import IrradiationTableView
from pychron.entry.identifier_generator import IdentifierGenerator
from pychron.paths import paths
from pychron.pychron_constants import PLUSMINUS
from pychron.entry.irradiated_position import IrradiatedPosition


class NeutronDose(HasTraits):
    def __init__(self, power, start, end, *args, **kw):
        self.power = power
        self.start = start.strftime('%m-%d-%Y %H:%M')
        self.end = end.strftime('%m-%d-%Y %H:%M')
        super(NeutronDose, self).__init__(*args, **kw)


class dirty_ctx(object):
    def __init__(self, p):
        self._p = p

    def __enter__(self):
        self._p.suppress_dirty = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._p.suppress_dirty = False


class LabnumberEntry(DVCIrradiationable):
    use_dvc = Bool

    irradiation_tray = Str
    trays = Property

    edit_irradiation_button = Button('Edit')
    edit_level_enabled = Property(depends_on='level')
    edit_irradiation_enabled = Property(depends_on='irradiation')

    tray_name = Str
    irradiated_positions = List(IrradiatedPosition)

    add_irradiation_button = Button('Add Irradiation')
    add_level_button = Button('Add Level')
    edit_level_button = Button('Edit')

    load_file_button = Button('Load File')

    import_irradiation_button = Button

    level_note = Str
    level_production_name = Str
    chronology_items = List
    estimated_j_value = Str
    # ===========================================================================
    # irradiation positions table events
    # ===========================================================================
    selected = Any
    refresh_table = Event

    # ===========================================================================
    #
    # ===========================================================================
    canvas = Instance(IrradiationCanvas, ())
    show_canvas = Bool(True)

    selected_sample = Any
    irradiation_prefix = Str

    dirty = Bool
    suppress_dirty = Bool
    _no_update = Bool

    monitor_name = Str
    monitor_material = Str

    _level_editor = None
    _irradiation_editor = None

    j_multiplier = Float(1e-4)  # j units per hour
    _estimated_j_value = 0

    def __init__(self, *args, **kw):
        super(LabnumberEntry, self).__init__(*args, **kw)

        for key in ('irradiation_prefix', 'monitor_name',
                    'monitor_material', 'j_multiplier'):
            bind_preference(self, key, 'pychron.entry.{}'.format(key))

    def activated(self):
        pass

    def import_irradiation(self):
        self.debug('import irradiation')
        from pychron.entry.dvc_import import do_import_irradiation

        mdb = 'pychron.mass_spec.database.massspec_database_adapter.MassSpecDatabaseAdapter'
        mssource = self.application.get_service(mdb)
        mssource.bind_preferences()

        do_import_irradiation(dvc=self.dvc, sources={mssource: 'Mass Spec'}, default_source='Mass Spec')
        self.updated = True

    def import_analyses(self):
        self.debug('import analyses')
        # from pychron.entry.dvc_import import do_analyses_import

    def import_irradiation_load_xls(self, p):
        self.debug('import irradiation file: {}'.format(p))

        from pychron.entry.dvc_import import do_import_irradiation
        from pychron.entry.xls_irradiation_source import XLSIrradiationSource

        xlssource = XLSIrradiationSource(p)
        name = os.path.basename(p)
        do_import_irradiation(dvc=self.dvc, sources={xlssource: name}, default_source=name)
        self.updated = True

    def get_igsns(self, igsn_repo):
        items = self.selected
        if not items:
            items = self.irradiated_positions

        for item in items:
            if item.sample:
                # need to check for existing IGSN for sample

                self.debug('Get IGSN for sample={}, position={}'.format(item.sample, item.hole))

    def transfer_j(self):
        items = self.selected
        if not items:
            items = self.irradiated_positions

        self.info('Transferring Js for Irradiation={}, Level={}'.format(self.irradiation,
                                                                        self.level))
        from pychron.entry.j_transfer import JTransferer
        klass = 'pychron.mass_spec.database.massspec_database_adapter.MassSpecDatabaseAdapter'
        ms = self.application.get_service(klass)
        if ms:
            ms.bind_preferences()
            if ms.connect():
                jt = JTransferer(pychrondb=self.dvc.db,
                                 massspecdb=ms)
                if jt.do_transfer(self.irradiation, self.level, items):
                    self._save_to_db()

                self.refresh_table = True
        else:
            self.warning_dialog('Unable to Transfer Js. Mass Spec database not configured properly. '
                                'Check Preferences>Database')

    def save_tray_to_db(self, p, name):
        with self.dvc.db.session_ctx():
            load_irradiation_map(self.dvc.db, p, name, overwrite_geometry=True)
        self._inform_save()

    def estimate_j(self):
        j = self._estimated_j_value

        pos = self.selected
        if not pos:
            pos = self.irradiated_positions

        for ip in pos:
            ip.trait_set(j=j, j_err=j * 1e-3)
        self.refresh_table = True

    def select_positions(self, freq, eoflag):
        positions = self.irradiated_positions
        ss = [irrad for i, irrad in enumerate(positions) if (i % freq != 0 if eoflag else i % freq == 0)]
        self.selected = ss

    def set_selected_attr(self, v, attr):
        if self.selected:
            for si in self.selected:
                setattr(si, attr, v)
            self.refresh_table = True

    def set_selected_attrs(self, vs, attrs):
        if self.selected:
            for si in self.selected:
                for v, attr in zip(vs, attrs):
                    setattr(si, attr, v)
            self.refresh_table = True

    def import_sample_metadata(self, p):
        try:
            from pychron.entry.loaders.mb_sample_loader import SampleLoader
        except ImportError, e:
            self.warning_dialog(str(e))
            SampleLoader = None

        if SampleLoader:
            sample_loader = SampleLoader()
            sample_loader.do_import(self, p)

    def make_labbook(self, out):
        """
            assemble a pdf of irradiations
            ask user for list of irradiations
        """

        db = self.dvc.db
        with db.session_ctx():
            irrads = db.get_irradiations(order_func='asc')
            irrads = [irrad.name for irrad in irrads]
            table = IrradiationTableView(irradiations=irrads)
            info = table.edit_traits()
            if info.result:
                if table.selected:
                    w = LabbookPDFWriter()
                    info = w.options.edit_traits()
                    if info.result:
                        irrads = db.get_irradiations(names=table.selected,
                                                     order_func='asc')

                        n = sum([len(irrad.levels) for irrad in irrads])
                        prog = open_progress(n=n)

                        w.build(out, irrads, progress=prog)
                        prog.close()

    def save_pdf(self, out):
        db = self.dvc.db
        with db.session_ctx():
            name = self.irradiation
            irrad = db.get_irradiation(name)
            if irrad:
                w = IrradiationPDFWriter()
                w.build(out, irrad)

    def save(self):
        if self._validate_save():
            self._save_to_db()
            self._inform_save()
            return True

    def generate_identifiers(self):
        if self.check_monitor_name():
            return

        ok = self.confirmation_dialog('Are you sure you want to generate the identifiers for this irradiation?')
        if ok:
            ret = self.confirmation_dialog('Overwrite existing identifiers?', return_retval=True, cancel=True)
            if ret != CANCEL:
                overwrite = ret == YES
                lg = IdentifierGenerator(monitor_name=self.monitor_name,
                                         irradiation=self.irradiation,
                                         overwrite=overwrite,
                                         dvc=self.dvc,
                                         db=self.dvc.db)
                if lg.setup():
                    lg.overwrite = overwrite
                    lg.generate_identifiers()
                    self._update_level()

    def preview_generate_identifiers(self):
        if self.check_monitor_name():
            return

        lg = IdentifierGenerator(monitor_name=self.monitor_name,
                                 overwrite=True,
                                 db=self.dvc.db)
        if lg.setup():
            lg.preview(self.irradiated_positions, self.irradiation, self.level)
            self.refresh_table = True

    def check_monitor_name(self):
        if not self.monitor_name.strip():
            self.warning_dialog('No monitor name set in Preferences.'
                                ' Set before trying to generate identifiers. e.g "FC-2"')
            return True

            # def make_irradiation_load_template(self, p):
            #     from pychron.entry.loaders.irradiation_template import IrradiationTemplate
            #     i = IrradiationTemplate()
            #     i.make_template(p)

        # loader = XLSIrradiationLoader()
        # loader.make_template(p)

    # def import_irradiation_load_xls(self, p):
    #     self.warning_dialog('XLS Irradiation Import not currently available')
    #     return
    #
    #     loader = XLSIrradiationLoader(db=self.dvc.db,
    #                                   dvc=self.dvc)
    #     loader.load_irradiation(p)

    def push_changes(self):
        if self.dvc.meta_repo.has_unpushed_commits():
            if self.confirmation_dialog('You have non-pushed commits. Would you like to share them?'):
                prog = open_progress(2)
                self.info('Pushing changes to meta repo')
                prog.change_message('Pushing changes to meta repo')
                self.dvc.meta_repo.push()
                prog.close()

    # private
    def _load_canvas_analyses(self, db, level):
        poss = db.get_analyzed_positions(level)
        if poss:
            positions = self.irradiated_positions
            canvas = self.canvas
            scene = canvas.scene
            with dirty_ctx(self):
                for idx, cnt in poss:
                    analyzed = bool(cnt)
                    item = scene.get_item(idx)
                    if item:
                        item.measured_indicator = analyzed
                        irp = positions[idx - 1]
                        irp.analyzed = analyzed

    def _load_holder_canvas(self, holes):
        if holes:
            canvas = IrradiationCanvas()
            load_holder_canvas(canvas, holes)
            self.canvas = canvas

    def _load_holder_positions(self, holes):
        self.irradiated_positions = []
        if holes:
            with dirty_ctx(self):
                with no_update(self):
                    self.irradiated_positions = [IrradiatedPosition(hole=int(c), pos=(x, y))
                                                 for x, y, r, c in holes]

    def _validate_save(self):
        """
            validate positions. ensure sample has material and project
        """
        no = []
        for irs in self.irradiated_positions:
            if irs.identifier:
                n = []
                if not irs.sample:
                    n.append('No sample')
                if not irs.project:
                    n.append('No project')
                if not irs.material:
                    n.append('No material')

                if n:
                    no.append('Position={} L#={}\n    {}'.format(irs.hole, irs.identifier, ', '.join(n)))
        if no:
            self.information_dialog('Missing Information\n{}'.format('\n'.join(no)))
            return
        else:
            return True

    def _inform_save(self):
        self.information_dialog('Changes saved to Database')

    def _save_to_db(self):
        db = self.dvc.db

        if not self.dvc.meta_repo.smart_pull():
            return

        with db.session_ctx():
            n = len(self.irradiated_positions)
            prog = open_progress(n)

            for ir in self.irradiated_positions:
                ln = ir.identifier

                dbpos = db.get_irradiation_position(self.irradiation, self.level, ir.hole)
                if not dbpos:
                    dbpos = db.add_irradiation_position(self.irradiation, self.level, ir.hole)

                if ln:
                    dbpos2 = db.get_identifier(ln)
                    if dbpos2:
                        irradname = dbpos2.level.irradiation.name
                        if irradname != self.irradiation:
                            self.warning_dialog('Labnumber {} already exists '
                                                'in Irradiation {}'.format(ln, irradname))
                            return
                    else:
                        dbpos.identifier = ln

                # dbpos.j = irs.j
                # dbpos.j_err = irs.j_err
                self.dvc.meta_repo.update_flux(self.irradiation, self.level,
                                               ir.hole, ir.identifier, ir.j, ir.j_err)

                dbpos.weight = float(ir.weight or 0)
                dbpos.note = ir.note

                sam = ir.sample
                proj = ir.project
                mat = ir.material
                if proj:
                    proj = db.add_project(proj)

                if mat:
                    mat = db.add_material(mat)

                if sam:
                    sam = db.add_sample(sam,
                                        project=proj,
                                        material=mat)
                    dbpos.sample = sam

                prog.change_message('Saving {}{}{} identifier={}'.format(self.irradiation, self.level,
                                                                         ir.hole, ln))
        self.dirty = False
        self._level_changed(self.level)
        if self.dvc.meta_repo.has_staged():
            self.dvc.meta_commit('Labnumber Entry Save')
            self.dvc.meta_push()

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
            # remove leading chars
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
            return j.join((head, '{:03d}'.format(int(last) + 1)))
        except ValueError:
            return name

    def _set_selected_values(self, new):
        sam = self.selected_sample
        if sam:
            ok = True
            if new.identifier:
                ok = self.confirmation_dialog('This position already has a identifier. \
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

    def _auto_increment_irradiation(self):
        if self.irradiations:
            lastname = self.irradiations[0]
        else:
            lastname = '0'

        # try to auto increment the irrad
        if self.irradiation_prefix:
            db = self.dvc.db
            with db.session_ctx():
                def f(table):
                    return (table.name.startswith(self.irradiation_prefix),)

                dbirrad = db.get_irradiations(names=f,
                                              order_func='desc',
                                              limit=1)
                if dbirrad:
                    lastname = dbirrad[0].name
                    # try to increment lastname
                    lastname = self._increment(lastname)

        return lastname

    # @simple_timer()
    def _update_level(self, name=None, debug=False):

        if name is None:
            name = self.level

        self.debug('update level= "{}"'.format(name))
        db = self.dvc.db
        with db.session_ctx() as sess:
            level = db.get_irradiation_level(self.irradiation, name)
            self.debug('retrieved level {}'.format(level))
            if not level:
                self.debug('no level for {}'.format(name))
                return

            self.level_note = level.note or ''
            self.level_production_name = level.production.name if level.production else ''
            if level.holder:
                self.irradiation_tray = level.holder
                holes = self.dvc.meta_repo.get_irradiation_holder_holes(level.holder)
                self._load_holder_positions(holes)
                self._load_holder_canvas(holes)

            try:
                positions = level.positions
                n = len(self.irradiated_positions)
                self.debug('positions in level {}.  \
    available holder positions {}'.format(n, len(self.irradiated_positions)))
                if positions:
                    with dirty_ctx(self):
                        self._make_positions(n, positions)
            except BaseException, e:
                import traceback
                traceback.print_exc()
                print 'excep', e
                self.warning_dialog('Failed loading Irradiation level="{}"'.format(name))
                sess.rollback()

    # @simple_timer()
    def _make_positions(self, n, positions):
        with no_update(self):
            for pi in positions:
                hi = pi.position - 1
                if hi < n:
                    ir = self.irradiated_positions[hi]
                    self._sync_position(pi, ir)
                else:
                    self.debug('extra irradiation position for this tray {}'.format(hi))

    def _sync_position(self, dbpos, ir):
        if dbpos:
            if dbpos.sample:
                ir.sample = dbpos.sample.name
                ir.material = dbpos.sample.material.name
                ir.project = dbpos.sample.project.name
                ir.identifier = dbpos.identifier or ''
                ir.hole = dbpos.position

                item = self.canvas.scene.get_item(str(ir.hole))
                item.fill = bool(dbpos.identifier)

                j, lambda_k = self.dvc.meta_repo.get_flux(self.irradiation, self.level, ir.hole)
                if j:
                    ir.j = nominal_value(j)
                    ir.j_err = std_dev(j)

                ir.note = dbpos.note or ''
                ir.weight = dbpos.weight or 0

    def _get_irradiation_editor(self, **kw):
        ie = self._irradiation_editor
        if ie is None:
            ie = IrradiationEditor(dvc=self.dvc)
            self._irradiation_editor = ie
        ie.trait_set(**kw)
        return ie

    def _get_level_editor(self, **kw):
        ie = self._level_editor
        if ie is None:
            self._level_editor = ie = LevelEditor(db=self.dvc.db,
                                                  meta_repo=self.dvc.meta_repo,
                                                  trays=self.trays)

        ie.trait_set(**kw)
        return ie

    # ===============================================================================
    # property get/set
    # ===============================================================================
    @cached_property
    def _get_trays(self):
        return self.dvc.meta_repo.get_irradiation_holder_names()

    def _get_edit_irradiation_enabled(self):
        return self.irradiation is not None

    def _get_edit_level_enabled(self):
        return self.level is not None

    # ===============================================================================
    # handlers
    # ===============================================================================
    @on_trait_change('canvas:selected')
    def _handle_canvas_selected(self, new):
        if new:
            self.selected = [next((ir for ir in self.irradiated_positions
                                   if ir.hole == int(new.name)), None)]
            if self.selected:
                fill = self._set_selected_values(self.selected[0])
                new.fill = fill

    @on_trait_change('irradiated_positions:+')
    def _set_dirty(self, name, new):
        if not self.suppress_dirty:
            self.dirty = True

    def _import_irradiation_button_fired(self):
        self.import_irradiation()

    def _load_file_button_fired(self):
        p = self.open_file_dialog()
        if p:
            self._load_positions_from_file(p)

    def _add_irradiation_button_fired(self):
        name = self._auto_increment_irradiation()
        irrad = self._get_irradiation_editor(name=name)
        new_irrad = irrad.add()
        if new_irrad:
            pname = 'Irradiation-{}'.format(new_irrad)
            sname = self.monitor_name
            if self.confirmation_dialog('Add default project ({}) and '
                                        'flux monitor sample {{}} for this irradiation?'.format(pname, sname)):
                # add irradiation project for flux monitors
                self.dvc.add_project(pname, principal_investigator=self.default_principal_investigator)

                self.dvc.add_sample(sname, pname, self.monitor_material)
            self.updated = True
            self.irradiation = new_irrad

    def _edit_irradiation_button_fired(self):
        irrad = self._get_irradiation_editor(name=self.irradiation)

        new_irrad = irrad.edit()
        self._suppress_auto_select_irradiation = True
        if new_irrad:
            self.irradiation = new_irrad

        self._suppress_auto_select_irradiation = False

        olevel = self.level
        self._irradiation_changed()
        self.level = olevel

    def _edit_level_button_fired(self):
        editor = self._get_level_editor(name=self.level,
                                        irradiation=self.irradiation)

        new_level = editor.edit()
        if new_level:
            self.updated = True
            self.level = new_level

        self._update_level()

    def _add_level_button_fired(self):
        editor = self._get_level_editor(irradiation=self.irradiation)
        new_level = editor.add()
        if new_level:
            self.updated = True
            self.level = new_level

    def _irradiation_changed(self):
        if self.irradiation:
            self.level = ''

            chron = self.dvc.meta_repo.get_chronology(self.irradiation)
            j = chron.duration * self.j_multiplier
            self._estimated_j_value = j
            self.estimated_j_value = u'{} {}{}'.format(floatfmt(j),
                                                       PLUSMINUS,
                                                       floatfmt(j * 0.001))
            items = [NeutronDose(*args) for args in chron.get_doses()]
            self.chronology_items = items

    def _level_changed(self, new):
        self.debug('level changed "{}"'.format(new))
        self.irradiated_positions = []
        if new:
            self._update_level(debug=True)


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build('_experiment')

    logging_setup('runid')
    m = LabnumberEntry()
    m.configure_traits()
# ============= EOF =============================================
