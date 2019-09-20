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

import os

# ============= enthought library imports =======================
from enable.component_editor import ComponentEditor
from pyface.constant import OK, YES, NO
from pyface.file_dialog import FileDialog
from traits.api import List, Instance, Str, Float, Any, Button, Property, HasTraits, Dict, Enum
from traitsui.api import View, Item, TabularEditor, HGroup, UItem, Group, VGroup, \
    HSplit, EnumEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron import json
from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.canvas.utils import load_holder_canvas
from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderHGroup, BorderVGroup
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.strings import SpacelessStr
from pychron.core.utils import alphas, alpha_to_int
from pychron.database.core.defaults import parse_irradiation_tray_map, load_irradiation_map
from pychron.dvc.meta_repo import MetaRepo
from pychron.entry.editors.base_editor import ModelView
from pychron.entry.editors.production import IrradiationProduction
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import FLUX_CONSTANTS


def prep_prname(prname):
    if prname.startswith('Global'):
        prname = '_'.join(prname.split(' ')[1:])
    return prname


class NewProduction(HasTraits):
    name = Str
    reactor = Str

    def traits_view(self):
        v = okcancel_view(HGroup('name', 'reactor'),
                          buttons=['OK', 'Cancel', 'Revert'],
                          title='New Production Ratio')
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
        rgrp = BorderHGroup(UItem('selected_reactor_name',
                                  editor=EnumEditor(name='reactor_names')),
                            icon_button_editor('add_reactor_button', 'add',
                                               tooltip='Add Default Production for the selected '
                                                       'Reactor to this Irradiation level'),
                            icon_button_editor('update_reactor_default_button',
                                               'arrow_up',
                                               tooltip='Set current as the reactor default'),
                            label='Available Default Productions')
        mgrp = BorderVGroup(UItem('selected_monitor'),
                            HGroup(Item('monitor_name'),
                                   Item('monitor_material')),
                            HGroup(Item('monitor_age'),
                                   Item('lambda_k')),
                            label='Monitor')

        pgrp = BorderHGroup(UItem('selected_production_name',
                                  editor=EnumEditor(name='production_names')),
                            icon_button_editor('apply_selected_production', 'arrow_left',
                                               tooltip='Apply selection'),
                            icon_button_editor('add_production_button', 'database_add',
                                               tooltip='Add a Production Ratio'),
                            icon_button_editor('edit_production_button', 'database_edit',
                                               enabled_when='selected_production',
                                               tooltip='Edit Production Ratio'),
                            label='Production'),
        pr_group = VGroup(rgrp,
                          pgrp,
                          UItem('selected_production', style='custom'),
                          label='Production Ratios')

        editor = TabularEditor(adapter=TrayAdapter(),
                               editable=False,
                               selected='selected_tray')
        tray_grp = VGroup(HGroup(icon_button_editor('add_tray_button', 'add',
                                                    tooltip='Add a tray from file')),
                          HSplit(UItem('trays', editor=editor, width=0.25),
                                 UItem('canvas', editor=ComponentEditor(), width=0.75)),
                          label='Tray')

        v = okcancel_view(VGroup(HGroup(Item('name'), Item('z')),
                                 BorderVGroup(UItem('level_note', style='custom'), label='Level Note'),
                                 Group(pr_group,
                                       tray_grp,
                                       mgrp,
                                       layout='tabbed')),
                          width=550,
                          height=650,
                          title=self.title)
        return v


class AddView(EditView):
    title = 'Add Level'


class UpdateReactorView(ModelView):
    def traits_view(self):
        v = okcancel_view(UItem('update_reactor_name',
                                editor=ComboboxEditor(name='update_reactor_names')),
                          width=300,
                          title='Update Reactor Default')
        return v


class LevelEditor(Loggable):
    db = Any

    level_note = Str
    name = SpacelessStr
    selected_tray = Str
    z = Float
    selected_production = Instance(IrradiationProduction, ())
    irradiation = Str

    new_production_name = Str

    productions = Dict
    production_names = List
    selected_production_name = Str

    trays = List

    reactors = Dict
    reactor_names = List
    selected_reactor_name = Str

    canvas = Instance(IrradiationCanvas, ())

    add_production_button = Button
    edit_production_button = Button
    add_tray_button = Button

    apply_selected_reactor = Button
    apply_selected_production = Button

    add_reactor_button = Button
    update_reactor_default_button = Button
    update_reactor_name = Str
    update_reactor_names = List
    meta_repo = Instance(MetaRepo)

    selected_monitor = Enum(list(FLUX_CONSTANTS.keys()))
    monitor_name = Property(depends_on='selected_monitor')
    monitor_age = Property(depends_on='selected_monitor')
    monitor_material = Property(depends_on='selected_monitor')
    lambda_k = Property(depends_on='selected_monitor')

    def edit(self):
        self._load_productions()
        self._edit_level()

    def add(self):
        self._load_productions()
        return self._add_level()

    # private
    def _select_production(self):
        self.selected_production_name = ''
        pname, prod = self.meta_repo.get_production(self.irradiation, self.name)
        self.debug('select production={} for {},{}'.format(pname, self.irradiation, self.name))
        self.selected_production_name = pname

    def _refresh_production(self):
        self.meta_repo.clear_cache = True
        self._load_productions()
        self._select_production()

    def _edit_level(self):

        orignal_name = self.name
        db = self.db
        level = db.get_irradiation_level(self.irradiation, self.name)

        self.z = level.z or 0

        self._select_production()

        original_tray = None
        if level.holder:
            self.selected_tray = next((t for t in self.trays if t == level.holder), '')
            original_tray = self.selected_tray

        if level.note:
            self.level_note = level.note.decode('utf-8')
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

                # save z to meta repo
                self.meta_repo.update_level_z(self.irradiation, self.name, self.z)

                if self.selected_production:
                    self._save_production()
                    prname = self.selected_production.name

                    # pr = db.get_production(prname)
                    # if not pr:
                    #     pr = db.add_production(prname)
                    # level.production = pr

                    self.meta_repo.update_level_production(self.irradiation, self.name, prname, self.level_note)
                if self.selected_monitor:
                    self.meta_repo.update_level_monitor(self.irradiation,
                                                        self.name,
                                                        self.monitor_name, self.monitor_material,
                                                        self.monitor_age,
                                                        self.lambda_k)

                if original_tray != self.selected_tray:
                    self._save_tray(level, original_tray)

                break
            else:
                break

        changes = self.meta_repo.get_local_changes()
        self.debug('changes {}'.format(changes))
        if changes:
            self.meta_repo.smart_pull()
            # self.meta_repo.commit('Edited level {}'.format(self.name))
            # self.meta_repo.push()
            db.commit()

        self._refresh_production()

        return self.name

    def _save_tray(self, level, original_tray):
        self.debug('saving tray {}. original={}, current={}'.format(level.name, original_tray, self.selected_tray))
        db = self.db
        # tr = db.get_irradiation_holder(self.selected_tray)
        # n = len(tuple(iter_geom(tr.geometry)))

        n = len(self.meta_repo.get_irradiation_holder_holes(self.selected_tray))
        on = len(level.positions)
        if n < on:
            if any([p.labnumber.analyses for p in level.positions[n:]]):
                self.warning_dialog('Cannot change tray from "{}" to "{}" '
                                    'This change would orphan irradiation identifiers '
                                    'that have associated analyses'.format(original_tray, self.selected_tray))
            elif self.confirmation_dialog('You are about to orphan {} irradiation identifiers. '
                                          'Are you sure you want to continue?'.format(on - n)):

                level.holder = self.selected_tray
                for p in level.positions[n:]:
                    self.debug('deleting {} {} {} {}'.format(level.irradiation.name,
                                                             level.name,
                                                             p.position,
                                                             p.labnumber.identifier))
                    db.delete_irradiation_position(p)
        else:
            level.holder = self.selected_tray

        print(level, level.holder, self.selected_tray)
        db.commit()

    def _add_level(self):
        irrad = self.irradiation
        db = self.db

        irrad = db.get_irradiation(irrad)
        if irrad.levels:
            level = irrad.levels[-1]

            self.z = level.z or 0

            if level.holder:
                self.selected_tray = next((t for t in self.trays if t == level.holder), '')

            nind = alpha_to_int(level.name) + 1
            self.name = alphas(nind)

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

                    if self._save_level():
                        return self.name
                    else:
                        break
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

    def _load_productions(self, load_reactors=True):
        self.meta_repo.smart_pull()
        root = os.path.join(paths.meta_root, self.irradiation, 'productions')
        ps = {}
        keys = []
        for p in os.listdir(root):
            if p.endswith('.json'):
                with open(os.path.join(root, p)) as rfile:
                    obj = json.load(rfile)
                head, tail = os.path.splitext(p)
                ps[head] = IrradiationProduction(head, obj)
                keys.append(head)

        self.productions = ps
        self.production_names = keys
        if load_reactors:
            self._load_reactors()

    def _load_reactors(self):

        p = os.path.join(paths.meta_root, 'reactors.json')
        reactors = {}
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                reactors = json.load(rfile)
                for k, v in reactors.items():
                    reactors[k] = IrradiationProduction(k, v)

        self.reactors = reactors
        self.reactor_names = list(reactors.keys())

    def _update_reactor(self):
        p = os.path.join(paths.meta_root, 'reactors.json')

        reactors = {}
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                reactors = json.load(rfile)

        self.update_reactor_names = list(reactors.keys())
        v = UpdateReactorView(model=self)

        info = v.edit_traits()
        if info.result:
            pp = os.path.join(paths.meta_root, self.irradiation,
                              'productions', '{}.json'.format(self.selected_production_name))
            with open(pp, 'r') as rfile:
                obj = json.load(rfile)

            with open(p, 'w') as wfile:
                obj['source_path'] = pp
                obj['source_sha'] = self.meta_repo.get_sha(pp)

                reactors[self.update_reactor_name] = obj

                json.dump(reactors, wfile)

            self.meta_repo.add(p, commit=False)
            self.meta_repo.commit('updated reactor default. {}'.format(self.update_reactor_name))

    def _save_level(self):
        # prname = self.new_production_name.replace(' ', '_')
        prname = self.selected_production_name
        # prname = prep_prname(prname)
        if not prname:
            self.warning_dialog('SAVE CANCELED\n\nPlease select a set of Production Ratios for this level.')
            return

        db = self.db
        # add to database
        db.add_irradiation_level(self.name, self.irradiation,
                                 self.selected_tray,
                                 prname,
                                 float(self.z),
                                 self.level_note)

        # add to repository
        self.meta_repo.add_level(self.irradiation, self.name)
        self.meta_repo.update_productions(self.irradiation, self.name, prname)
        self.meta_repo.add_production_to_irradiation(self.irradiation, prname,
                                                     self.selected_production.get_params())

        self.meta_repo.commit('Added level {} to {}'.format(self.name, self.irradiation))

        self._refresh_production()
        return True

    def _save_production(self, name=None):
        prod = self.selected_production
        self.debug('Saving production={}, dirty={}, keywordname={}'.format(prod.name, prod.dirty, name))
        if prod.dirty or name:  # or prod.name.startswith('Global'):
            if name:
                prname = name
            else:
                prname = prod.name

            # prname = prep_prname(prname)
            prod.name = prname

            self.debug('saving production {}'.format(prname))

            self.meta_repo.add_production_to_irradiation(self.irradiation, prname,
                                                         self.selected_production.get_params())
            self.meta_repo.commit('Edited production {} for Irradiation {}'.format(prname, self.irradiation))

    def _add_production_button_fired(self):
        v = okcancel_view(Item('new_production_name', label='Name'), title='New Production')
        info = self.edit_traits(v)
        if info.result:
            self._save_production(name=self.new_production_name)
            self._load_productions()

    def _update_reactor_default_button_fired(self):
        self._update_reactor()

    def _edit_production_button_fired(self):
        self.selected_production.editable = True

    def _apply_selected_production_fired(self):
        if self.selected_production_name:
            o = self.selected_production_name
            self.selected_production_name = ''
            self.selected_production_name = o

    # def _apply_selected_reactor_fired(self):
    #     if self.selected_reactor_name:
    #         o = self.selected_reactor_name
    #         self.selected_reactor_name = ''
    #         self.selected_reactor_name = o

    def _selected_production_name_changed(self, new):
        if new:
            self.selected_production = self.productions[new]

    # def _selected_reactor_name_changed(self, new):
    #     if new:
    #         self.selected_production = self.reactors[new]

    def _add_reactor_button_fired(self):
        if self.selected_reactor_name:
            prod = self.reactors[self.selected_reactor_name]
            self.meta_repo.add_production_to_irradiation(self.irradiation,
                                                         self.selected_reactor_name, prod.get_params())
            self._load_productions(load_reactors=False)

    def _selected_tray_changed(self):
        holes = self.meta_repo.get_irradiation_holder_holes(self.selected_tray)
        if holes:
            load_holder_canvas(self.canvas, holes)

    def _add_tray_button_fired(self):
        dlg = FileDialog(action='open', default_directory=paths.irradiation_tray_maps_dir)
        if dlg.open() == OK:
            if dlg.path:
                # verify this is a valid irradiation map file
                if parse_irradiation_tray_map(dlg.path) is not None:
                    db = self.db
                    load_irradiation_map(db, dlg.path,
                                         os.path.basename(dlg.path), overwrite_geometry=True)

    def _get_monitor_name(self):
        return FLUX_CONSTANTS[self.selected_monitor].get('monitor_name', '')

    def _get_monitor_age(self):
        return FLUX_CONSTANTS[self.selected_monitor].get('monitor_age', 0)

    def _get_monitor_material(self):
        return FLUX_CONSTANTS[self.selected_monitor].get('monitor_material', '')

    def _get_lambda_k(self):
        c = FLUX_CONSTANTS[self.selected_monitor]
        try:
            return c['lambda_ec'][0] + c['lambda_b'][0]
        except KeyError:
            return 0


if __name__ == '__main__':
    paths.build('_dev')
    logging_setup('le')
    from pychron.dvc.dvc_database import DVCDatabase

    dbt = DVCDatabase(kind='sqlite', path='/Users/ross/Programming/test3.sqlite')
    dbt.connect()
    # from pychron.dvc.meta_repo import MetaRepo

    mr = MetaRepo()
    mr.open_repo(paths.meta_root)


    class Demo(HasTraits):
        test = Button
        traits_view = View('test')

        def _test_fired(self):
            e = LevelEditor(db=dbt,
                            meta_repo=mr,
                            irradiation='NM-274',
                            name='H')
            e.edit()


    d = Demo()
    d.configure_traits()
# ============= EOF =============================================
