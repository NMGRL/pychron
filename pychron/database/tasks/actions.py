## ===============================================================================
## Copyright 2013 Jake Ross
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## ===============================================================================
#
## ============= enthought library imports =======================
#from pyface.action.action import Action
#
## ============= standard library imports ========================
## ============= local library imports  ==========================
##from pychron.database.migrate import manage_database
#from pychron.database.adapters.isotope_adapter import IsotopeAdapter
#from pychron.database.manage_database import build_db, update_db
#
#from traits.api import HasTraits, Any
#from traitsui.api import View, Item
#
#
#class DatabaseConnection(HasTraits):
#    db=Any
#    def trait_context(self):
#        return {'model': self.db}
#
#    def traits_view(self):
#        v=View(Item('name'),
#               Item('host'))
#
#        return v
#
#
#class NewDatabaseAction(Action):
#    name='New Database'
#    description = 'Create a new empty database. Default values will be populated after creation'
#    def perform(self, event):
#        app = event.task.window.application
#        man = app.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
#
#        #get url of database to create
#        db=IsotopeAdapter(name='pychrondata_mb',username='root', password='root', host='localhost')
#        #dc=DatabaseConnection(db=db)
#
#        #url='mysql+pymysql://root:Argon@localhost/isotopedb_new?connect_timeout=3'
#        build_db(db.url)
#        man.populate_default_tables(db)
#        #if dc.edit_traits(kind='modal'):
#        #    build_db(db.url)
#        #    man.populate_default_tables(db)
#
#
#class UpdateDatabaseAction(Action):
#    name = 'Update Database'
#
#    def perform(self, event):
#        app = event.task.window.application
#        man = app.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
#        msg = 'Are you sure use would like to update the database? This is for advanced users only!'
#        if man.confirmation_dialog(msg):
#            url = man.db.url
#
#            #repo = 'isotopedb'
#            progress = man.open_progress()
#
#            update_db()
#            #manage_database(url, repo,
#            #                logger=man.logger,
#            #                progress=progress)
#
#            man.populate_default_tables()
#
#            # ============= EOF =============================================
