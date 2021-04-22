# ===============================================================================
# Copyright 2020 ross
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
from enable.component_editor import ComponentEditor
from traits.api import Str, List, Instance, Property, Button
from traitsui.api import TabularEditor, VGroup, Item, UItem, HSplit, HGroup
from traitsui.tabular_adapter import TabularAdapter

from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.canvas.utils import load_holder_canvas
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.strings import SpacelessStr
from pychron.core.utils import alpha_to_int, alphas
from pychron.entry.editors.base_editor import ModelView
from pychron.entry.tray_maker import TrayMaker
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.loggable import Loggable


class TrayAdapter(TabularAdapter):
    columns = [('Name', 'name')]
    name_text = Property

    def _get_name_text(self):
        return self.item


class EditView(ModelView):
    title = 'Edit Level'

    def traits_view(self):
        editor = TabularEditor(adapter=TrayAdapter(),
                               editable=False,
                               selected='selected_tray')
        tray_grp = VGroup(HGroup(icon_button_editor('add_tray_button', 'add',
                                                    tooltip='Add a tray from file')),
                          HSplit(UItem('trays', editor=editor, width=0.25),
                                 UItem('canvas', editor=ComponentEditor(), width=0.75)),
                          label='Tray')

        v = okcancel_view(VGroup(HGroup(Item('name')),
                                 BorderVGroup(UItem('level_note', style='custom'), label='Level Note'),
                                 tray_grp),
                          width=550,
                          height=650,
                          title=self.title)
        return v


class AddView(EditView):
    title = 'Add Level'


class PackageLevelEditor(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')
    level_note = Str
    name = SpacelessStr
    selected_tray = Str
    irradiation = Str
    trays = List
    add_tray_button = Button
    canvas = Instance(IrradiationCanvas, ())

    _add_view_klass = AddView
    _edit_view_klass = EditView

    _check_attrs = (('name', 'No name enter for this level. Would you like to enter one?'),
                    ('selected_tray', 'No tray selected for this level. Would like to select one?'))
    _tagname = 'Package'

    def edit(self):
        self._edit_level()

    def add(self):
        return self._add_level()

    def _save_level(self):
        prname = 'NoProduction'
        db = self.dvc.db
        # add to database
        db.add_irradiation_level(self.name, self.irradiation,
                                 self.selected_tray,
                                 prname,
                                 0,
                                 self.level_note)

        # add to repository
        meta_repo = self.dvc.meta_repo
        meta_repo.add_level(self.irradiation, self.name)
        meta_repo.update_productions(self.irradiation, self.name, prname)
        meta_repo.add_production_to_irradiation(self.irradiation, prname, {})

        meta_repo.commit('Added level {} to {}'.format(self.name, self.irradiation))
        return True

    def _edit_level(self):
        pass

    def _add_level(self):
        irrad = self._pre_add_level()
        if irrad:
            av = self._add_view_klass(model=self)
            info = av.edit_traits()
            while 1:
                if info.result:
                    for attr, msg in self._check_attrs:
                        info = self._check_attr_set(av, attr, msg)
                        if info == 'break':
                            break
                        elif info is not None:
                            continue

                    if not next((li for li in irrad.levels if li.name == self.name), None):
                        if self._save_level():
                            return self.name
                        else:
                            break
                    else:
                        self.warning_dialog('Level {} already exists for {} {}'.format(self.name, self._tagname,
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

    def _pre_add_level(self):
        irrad = self.irradiation
        db = self.dvc.db

        irrad = db.get_irradiation(irrad)
        if irrad.levels:
            level = irrad.levels[-1]

            self.z = level.z or 0

            if level.holder:
                self.selected_tray = next((t for t in self.trays if t == level.holder), '')

            nind = alpha_to_int(level.name) + 1
            self.name = alphas(nind)
        return irrad

    def _selected_tray_changed(self):
        holes = self.dvc.meta_repo.get_irradiation_holder_holes(self.selected_tray)
        if holes:
            load_holder_canvas(self.canvas, holes)

    def _add_tray_button_fired(self):
        # self.warning_dialog('Adding trays has been disabled. Contact pychron developers')
        tm = TrayMaker(names=self.dvc.meta_repo.get_irradiation_holder_names())
        info = tm.edit_traits()
        print(info.result, tm.name)
        if info.result and tm.name:
            self.dvc.meta_repo.make_geometry_file(tm.name, tm.holes())
            self.load_trays()

    def load_trays(self):
        self.trays = self.dvc.meta_repo.get_irradiation_holder_names()
# ============= EOF =============================================
