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
from datetime import timedelta

from sqlalchemy.sql.functions import count
from sqlalchemy.util import OrderedSet
from traits.api import HasTraits, Str, List
from traitsui.api import View, Item

# ============= standard library imports ========================
import os
from sqlalchemy import not_, func
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.core.query import compile_query
from pychron.dvc.dvc_orm import AnalysisTbl, ProjectTbl, Base, MassSpectrometerTbl, IrradiationTbl, LevelTbl, SampleTbl, \
    MaterialTbl, IrradiationPositionTbl, UserTbl, ExtractDeviceTbl, LoadTbl, LoadHolderTbl, LoadPositionTbl, \
    MeasuredPositionTbl
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
    """
    mysql2sqlite
    https://gist.github.com/esperlu/943776


    update local database
    when pushing
    1. pull remote database file and merge with local
       a. pull remote to path.remote (rsync remote path.remote)
       b. create merged database at path.merge
       c. rsync path.merge path
    2. push local to remote
       a. rsync lpath remote


    """
    kind = 'sqlite'

    irradiation = Str
    irradiations = List
    level = Str
    levels = List

    def __init__(self, clear=False, auto_add=False, *args, **kw):
        super(DVCDatabase, self).__init__(*args, **kw)

        # self._bind_preferences()
        self.path = paths.meta_db

        # self.synced_path = '{}.sync'.format(paths.meta_db)
        # self.merge_path = '{}.merge'.format(paths.meta_db)
        # self.remote_path = '/var/pychronmeta.sqlite'
        self.connect()

        if clear and os.path.isfile(self.path):
            os.remove(self.path)

        if not os.path.isfile(self.path):
            self.create_all(Base.metadata)
            # else:
            # with self.session_ctx() as sess:
            # print sess
        # Base.metadata.init(sess.bind)

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

    def find_references(self, times, atypes, hours=10):
        with self.session_ctx() as sess:
            # delta = 60 * 60 * hours  # seconds
            delta = timedelta(hours=hours)
            refs = OrderedSet()
            ex = None
            for ti in times:
                low = ti - delta
                high = ti + delta
                rs = self.get_analyses_data_range(low, high, atypes, exclude=ex)
                refs.update(rs)
                ex = [r.idanalysisTbl for r in refs]
                # print rs
                # print ti, low, high, rs, refs
            # print 'refs', refs
            return [ri.record_view() for ri in refs]

    def get_analyses_data_range(self, low, high, atypes, exclude=None):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.filter(AnalysisTbl.timestamp >= low.strftime('%Y-%m-%d %H:%M:%S'))
            q = q.filter(AnalysisTbl.timestamp <= high.strftime('%Y-%m-%d %H:%M:%S'))

            if isinstance(atypes, (list, tuple)):
                if len(atypes) == 1:
                    atypes = atypes[0]

            if not isinstance(atypes, (list, tuple)):
                q = q.filter(AnalysisTbl.analysis_type == atypes)
            else:
                q = q.filter(AnalysisTbl.analysis_type.in_(atypes))

            if exclude:
                q = q.filter(not_(AnalysisTbl.idanalysisTbl.in_(exclude)))
            return self._query_all(q, verbose_query=False)

    def get_production_name(self, irrad, level):
        with self.session_ctx() as sess:
            dblevel = self.get_irradiation_level(irrad, level)
            # print dblevel, dblevel.productionID, dblevel.production, dblevel.idlevelTbl
            return dblevel.production.name

    def add_measured_position(self, position=None, load=None, **kw):
        a = MeasuredPositionTbl(**kw)
        if position:
            a.position = position
        if load:
            a.loadName = load
        return self._add_item(a)

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
        # self.debug('ADDING SAMPLE {},{},{}'.format(name,project,material))
        a = self.get_sample(name, project)
        if a is None:
            a = SampleTbl(name=name)
            a.project = self.get_project(project)
            a.material = self.get_material(material)
            a = self._add_item(a)
        # else:
        # self.debug('SAMPLE {},{} ALREADY EXISTS'.format(name,project))
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

    # special getters
    def get_labnumber_analyses(self, lns,
                               low_post=None, high_post=None,
                               omit_key=None, exclude_uuids=None,
                               mass_spectrometers=None, **kw):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl)
            q = q.join(IrradiationPositionTbl)

            if not hasattr(lns, '__iter__'):
                lns = (lns,)
            q = q.filter(IrradiationPositionTbl.identifier.in_(lns))

            if low_post:
                q = q.filter(AnalysisTbl.timestamp >= str(low_post))

            if high_post:
                q = q.filter(AnalysisTbl.timestamp <= str(high_post))

            if omit_key:
                q = q.filter(AnalysisTbl.tag != omit_key)

            if exclude_uuids:
                q = q.filter(not_(AnalysisTbl.uuid.in_(exclude_uuids)))

            if mass_spectrometers:
                if not hasattr(mass_spectrometers, '__iter__'):
                    mass_spectrometers = (mass_spectrometers,)
                q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
            tc = q.count()
            return self._query_all(q), tc

    def get_project_date_range(self, names):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisTbl.timestamp)
            q = q.join(IrradiationPositionTbl, SampleTbl, ProjectTbl)
            if names:
                q = q.filter(ProjectTbl.name.in_(names))

            asc = AnalysisTbl.timestamp.asc()
            desc = AnalysisTbl.timestamp.desc()
            return self._get_date_range(q, asc, desc)

    def get_project_labnumbers(self, project_names, filter_non_run, low_post=None, high_post=None,
                               analysis_types=None, mass_spectrometers=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTbl)
            q = q.join(SampleTbl, ProjectTbl)
            # filter_non_run = False
            if filter_non_run:
                if mass_spectrometers or analysis_types or low_post or high_post:
                    q = q.join(AnalysisTbl)

                if mass_spectrometers:
                    if not hasattr(mass_spectrometers, '__iter__'):
                        mass_spectrometers = (mass_spectrometers,)
                    q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))

                if analysis_types:
                    q = q.filter(AnalysisTbl.analysistype.in_(analysis_types))
                    project_names.append('references')

                q = q.group_by(IrradiationPositionTbl.identifier)
                q = q.having(count(AnalysisTbl.idanalysisTbl) > 0)
                if low_post:
                    q = q.filter(AnalysisTbl.timestamp >= str(low_post))
                if high_post:
                    q = q.filter(AnalysisTbl.timestamp <= str(high_post))

            if project_names:
                q = q.filter(ProjectTbl.name.in_(project_names))

            self.debug(compile_query(q))
            return self._query_all(q)

    def get_analysis_groups(self, **kw):
        return []

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

            project = self.get_project(project)

            q = q.filter(SampleTbl.project == project)
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

    def get_irradiations(self, names=None, order_func='desc',
                         project_names=None,
                         mass_spectrometers=None, **kw):

        if names is not None:
            if hasattr(names, '__call__'):
                f = names(IrradiationTbl)
            else:
                f = (IrradiationTbl.name.in_(names),)
            kw = self._append_filters(f, kw)
        if project_names:
            kw = self._append_filters(ProjectTbl.name.in_(project_names), kw)
            kw = self._append_joins((LevelTbl, IrradiationPositionTbl, SampleTbl), kw)

        if mass_spectrometers:
            kw = self._append_filters(AnalysisTbl.mass_spectrometer.name.in_(mass_spectrometers), kw)
            kw = self._append_joins(LevelTbl, IrradiationPositionTbl, AnalysisTbl, kw)

        order = None
        if order_func:
            order = getattr(IrradiationTbl.name, order_func)()

        return self._retrieve_items(IrradiationTbl, order=order, **kw)

    def get_projects(self, irradiation=None, level=None, mass_spectrometers=None, order=None):

        if order:
            order = getattr(ProjectTbl.name, order)()

        if irradiation or mass_spectrometers:
            with self.session_ctx() as sess:
                q = sess.query(ProjectTbl)
                q = q.join(SampleTbl, IrradiationPositionTbl)
                if irradiation:
                    q = q.join(LevelTbl, IrradiationPositionTbl)
                    q = q.filter(LevelTbl.name == level)
                    q = q.filter(IrradiationTbl.name == irradiation)

                else:
                    if not hasattr(mass_spectrometers, '__iter__'):
                        mass_spectrometers = (mass_spectrometers,)

                    q = q.join(AnalysisTbl)

                    q = q.filter(AnalysisTbl.mass_spectrometer.in_(mass_spectrometers))
                    if order:
                        q = q.order_by(order)
                ps = self._query_all(q)
        else:
            ps = self._retrieve_items(ProjectTbl, order=order)
        return ps

    def get_mass_spectrometers(self):
        return self._retrieve_items(MassSpectrometerTbl)

        # private

# ============= EOF =============================================
