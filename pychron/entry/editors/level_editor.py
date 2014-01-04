#===============================================================================
# Copyright 2014 Jake Ross
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
import struct
from enable.component_editor import ComponentEditor
from pyface.constant import OK, YES, NO
from pyface.file_dialog import FileDialog
from traits.api import List, Instance, Str, Float, Any, Button, Property
from traitsui.api import View, Item, TabularEditor, HGroup, UItem, VSplit, Group, VGroup, \
    HSplit

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.database.defaults import load_irradiation_map, parse_irradiation_tray_map
from pychron.entry.editors.base_editor import ModelView
from pychron.entry.editors.production import IrradiationProduction
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import ALPHAS


def load_holder_canvas(canvas, geom):
    if geom:
        canvas = canvas
        holes = [(x, y, r, str(c + 1))
                 for c, (x, y, r) in iter_geom(geom)]
        canvas.load_scene(holes)


def iter_geom(geom):
    f = lambda x: struct.unpack('>fff', geom[x:x + 12])
    return ((i, f(gi)) for i, gi in enumerate(xrange(0, len(geom), 12)))


class ProductionAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Reactor', 'reactor')]
    font = 'arial 10'


class TrayAdapter(TabularAdapter):
    columns = [('Name', 'name')]
    name_text = Property

    def _get_name_text(self):
        return self.item


class EditView(ModelView):
    title = Str

    def traits_view(self):
        pr_group = VGroup(HGroup(icon_button_editor('add_production_button', 'add',
                                                    tooltip='Add a Production Ratio')),
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

    name = Str
    selected_tray = Str
    z = Float
    selected_production = Instance(IrradiationProduction, ())

    productions = List
    trays = List

    canvas = Instance(IrradiationCanvas, ())
    add_production_button = Button
    add_tray_button = Button

    def edit(self):
        self._load_productions()
        self._edit_level()

    def add(self):
        self._load_productions()
        return self._add_level()

    def _edit_level(self):
        orignal_name=self.name
        db = self.db
        with db.session_ctx():
            level = db.get_irradiation_level(self.irradiation, self.name)

            self.z = level.z
            if level.production:
                self.selected_production = next((p for p in self.productions
                                                 if p.name == level.production.name), None)
            if level.holder:
                self.selected_tray = next((t for t in self.trays if t == level.holder.name), None)

            ev = EditView(model=self)
            info = ev.edit_traits()
            while 1:
                if info.result:
                    if self.name!=orignal_name:
                        ret=self.confirmation_dialog('You have changed the name for this level.\n\n'
                                                      'Would you like to rename "{}" to "{}" (Yes) '
                                                      'or add a new level named "{}" (No)'.format(orignal_name, self.name, self.name), cancel=True, return_retval=True)
                        if ret == YES:
                            level.name = self.name
                        elif ret == NO:
                            self._add_level()
                        else:
                            return

                    pr = db.get_irradiation_production(self.selected_production.name)
                    level.production = pr
                    tr = db.get_irradiation_holder(self.selected_tray)
                    level.tray = tr
                    break
                else:
                    break

        return self.name

    def _add_level(self):
        irrad = self.irradiation
        db = self.db
        with db.session_ctx():
            irrad = db.get_irradiation(irrad)
            nind = 0
            if irrad.levels:
                level = irrad.levels[-1]

                self.z = level.z
                if level.production:
                    self.selected_production = next((p for p in self.productions
                                                     if p.name == level.production.name), None)
                if level.holder:
                    self.selected_tray = next((t for t in self.trays if t == level.holder.name), None)

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
                                                 self.selected_production.name,
                                                 self.z)
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
            for pr in db.get_irradiation_productions():
                p = IrradiationProduction(name=pr.name)
                p.create(pr)
                ps.append(p)

            self.productions = ps

    def _add_production_button_fired(self):
        pass

    def _selected_tray_changed(self):
        with self.db.session_ctx():
            holder = self.db.get_irradiation_holder(self.selected_tray)
            if holder:
                load_holder_canvas(self.canvas, holder.geometry)

    def _add_tray_button_fired(self):
        dlg = FileDialog(action='open', default_directory=paths.irradiation_tray_maps_dir)
        if dlg.open() == OK:
            if dlg.path:
                #verify this is a valid irradiation map file
                if parse_irradiation_tray_map(dlg.path) is not None:
                    db = self.db
                    with db.session_ctx():
                        load_irradiation_map(db, dlg.path,
                                             os.path.basename(dlg.path))


#============= EOF =============================================

