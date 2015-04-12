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

from sqlalchemy import not_, func
from traits.api import HasTraits, Str, List
from traitsui.api import View, Item


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.dvc.dvc_orm import AnalysisTbl, ProjectTbl, Base, MassSpectrometerTbl, IrradiationTbl, LevelTbl, SampleTbl, \
    MaterialTbl, IrradiationPositionTbl, UserTbl, ExtractDeviceTbl, LoadTbl, LoadHolderTbl, LoadPositionTbl
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

    def __init__(self, clear=False, auto_add=False, *args, **kw):
        super(DVCDatabase, self).__init__(*args, **kw)

        self.path = paths.meta_db
        self.connect()

        if clear and os.path.isfile(self.path):
            os.remove(self.path)

        if not os.path.isfile(self.path):
            self.create_all(Base.metadata)

        with self.session_ctx():
            if not self.get_mass_spectrometers():
                if auto_add:
                    self.add_mass_spectrometer('Jan', 'ArgusVI')
                else:
                    while 1:
                        self.information_dialog('No Mass spectrometer in the database. Add one now')
                        nv = NewMassSpectrometerView(name='Jan', kind='ArgusVI')
                        info = nv.edit_traits()
                        if info.result:
                            self.add_mass_spectrometer(nv.name, nv.kind)
                            break

            if not self.get_users():
                self.add_user('root')

    def add_load_holder(self, name):
        a = LoadHolderTbl(name=name)
        return self._add_item(a)

    def add_load(self, name, holder):
        a = LoadTbl(name=name, holderName=holder)
        return self._add_item(a)

    def add_user(self, name, **kw):
        a = UserTbl(name=name, **kw)
        return self._add_item(a)

    def add_analysis(self, **kw):
        a = AnalysisTbl(**kw)
        return self._add_item(a)

    def add_material(self, name):
        a = self.get_material(name)
        if a is None:
            a = MaterialTbl(name=name)
            a = self._add_item(a)
        return a

    def add_sample(self, name, project, material):
        a = self.get_sample(name, project)
        if a is None:
            a = SampleTbl(name=name)
            a.project = self.get_project(project)
            a.material = self.get_material(material)
            a = self._add_item(a)
        return a

    def add_mass_spectrometer(self, name, kind):
        a = MassSpectrometerTbl(name=name, kind=kind)
        return self._add_item(a)

    def add_irradiation(self, name):
        a = IrradiationTbl(name=name)
        return self._add_item(a)

    def add_irradiation_level(self, name, irradiation, holder, z=0, note=''):
        irradiation = self.get_irradiation(irradiation)
        a = LevelTbl(name=name,
                     irradiation=irradiation,
                     holder=holder,
                     z=z,
                     note=note)

        return self._add_item(a)

    def add_project(self, name):
        a = self.get_project(name)
        if a is None:
            a = ProjectTbl(name=name)
            a = self._add_item(a)
        return a

    def add_irradiation_position(self, irrad, level, pos):
        a = IrradiationPositionTbl(position=pos)
        a.level = self.get_irradiation_level(irrad, level)
        return self._add_item(a)

    def add_load_position(self, ln, position, weight=0, note=''):
        a = LoadPositionTbl(identifier=ln, position=position, weight=weight, note=note)
        return self._add_item(a)

    # single getters
    def get_loadtable(self, name=None):
        if name is not None:
            lt = self._retrieve_item(LoadTbl, name)
        else:
            with self.session_ctx() as s:
                q = s.query(LoadTbl)
                q = q.order_by(LoadTbl.create_date.desc())
                lt = self._query_first(q)

        return lt

    def get_identifier(self, identifier):
        return self._retrieve_item(IrradiationPositionTbl, identifier, key='identifier')

    def get_irradiation_position(self, irrad, level, pos):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            q = q.join(LevelTbl, IrradiationTbl)
            q = q.filter(IrradiationTbl.name == irrad)
            q = q.filter(LevelTbl.name == level)
            q = q.filter(IrradiationPositionTbl.position == pos)

        return self._query_one(q)

    def get_project(self, name):
        return self._retrieve_item(ProjectTbl, name)

    def get_irradiation_level(self, irrad, name):
        with self.session_ctx() as sess:
            irrad = self.get_irradiation(irrad)
            if irrad:
                q = sess.query(LevelTbl)
                q = q.filter(LevelTbl.irradiationID == irrad.idirradiationTbl)
                q = q.filter(LevelTbl.name == name)
                return self._query_one(q)

    def get_irradiation(self, name):
        return self._retrieve_item(IrradiationTbl, name)

    def get_material(self, name):
        return self._retrieve_item(MaterialTbl, name)

    def get_sample(self, name, project):
        with self.session_ctx() as sess:
            q = sess.query(SampleTbl)
            q = q.join(ProjectTbl)
            q = q.filter(ProjectTbl.name == project)
            q = q.filter(SampleTbl.name == name)

            return self._query_one(q)

    def get_last_identifier(self, sample=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            if sample:
                q = q.join(SampleTbl)
                q = q.filter(SampleTbl.name == sample)

            q = q.order_by(func.abs(IrradiationPositionTbl.identifier).desc())
            return self._query_first(q)

    def get_latest_load(self):
        return self._retrieve_first(LoadTbl, order_by=LoadTbl.create_date.desc())

    # multi getters
    def get_load_holders(self):
        with self.session_ctx():
            return [ni.name for ni in self._retrieve_items(LoadHolderTbl)]

    def get_last_identifiers(self, sample=None, limit=1000, excludes=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            if sample:
                q = q.join(SampleTbl)
                q = q.filter(SampleTbl.name == sample)
                if excludes:
                    q = q.filter(not_(SampleTbl.name.in_(excludes)))
            elif excludes:
                q = q.join(SampleTbl)
                q = q.filter(not_(SampleTbl.name.in_(excludes)))
            q = q.filter(IrradiationPositionTbl.identifier.isnot(None))
            q = q.order_by(func.abs(IrradiationPositionTbl.identifier).desc())
            q = q.limit(limit)
            return [ni.identifier for ni in self._query_all(q, verbose_query=True)]

    def get_loads(self):
        with self.session_ctx():
            loads = self._retrieve_items(LoadTbl)
            return [ui.name for ui in loads]

    def get_extraction_devices(self):
        with self.session_ctx():
            eds = self._retrieve_items(ExtractDeviceTbl)
            return [ui.name for ui in eds]

    def get_users(self):
        with self.session_ctx():
            users = self._retrieve_items(UserTbl)
            return [ui.name for ui in users]

    def get_material_names(self):
        with self.session_ctx():
            names = self._retrieve_items(MaterialTbl)
            return [ni.name for ni in names]

    def get_samples(self, project=None, **kw):
        if project:
            if hasattr(project, '__iter__'):
                kw = self._append_filters(ProjectTbl.name.in_(project), kw)
            else:
                kw = self._append_filters(ProjectTbl.name == project, kw)
            kw = self._append_joins(ProjectTbl, kw)
        return self._retrieve_items(SampleTbl, verbose_query=False, **kw)

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



