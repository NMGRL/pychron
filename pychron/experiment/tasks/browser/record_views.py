#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Str
#============= standard library imports ========================
#============= local library imports  ==========================


class RecordView(HasTraits):
    def __init__(self, dbrecord, *args, **kw):
        self._create(dbrecord)
        super(RecordView, self).__init__(*args, **kw)

    def _create(self, *args, **kw):
        pass


class SampleRecordView(RecordView):
    name = Str
    material = Str
    project = Str
    labnumber = Str

    def _create(self, dbrecord):
        self.name = dbrecord.name
        if dbrecord.material:
            self.material = dbrecord.material.name
        if dbrecord.project:
            self.project = dbrecord.project.name


class ProjectRecordView(RecordView):
    name = Str

    def _create(self, dbrecord):
        if not isinstance(dbrecord, str):
            self.name = dbrecord.name
        else:
            self.name = dbrecord

            #============= EOF =============================================
