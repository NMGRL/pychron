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
import json
import os

from traits.api import Instance, Dict, List, Str
from traitsui.api import View, Item, UItem, Group, VGroup, HGroup, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.editors.base_editor import ModelView
from pychron.entry.editors.chronology import IrradiationChronology
from pychron.entry.editors.production import IrradiationProduction
from pychron.loggable import Loggable
from pychron.paths import paths


class AddView(ModelView):
    def traits_view(self):
        v = View(VGroup(Item('name'),
                        Group(UItem('chronology', style='custom'),
                              label='Chronology', show_border=True)),
                 HGroup(UItem('selected_reactor_name', editor=EnumEditor(name='reactor_names')),
                        label='Reactor', show_border=True),
                 title='Add Irradiation',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 width=500,
                 resizable=True)
        return v


class EditView(ModelView):
    def traits_view(self):
        v = View(VGroup(Item('name', style='readonly'),
                        Group(UItem('chronology', style='custom'),
                              label='Chronology', show_border=True)),
                 title='Edit Irradiation',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 width=500,
                 resizable=True)
        return v


class IrradiationEditor(Loggable):
    """
        class used to create/edit an irradiation

    """
    chronology = Instance(IrradiationChronology, ())
    dvc = Instance('pychron.dvc.dvc.DVC')

    reactors = Dict
    reactor_names = List
    selected_reactor_name = Str

    def add(self):

        self._load_reactors()

        v = AddView(model=self)
        info = v.edit_traits()

        while 1:
            if info.result:
                name = self.name
                if not name:
                    if self.confirmation_dialog('No name enter. Would you like to enter one?'):
                        info = v.edit_traits()
                        continue
                    else:
                        break

                if not self.dvc.get_irradiation(name):
                    if not self.selected_reactor_name:
                        self.information_dialog('Please select a reactor')
                        info = v.edit_traits()
                        continue

                    self._add_irradiation()
                    return name

                else:
                    if self.confirmation_dialog('Irradiation "{}" already exists. '
                                                'Would you like to try again ?'.format(name)):
                        info = v.edit_traits()
                        continue
                    else:
                        break
            else:
                break

    def edit(self):
        self._load_reactors()

        chronology = self.dvc.get_chronology(self.name)
        self.chronology.set_dosages(chronology.get_doses())
        v = EditView(model=self)
        info = v.edit_traits()
        if info.result:
            self._add_irradiation()
            if self.selected_reactor_name:
                self.dvc.add_production_to_irradiation(self.name, self.reactor.name, self.reactor.get_params())

            self.dvc.update_chronology(self.name, self.chronology.get_doses())

        return self.name

    def _add_irradiation(self):
        self.debug('add irradiation={}'.format(self.name))
        self.dvc.add_irradiation(self.name, self.chronology.get_doses(), verbose=False)
        if self.selected_reactor_name:
            self.dvc.add_production_to_irradiation(self.name, self.reactor.name, self.reactor.get_params())

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

    @property
    def reactor(self):
        return self.reactors[self.selected_reactor_name]

# ============= EOF =============================================
