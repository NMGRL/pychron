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
from traitsui.api import Item, UItem, VGroup, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.core.ui.strings import SpacelessStr
from pychron.entry.editors.base_editor import ModelView
from pychron.entry.editors.chronology import IrradiationChronology
from pychron.entry.editors.production import IrradiationProduction
from pychron.loggable import Loggable
from pychron.paths import paths


class IrradiationAddView(ModelView):
    def traits_view(self):
        v = okcancel_view(VGroup(VGroup(Item('name'),
                                        BorderVGroup(UItem('chronology', style='custom'),
                                                     label='Chronology')),
                                 BorderHGroup(UItem('selected_reactor_name', editor=EnumEditor(name='reactor_names')),
                                              label='Reactor')),
                          title='Add Package',
                          width=500)
        return v


class IrradiationEditView(ModelView):
    def traits_view(self):
        v = okcancel_view(VGroup(Item('name', style='readonly'),
                                 BorderVGroup(UItem('chronology', style='custom'),
                                              label='Chronology')),
                          title='Edit Irradiation',
                          width=500)
        return v


class PackageAddView(ModelView):
    def traits_view(self):
        v = okcancel_view(Item('name'),
                          title='Add Package',
                          width=500)
        return v


class PackageEditView(ModelView):
    def traits_view(self):
        v = okcancel_view(Item('name', style='readonly'),
                          title='Edit Irradiation',
                          width=500)
        return v


class PackageEditor(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')
    name = SpacelessStr
    tagname = 'Package'
    _add_view_klass = PackageAddView
    _edit_view_klass = PackageEditView

    def _pre_add_hook(self):
        pass

    def _add_hook(self, v):
        pass

    def add(self):
        self._pre_add_hook()

        v = self._add_view_klass(model=self)
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
                    info = self._add_hook(v)
                    if info:
                        continue

                    self._add_package()
                    return name

                else:
                    if self.confirmation_dialog('{} "{}" already exists. '
                                                'Would you like to try again ?'.format(self.tagname, name)):
                        info = v.edit_traits()
                        continue
                    else:
                        break
            else:
                break

    def edit(self):
        v = self._edit_view_klass(model=self)
        info = v.edit_traits()
        if info.result:
            self._add_package()

        return self.name

    def _add_package(self):
        self.debug('add package={}'.format(self.name))
        self.dvc.add_irradiation(self.name, [], verbose=False)
        self.dvc.add_production_to_irradiation(self.name, 'NoReactor', {})


class IrradiationEditor(PackageEditor):
    """
        class used to create/edit an irradiation

    """
    _add_view_klass = IrradiationAddView
    _edit_view_klass = IrradiationEditView

    chronology = Instance(IrradiationChronology, ())

    reactors = Dict
    reactor_names = List
    selected_reactor_name = Str
    tagname = 'Irradiation'

    def _pre_add_hook(self):
        self._load_reactors()

    def _add_hook(self, v):
        if not self.selected_reactor_name:
            self.information_dialog('Please select a reactor')
            info = v.edit_traits()
            return info

    def edit(self):
        self._load_reactors()

        chronology = self.dvc.get_chronology(self.name)
        self.chronology.set_dosages(chronology.get_doses())
        v = self._edit_view_klass(model=self)
        info = v.edit_traits()
        if info.result:
            self.debug('add irradiation={}'.format(self.name))
            self.dvc.add_irradiation(self.name, self.chronology.get_doses(), verbose=False)
            if self.selected_reactor_name:
                self.dvc.add_production_to_irradiation(self.name, self.reactor.name, self.reactor.get_params())

            self.dvc.update_chronology(self.name, self.chronology.get_doses())

        return self.name

    # def _add_irradiation(self):
    #    self.debug('add irradiation={}'.format(self.name))
    #    self.dvc.add_irradiation(self.name, self.chronology.get_doses(), verbose=False)
    #    if self.selected_reactor_name:
    #        self.dvc.add_production_to_irradiation(self.name, self.reactor.name, self.reactor.get_params())

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
