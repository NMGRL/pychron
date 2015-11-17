# ===============================================================================
# Copyright 2014 Jake Ross
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
from datetime import datetime
import os

from enable.component_editor import ComponentEditor
from pyface.constant import OK, YES, NO
from pyface.file_dialog import FileDialog
from traits.api import List, Instance, Str, Float, Any, Button, Property, HasTraits
from traitsui.api import View, Item, TabularEditor, HGroup, UItem, VSplit, Group, VGroup, \
    HSplit
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.canvas.utils import load_holder_canvas, iter_geom
from pychron.database.defaults import load_irradiation_map, parse_irradiation_tray_map
from pychron.entry.editors.base_editor import ModelView
from pychron.entry.editors.production import IrradiationProduction
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import ALPHAS


class NewProduction(HasTraits):
    name = Str
    reactor = Str

    def traits_view(self):
        v = View(HGroup('name', 'reactor'),
                 buttons=['OK', 'Cancel', 'Revert'],
                 title='New Production Ratio',
                 kind='livemodal')
        return v


class ProductionAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Reactor', 'reactor'), ('Last Modified', 'last_modified')]
    font = '10'


class TrayAdapter(TabularAdapter):
    columns = [('Name', 'name')]
    name_text = Property

    def _get_name_text(self):
        return self.item


class EditView(ModelView):
    title = 'Edit Level'

    def traits_view(self):
        pr_group = VGroup(HGroup(icon_button_editor('add_production_button', 'database_add',
                                                    tooltip='Add a Production Ratio'),
                                 icon_button_editor('edit_production_button', 'database_edit',
                                                    enabled_when='selected_production',
                                                    tooltip='Edit Production Ratio')),
                          VSplit(UItem('productions', editor=TabularEditor(adapter=ProductionAdapter(),
                                                                           editable=False,
                                                                           selected='selected_production')),
                                 UItem('selected_production', style='custom')),
                          label='Production Ratios')

        editor = TabularEditor(adapter=TrayAdapter(),
                               editable=False,
                               selected='selected_tray')
        tray_grp = VGroup(HGroup(icon_button_editor('add_tray_button', 'add',
                                                    tooltip='Add a tray from file')),
                          HSplit(UItem('trays', editor=editor, width=0.25),
                                 UItem('canvas', editor=ComponentEditor(), width=0.75)),
                          label='Tray')

        v = View(Item('name'),
                 VGroup(UItem('level_note', style='custom'), label='Level Note', show_border=True),
                 Group(
                     pr_group,
                     tray_grp,
                     layout='tabbed'),
                 resizable=True,
                 width=550,
                 height=650,
                 title=self.title,
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v


class AddView(EditView):
    title = 'Add Level'


class LevelEditor(Loggable):
    db = Any

    level_note = Str
    name = Str
    selected_tray = Str
    z = Float
    selected_production = Instance(IrradiationProduction, ())

    productions = List
    trays = List

    canvas = Instance(IrradiationCanvas, ())

    add_production_button = Button
    edit_production_button = Button
    add_tray_button = Button

    def edit(self):
        self._load_productions()
        self._edit_level()

    def add(self):
        self._load_productions()
        return self._add_level()

    def _edit_level(self):
        orignal_name = self.name
        db = self.db
        with db.session_ctx():
            level = db.get_irradiation_level(self.irradiation, self.name)

            self.z = level.z or 0
            # if level.production:
            # self.selected_production = next((p for p in self.productions
            # if p.name == level.production.name), None)
            original_tray = None
            if level.holder:
                self.selected_tray = next((t for t in self.trays if t == level.holder), None)
                original_tray = self.selected_tray

            if level.note:
                self.level_note = level.note
            else:
                self.level_note = ''

            ev = EditView(model=self)
            info = ev.edit_traits()
            while 1:
                if info.result:
                    if self.name != orignal_name:
                        ret = self.confirmation_dialog('You have changed the name for this level.\n\n'
                                                       'Would you like to rename "{}" to "{}" (Yes) '
                                                       'or add a new level named "{}" (No)'.format(orignal_name,
                                                                                                   self.name,
                                                                                                   self.name),
                                                       cancel=True, return_retval=True)
                        if ret == YES:
                            level.name = self.name
                        elif ret == NO:
                            self._add_level()
                        else:
                            return

                    level.note = self.level_note
                    level.z = self.z

                    if original_tray != self.selected_tray:
                        self._save_tray(level, original_tray)

                    break
                else:
                    break

        return self.name

    def _save_tray(self, level, original_tray):
        db = self.db
        tr = db.get_irradiation_holder(self.selected_tray)
        n = len(tuple(iter_geom(tr.geometry)))
        on = len(level.positions)
        if n < on:
            if any([p.labnumber.analyses for p in level.positions[n:]]):
                self.warning_dialog('Cannot change tray from "{}" to "{}" '
                                    'This change would orphan irradiation identifiers '
                                    'that have associated analyses'.format(original_tray, self.selected_tray))
            elif self.confirmation_dialog('You are about to orphan {} irradiation identifiers. '
                                          'Are you sure you want to continue?'.format(on - n)):

                level.holder = tr
                for p in level.positions[n:]:
                    self.debug('deleting {} {} {} {}'.format(level.irradiation.name,
                                                             level.name,
                                                             p.position,
                                                             p.labnumber.identifier))
                    db.delete_irradiation_position(p)
        else:
            level.holder = tr

    def _add_level(self):
        irrad = self.irradiation
        db = self.db
        with db.session_ctx():
            irrad = db.get_irradiation(irrad)
            nind = 0
            if irrad.levels:
                level = irrad.levels[-1]

                self.z = level.z

                if level.holder:
                    self.selected_tray = next((t for t in self.trays if t == level.holder), None)

                if level.name in ALPHAS:
                    nind = ALPHAS.index(level.name) + 1

            try:
                self.name = ALPHAS[nind]
            except IndexError:
                self.warning_dialog('Too many levels max level={}'.format(ALPHAS[-1]))
                return

            av = AddView(model=self)
            info = av.edit_traits()
            while 1:
                if info.result:
                    for attr, msg in (('name', 'No name enter for this level. Would you like to enter one?'),
                                      ('selected_production',
                                       'No Production Ratios selected for this level. Would you like to select one?'),
                                      ('selected_tray', 'No tray selected for this level. Would like to select one?')):
                        info = self._check_attr_set(av, attr, msg)
                        if info == 'break':
                            break
                        elif info is not None:
                            continue

                    if not next((li for li in irrad.levels if li.name == self.name), None):
                        db.add_irradiation_level(self.name, irrad,
                                                 self.selected_tray,
                                                 self.z,
                                                 self.level_note)

                        return self.name

                    else:
                        self.warning_dialog('Level {} already exists for Irradiation {}'.format(self.name,
                                                                                                self.irradiation))
                else:
                    break

    def _check_attr_set(self, av, name, msg):
        if not getattr(self, name):
            if self.confirmation_dialog(msg):
                info = av.edit_traits()
                return info
            else:
                return 'break'

    def _load_productions(self):
        db = self.db
        with db.session_ctx():
            ps = []
            for pr in self.repo.get_irradiation_productions():
                p = IrradiationProduction(name=pr.name)
                p.create(pr)
                ps.append(p)

            self.productions = ps

    def _add_production(self):
        pr = NewProduction()
        info = pr.edit_traits()
        db = self.db
        with db.session_ctx():
            while 1:
                if info.result:
                    if db.get_irradiation_production(pr.name):
                        if self.confirmation_dialog(
                                'Production Ratio "{}" already exists. Would you like to enter an new name?'):
                            info = pr.edit_traits()
                            continue
                    else:
                        if self.selected_production:
                            pp = self.selected_production.clone_traits()
                        else:
                            pp = IrradiationProduction()

                        db.add_irradiation_production(name=pr.name, last_modified=datetime.now())
                        pp.name = pr.name
                        self.productions.append(pp)

                        self.selected_production = next((pp for pp in self.productions if pp.name == pr.name), None)
                        self.selected_production.editable = True

                break

    def _edit_production_button_fired(self):
        self.selected_production.editable = True

    def _add_production_button_fired(self):
        self._add_production()

    def _selected_tray_changed(self):
        with self.db.session_ctx():
            holes = self.repo.get_irradiation_holder_holes(self.selected_tray)
            load_holder_canvas(self.canvas, holes)

    def _add_tray_button_fired(self):
        dlg = FileDialog(action='open', default_directory=paths.irradiation_tray_maps_dir)
        if dlg.open() == OK:
            if dlg.path:
                # verify this is a valid irradiation map file
                if parse_irradiation_tray_map(dlg.path) is not None:
                    db = self.db
                    with db.session_ctx():
                        load_irradiation_map(db, dlg.path,
                                             os.path.basename(dlg.path), overwrite_geometry=True)


# ============= EOF =============================================

