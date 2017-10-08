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

from traits.api import HasTraits, Bool, Instance
from traitsui.api import View, Item

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.xls.xls_parser import XLSParser
from pychron.loggable import Loggable


class XLSSampleLoaderOption(HasTraits):
    dry = Bool(False)

    def traits_view(self):
        v = View(Item('dry'),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v


class XLSSampleLoader(Loggable):
    options = Instance(XLSSampleLoaderOption, ())

    def do_loading(self, manager, db, path, dry=True, use_progress=True, quiet=False):
        if not quiet:
            option = self.options
            info = option.edit_traits()
            if not info.result:
                return

            dry = option.dry

        if not os.path.isfile(path):
            self.warning('No file located at {}'.format(path))

        xp = XLSParser()
        xp.load(path)

        add_samples = True

        if manager and use_progress:
            db = manager.db
            progress = manager.open_progress(xp.nrows)
            progress.position = (100,100)

        added_projects = []
        added_materials = []
        keys = ('sample', 'project', 'material')
        for args in xp.itervalues(keys=keys):
            sample, project, material = args['sample'], args['project'], args['material']

            # check if project exists
            if project not in added_projects:
                dbproject = db.get_project(project)
                if not dbproject:
                    if quiet or self.confirmation_dialog('"{}" does not exist. Add to database?'.format(project)):
                        added_projects.append(project)
                        db.add_project(project)
                    else:
                        continue

            # check if material exists
            if material not in added_materials:
                dbmaterial = db.get_material(material)
                if not dbmaterial:
                    if quiet or self.confirmation_dialog('"{}" does not exist. Add to database?'.format(material)):
                        added_materials.append(material)
                        db.add_material(material)
                    else:
                        continue

            if use_progress:
                progress.change_message('Setting sample {}'.format(sample))

            dbsample = db.get_sample(sample, project, material, verbose=False)
            if not dbsample:
                if add_samples:
                    # print 'trying to add sample {} {} {}'.format(sample,project, material)
                    dbsample = db.add_sample(sample, project, material)
            db.commit()

        if use_progress:
            progress.close()

# ============= EOF =============================================



