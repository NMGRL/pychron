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
from traits.api import HasTraits, Str, Float, List, Dict
from traitsui.api import View, Item, HGroup, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


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
            Item('name', editor=EnumEditor(name='names')),
            Item('name', show_label=False),
            Item('mass')),
                 width=500, title='Add New Molecular Weight',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


class MolecularWeightEditor(IsotopeDatabaseManager):
    def add_molecular_weight(self):
        db = self.db
        with db.session_ctx():
            wts = db.get_molecular_weights()
            names = [wi.name for wi in wts]
            weights = dict([(wi.name, wi.mass) for wi in wts])

        wt = MolecularWeight(names=names, weights=weights)
        info = wt.edit_traits(kind='livemodal')
        if info.result:
            with db.session_ctx():
                dbwt = db.get_molecular_weight(wt.name)
                if dbwt is None:
                    db.add_molecular_weight(wt.name, wt.mass)
                else:
                    dbwt.mass = wt.mass


# ============= EOF =============================================

