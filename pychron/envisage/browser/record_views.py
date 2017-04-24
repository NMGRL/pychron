# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Str, Date, Long, Bool

from pychron.experiment.utilities.identifier import get_analysis_type


class RecordView(object):
    def __init__(self, dbrecord, *args, **kw):
        self._create(dbrecord)
        super(RecordView, self).__init__(*args, **kw)

    def _create(self, *args, **kw):
        pass


class InterpretedAgeRecordView(object):
    name = ''
    identifier = ''
    path = ''

    def __init__(self, idn, path, name):
        self.identifier = idn
        self.name = name
        self.path = path

    @property
    def id(self):
        return self.identifier


class SampleImageRecordView(RecordView):
    name = Str
    record_id = Long
    crete_date = Date

    def _create(self, dbrecord):
        self.name = dbrecord.name
        self.record_id = dbrecord.id
        self.create_date = dbrecord.create_date


class SampleRecordView(RecordView):
    name = ''
    material = ''
    project = ''
    grainsize = ''
    lat = 0
    lon = 0
    elevation = 0
    lithology = ''
    rock_type = ''
    identifier = ''
    principal_investigator = ''
    note = ''
    id = None

    def __str__(self):
        return self.name

    def _create(self, dbrecord):
        self.id = dbrecord.id

        if dbrecord.material:
            self.material = dbrecord.material.name
            self.grainsize = dbrecord.material.grainsize or ''

        if dbrecord.project:
            self.project = dbrecord.project.name
            if dbrecord.project.principal_investigator:
                self.principal_investigator = dbrecord.project.principal_investigator.name

        for attr in ('name', 'lat', ('lon', 'long'),
                     'elevation', 'lithology', 'location', 'igsn', 'rock_type', 'note'):
            if isinstance(attr, tuple):
                attr, dbattr = attr
            else:
                dbattr = attr
            try:
                v = getattr(dbrecord, dbattr)
                if v is not None:
                    setattr(self, attr, v)
            except AttributeError:
                pass


class LabnumberRecordView(RecordView):
    name = ''
    material = ''
    project = ''
    labnumber = ''
    sample = ''

    lat = 0
    lon = 0
    elevation = 0
    lithology = ''

    alt_name = ''
    low_post = None

    irradiation = ''
    irradiation_level = ''
    irradiation_pos = ''

    def _create(self, dbrecord):
        self.labnumber = dbrecord.identifier or ''

        pos = dbrecord
        # pos = dbrecord.irradiation_position
        if pos:
            self.irradiation_pos = str(pos.position)
            level = pos.level
            if level:
                irrad = level.irradiation
                self.irradiation_level = level.name
                if irrad:
                    self.irradiation = irrad.name

        sample = dbrecord.sample
        if sample:
            if sample.material:
                if isinstance(sample.material, (str, unicode)):
                    self.material = sample.material
                else:
                    self.material = sample.material.name
            if sample.project:
                if isinstance(sample.material, (str, unicode)):
                    self.project = sample.project
                else:
                    self.project = sample.project.name

        for attr in ('name', 'lat', ('lon', 'long'),
                     'elevation', 'lithology', 'location', 'igsn'):
            if isinstance(attr, tuple):
                attr, dbattr = attr
            else:
                dbattr = attr
            try:
                v = getattr(sample, dbattr)
                if v is not None:
                    setattr(self, attr, v)
            except AttributeError:
                pass

                # import time
                # for i in range(100):
                #     time.sleep(0.001)

    # def _get_identifier(self):
    #     return self.labnumber

    # def _get_irradiation_and_level(self):
    #     return '{}{}'.format(self.irradiation, self.irradiation_level)
    @property
    def irradiation_and_level(self):
        return '{}{}'.format(self.irradiation, self.irradiation_level)

    # mirror labnumber as identifier
    @property
    def identifier(self):
        return self.labnumber

    @property
    def analysis_type(self):
        return get_analysis_type(self.identifier)

    @property
    def id(self):
        return self.identifier


class NameView(HasTraits):
    name = Str

    @property
    def id(self):
        return self.name


class ProjectRecordView(RecordView, NameView):
    name = Str
    principal_investigator = Str
    lab_contact = Str
    checkin_date = Date
    unique_id = Long

    institution = Str
    comment = Str
    db_comment = Str
    db_name = Str
    dirty = Bool(False)

    def _create(self, dbrecord):
        if not isinstance(dbrecord, str):
            self.name = dbrecord.name
            if dbrecord.principal_investigator:
                self.principal_investigator = dbrecord.principal_investigator.name
            self.unique_id = dbrecord.id
            self.checkin_date = dbrecord.checkin_date
            self.db_comment = self.comment = dbrecord.comment or ''
            self.lab_contact = dbrecord.lab_contact or ''
            self.institution = dbrecord.institution or ''

        else:
            self.name = dbrecord
        self.db_name = self.name


class RepositoryRecordView(NameView):
    principal_investigator = Str


class AnalysisGroupRecordView(RecordView):
    name = Str
    create_date = Date
    last_modified = Date
    id = Long

    def _create(self, dbrecord):
        self.id = dbrecord.id
        for attr in ('name', 'create_date', 'last_modified'):
            setattr(self, attr, getattr(dbrecord, attr))


class AnalysisRecordView(RecordView):
    def _create(self, dbrecord):
        for attr in ('record_id', 'tag'):
            setattr(self, attr, getattr(dbrecord, attr))


class PrincipalInvestigatorRecordView(RecordView, NameView):
    name = ''
    email = ''
    affiliation = ''

    def _create(self, dbrecord):
        self.name = dbrecord.name
        self.email = dbrecord.email
        self.affiliation = dbrecord.affiliation

# ============= EOF =============================================
