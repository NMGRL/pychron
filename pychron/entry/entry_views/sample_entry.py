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
from traits.api import List, Str
from traitsui.api import Item, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
# from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.entry.entry_views.entry import BaseEntry


class SampleEntry(BaseEntry):
    sample = Str
    material = Str
    materials = List
    project = Str
    projects = List

    # def edit_sample(self, sample, project, material):
    #     db = self.db
    #     with db.session_ctx():
    #         dbsam = db.get_sample(sample, project, material)
    #         if dbsam:
    #             print 'fffff', dbsam

    def _add_item(self):
        dvc = self.dvc
        project = self.project
        sample = self.sample
        material = self.material
        self.info('Attempting to add Sample="{}", '
                  'Project="{}", Material="{}"'.format(sample, project, material))

        dbsam = dvc.get_sample(sample, project)
        if dbsam is None:
            dvc.add_sample(sample, project, material)
            return True
        else:
            self.warning('{}, Project={}, Material={} already exists'.format(sample,
                                                                             project,
                                                                             material))

    def traits_view(self):
        v = self._new_view(Item('sample'),
                           Item('project', editor=EnumEditor(name='projects')),
                           Item('material', editor=EnumEditor(name='materials')),
                           title='New Sample')
        return v

# ============= EOF =============================================
