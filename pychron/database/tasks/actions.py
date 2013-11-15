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
from pyface.action.action import Action

#============= standard library imports ========================
#============= local library imports  ==========================


class UpdateDatabaseAction(Action):
    name = 'Update Database'

    def perform(self, event):
        app = event.task.window.application
        man = app.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        msg = 'Are you sure use would like to update the database? This is for advanced users only!'
        if man.confirmation_dialog(msg):
            url = man.db.url

            repo = 'isotopedb'
            from pychron.database.migrate.manage_database import manage_database

            progress = man.open_progress()
            manage_database(url, repo,
                            logger=man.logger,
                            progress=progress)

            man.populate_default_tables()

            #============= EOF =============================================
