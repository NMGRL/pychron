# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Float, List, Dict, Instance
from traitsui.api import View, Item, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.combobox_editor import ComboboxEditor


class MolecularWeight(HasTraits):
    name = Str
    mass = Float

    names = List
    weights = Dict

    def _name_changed(self, name):
        if name in self.names:
            self.mass = self.weights[name]

    def traits_view(self):
        v = View(HGroup(
            Item('name', editor=ComboboxEditor(name='names')),
            Item('mass')),
            width=500, title='Add New Molecular Weight',
            buttons=['OK', 'Cancel'],
            resizable=True)
        return v


class MolecularWeightEditor(HasTraits):
    dvc = Instance('pychron.dvc.dvc.DVC')

    def add_molecular_weight(self):
        dvc = self.dvc
        if not dvc.meta_pull():
            return

        wts = dvc.get_molecular_weights()
        names = wts.keys()

        wt = MolecularWeight(names=names, weights=wts)
        info = wt.edit_traits(kind='livemodal')
        if info.result:
            wts[wt.name] = wt.mass
            dvc.update_molecular_weights(wts, commit=True)
            dvc.meta_push()

# ============= EOF =============================================
