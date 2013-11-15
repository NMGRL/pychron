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
from traits.api import List, Str
from traitsui.api import View, Item

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


class SampleEntry(IsotopeDatabaseManager):
    sample = Str
    material = Str
    materials = List

    def edit_sample(self, sample, project, material):
        db = self.db
        with db.session_ctx():
            dbsam = db.get_sample(sample, project, material)
            if dbsam:
                print dbsam


    def add_sample(self, project):
        while 1:
            info = self.edit_traits()
            if info.result:
                db = self.db
                with db.session_ctx():
                    dbsam = db.get_sample(self.sample, project, self.material)
                    if dbsam is None:
                        db.add_sample(self.sample,
                                      project=project,
                                      material=self.material)
                    else:
                        self.warning('{}, Project={}, Material={} already exists'.format(self.sample,
                                                                                         project,
                                                                                         self.material))
            else:
                break


    def traits_view(self):
        v = View(Item('sample'),
                 kind='modal',
                 resizable=True, title='New Sample')
        return v

        #============= EOF =============================================
