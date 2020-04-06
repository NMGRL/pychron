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
from traits.api import Instance, Str, HasTraits, List, Any
from traitsui.api import View, Item, TabularEditor, UItem, HGroup
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.pychron_traits import BorderVGroup
from pychron.loggable import Loggable


class EDAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class MSAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Kind', 'kind')]


class Named(HasTraits):
    name = Str

    def __init__(self, record):
        super(Named, self).__init__()
        self.name = record.name


class MS(Named):
    kind = Str

    def __init__(self, record):
        super(MS, self).__init__(record)
        self.kind = record.kind


class ED(Named):
    pass


class NamedEntry(HasTraits):
    name = Str
    items = List
    _klass = None
    selected = Any

    def load(self, dvc):
        self.get_items(dvc)

    def save(self, dvc):
        with dvc.session_ctx():
            inst = self._get_instance(dvc)
            if inst is None:
                self._add(dvc)
            else:
                self._update(inst)
            dvc.commit()

        self.get_items(dvc)

    def get_items(self, dvc):
        with dvc.session_ctx():
            self.items = [self._klass(i) for i in self._get_items(dvc)]

    def _get_items(self, dvc):
        raise NotImplementedError

    def _get_instance(self, dvc):
        raise NotImplementedError

    def _update(self, inst):
        inst.name = self.name

    def _selected_changed(self, new):
        if new:
            self.name = new.name


class MSEntry(NamedEntry):
    kind = Str
    _klass = MS

    def _selected_changed(self, new):
        if new:
            self.name = new.name
            self.kind = new.kind

    def _get_items(self, dvc):
        return dvc.get_mass_spectrometers()

    def _get_instance(self, dvc):
        inst = dvc.get_mass_spectrometer(self.name)
        return inst

    def _update(self, inst):
        inst.name = self.name
        inst.kind = self.kind

    def _add(self, dvc):
        dvc.add_mass_spectrometer(self.name, self.kind)

    def traits_view(self):
        return View(BorderVGroup(HGroup(Item('name'), Item('kind')),
                                 UItem('items', editor=TabularEditor(selected='selected',
                                                                              adapter=MSAdapter())),
                                 label='Mass Spectrometer'))


class EDEntry(NamedEntry):
    _klass = ED

    def _get_items(self, dvc):
        return dvc.get_extraction_devices()

    def _get_instance(self, dvc):
        return dvc.get_extraction_device(self.name)

    def _add(self, dvc):
        dvc.add_extraction_device(self.name)

    def traits_view(self):
        return View(BorderVGroup(HGroup(Item('name')),
                                 UItem('items', editor=TabularEditor(selected='selected',
                                                                     adapter=EDAdapter())),
                                 label='Extract Device'))


class BasicEntryManager(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')
    ms = Instance(MSEntry, ())
    ed = Instance(EDEntry, ())

    def activated(self):
        self.ms.load(self.dvc)
        self.ed.load(self.dvc)

    def prepare_destroy(self):
        pass

    def save(self):
        if self.ms.name:
            self.ms.save(self.dvc)
        else:
            self.info('Skipping Mass Spectrometer')
        if self.ed.name:
            self.ed.save(self.dvc)
        else:
            self.info('Skipping Extract Device')
# ============= EOF =============================================
