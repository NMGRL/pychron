# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import HasTraits, Str, List
from traitsui.api import View, Item

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.dvc.dvc_orm import AnalysisTbl, ProjectTbl, Base, MassSpectrometerTbl, IrradiationTbl, LevelTbl
from pychron.paths import paths


class NewMassSpectrometerView(HasTraits):
    name = Str
    kind = Str

    def traits_view(self):
        v = View(Item('name'),
                 Item('kind'),
                 buttons=['OK', 'Cancel'],
                 title='New Mass Spectrometer',
                 kind='livemodal')
        return v


class DVCDatabase(DatabaseAdapter):
    kind = 'sqlite'

    irradiation = Str
    irradiations = List
    level = Str
    levels = List

    def __init__(self, *args, **kw):
        super(DVCDatabase, self).__init__(*args, **kw)

        self.path = paths.meta_db
        self.connect()

        if not os.path.isfile(self.path):
            self.create_all(Base.metadata)

        with self.session_ctx():
            if not self.get_mass_spectrometers():
                while 1:
                    self.information_dialog('No Mass spectrometer in the database. Add one now')
                    nv = NewMassSpectrometerView()
                    info = nv.edit_traits()
                    if info.result:
                        self.add_mass_spectrometer(nv.name, nv.kind)
                        break

    def add_analysis(self, **kw):
        a = AnalysisTbl(**kw)
        return self._add_item(a)

    def add_mass_spectrometer(self, name, kind):
        a = MassSpectrometerTbl(name=name, kind=kind)
        return self._add_item(a)

    def add_irradiation(self, name):
        a = IrradiationTbl(name=name)
        return self._add_item(a)

    def add_irradiation_level(self, name, irradiation, holder, z):
        irradiation = self.get_irradiation(irradiation)
        a = LevelTbl(name=name,
                     irradiation=irradiation,
                     holder=holder,
                     z=z)

        return self._add_item(a)

    # single getters
    def get_irradiation_level(self, irrad, name):
        with self.session_ctx() as sess:
            irrad = self.get_irradiation(irrad)
            q = sess.query(LevelTbl)
            q.filter(LevelTbl.irradiationID == irrad.idirradiationTbl)
            q.filter(LevelTbl.name == name)
            return self._query_one(q)

    def get_irradiation(self, name):
        return self._retrieve_item(IrradiationTbl, name)

    # multi getters
    def get_irradiations(self, names=None, **kw):

        if names is not None:
            if hasattr(names, '__call__'):
                f = names(IrradiationTbl)
            else:
                f = (IrradiationTbl.name.in_(names),)
            kw = self._append_filters(f, kw)

        return self._retrieve_items(IrradiationTbl, **kw)

    def get_projects(self, order=None):
        if order == 'asc':
            order = ProjectTbl.name.asc()
        elif order == 'desc':
            order = ProjectTbl.name.desc()

        return self._retrieve_items(ProjectTbl, order=order)

    def get_mass_spectrometers(self):
        return self._retrieve_items(MassSpectrometerTbl)

# ============= EOF =============================================



