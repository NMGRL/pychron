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

from traits.api import provides

# ============= standard library imports ========================
from sqlalchemy import Column, String, Integer, Float, distinct, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.i_browser import IBrowser
from pychron.experiment.utilities.identifier import make_step

Base = declarative_base()


class NoSchemaError(BaseException):
    pass


class DVCIndex(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__

    id = Column(Integer, primary_key=True)
    repo = Column(String(200))


class AnalysisIndex(DVCIndex, Base):
    identifier = Column(String(80))
    aliquot = Column(Integer)
    increment = Column(Integer)
    cleanup = Column(Float)
    duration = Column(Float)
    extract_value = Column(Float)
    uuid = Column(String(36))
    analysis_type = Column(String(40))
    position = Column(String(120))

    measurement_script = Column(String(80))
    extraction_script = Column(String(80))

    mass_spectrometer = Column(String(80))
    extract_device = Column(String(80))

    sample = Column(String(80))
    project = Column(String(80))
    material = Column(String(80))

    irradiation = Column(String(80))
    irradiation_level = Column(String(80))
    irradiation_position = Column(String(80))

    tag = Column(String(80))
    analysis_timestamp = Column(DateTime)

    measurement = None
    extraction = None

    @property
    def labnumber(self):
        return LabnumberRecord(self)

    @property
    def step(self):
        return make_step(self.increment)


class MassSpecRecord(object):
    __slots__ = ['name']

    def __init__(self, name):
        self.name = name


class ProjectRecord(object):
    __slots__ = ['name']

    def __init__(self, name):
        self.name = name


class SampleObject(object):
    def __init__(self, sample, project, material):
        self.material = material
        self.project = project
        self.name = sample


class IrradiationPosObject(object):
    def __init__(self, pos, level):
        self.position = pos
        self.level = level


class LevelObject(object):
    def __init__(self, name, irrad):
        self.name = name
        self.irradiation = irrad


class IrradiationObject(object):
    def __init__(self, name):
        self.name = name


class LabnumberRecord(object):
    def __init__(self, r):
        self.name = r.identifier
        self.labnumber = r.identifier
        self.identifier = r.identifier
        self.sample = SampleObject(r.sample, r.project, r.material)

        irrad = IrradiationObject(r.irradiation)
        level = LevelObject(r.irradiation_level, irrad)
        self.irradiation_position = IrradiationPosObject(r.irradiation_position, level)


def index_factory(path, overwrite=False):
    """
    create a new sqlite db.
    if path not a file or overwrite create all tables
    :param path:
    :param overwrite:
    :return:
    """

    if os.path.isfile(path):
        if overwrite:
            os.remove(path)
    else:
        overwrite = True

    db = IndexAdapter(path=path)
    db.connect()
    if overwrite:
        db.create_all(Base.metadata)
    return db


@provides(IBrowser)
class IndexAdapter(DatabaseAdapter):
    schema = AnalysisIndex
    kind = 'sqlite'

    # irradiations = Property
    # levels = Property(depends_on='irradiation')
    # irradiation = Str
    # level = ''

    # @cached_property
    def get_irradiations(self):
        with self.session_ctx() as sess:
            q = sess.query(distinct(AnalysisIndex.irradiation))
            q = q.order_by(AnalysisIndex.irradiation.asc())
            irs = [v[0] for v in self._query_all(q)]
            return irs

    # @cached_property
    def get_levels(self):
        with self.session_ctx() as sess:
            q = sess.query(distinct(AnalysisIndex.irradiation_level))
            q = q.filter(AnalysisIndex.irradiation == self.irradiation)
            return [v[0] for v in self._query_all(q)]

    # browswer protocol
    def get_analysis_groups(self, *args, **kw):
        return []

    def get_project_labnumbers(self, project_names, filter_non_run, low_post=None, high_post=None,
                               analysis_types=None, mass_spectrometers=None):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisIndex)
            q = q.filter(AnalysisIndex.project.in_(project_names))
            q = q.group_by(AnalysisIndex.identifier)
            qs = self._query_all(q)

            return [LabnumberRecord(qi) for qi in qs]

    def get_labnumber_analyses(self, lns, low_post=None, high_post=None,
                               omit_key=None, exclude_uuids=None, mass_spectrometers=None, **kw):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisIndex)
            q = q.filter(AnalysisIndex.identifier.in_(lns))
            return self._query_all(q), int(q.count())

    def get_projects(self, **kw):
        with self.session_ctx() as sess:
            q = sess.query(distinct(AnalysisIndex.project))
            q = q.order_by(AnalysisIndex.project.asc())

            qs = self._query_all(q)
            return [ProjectRecord(v[0]) for v in qs]

    def get_mass_spectrometers(self):
        with self.session_ctx() as sess:
            q = sess.query(distinct(AnalysisIndex.mass_spectrometer))
            qs = self._query_all(q)
            return [MassSpecRecord(v[0]) for v in qs]

    def get_analysis_types(self):
        return []

    def get_extraction_devices(self):
        return []

    def get_analysis_exists(self, uuid):
        with self.session_ctx() as sess:
            q = sess.query(AnalysisIndex.uuid)
            q = q.filter(AnalysisIndex.uuid == uuid)

            return self._query_one(q) is not None

    def add_analysis_to_index(self, repopath, ai):
        if self.get_analysis_exists(ai.uuid):
            self.info('Analysis already in index: {}'.format(ai.record_id))
            return

        # add to sqlite index
        self.add(repo=repopath,
                 identifier=ai.identifier,
                 aliquot=ai.aliquot,
                 increment=ai.increment,
                 cleanup=ai.cleanup_duration,
                 duration=ai.extract_duration,
                 extract_value=ai.extract_value,
                 uuid=ai.uuid,
                 measurement_script=ai.measurement_script_name,
                 extraction_script=ai.extraction_script_name,
                 mass_spectrometer=ai.mass_spectrometer,
                 extract_device=ai.extract_device,
                 material=ai.material,
                 sample=ai.sample,
                 project=ai.project,
                 irradiation=ai.irradiation,
                 irradiation_level=ai.irradiation_level,
                 irradiation_position=ai.irradiation_position,
                 tag=ai.tag,
                 position=ai.position,
                 analysis_timestamp=ai.rundate,
                 analysis_type=ai.analysis_type)

    def add(self, **kw):
        if self.schema is None:
            raise NoSchemaError()

        with self.session_ctx():
            obj = self.schema(**kw)
            self._add_item(obj)

# ============= EOF =============================================
