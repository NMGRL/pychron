#===============================================================================
# Copyright 2011 Jake Ross
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
from pyface.action.api import Action

#============= standard library imports ========================

#============= local library imports  ==========================
MDD_PROTOCOL = 'pychron.modeling.modeler_manager.ModelerManager'
class AutoarrAction(Action):
    '''
    '''
    def perform(self, event):
        '''
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.modeler.execute_autoarr()

class AutoagemonAction(Action):
    '''
    '''
    def perform(self, event):
        '''
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.modeler.execute_autoagemon()

class AutoagefreeAction(Action):
    '''
    '''
    def perform(self, event):
        '''
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.modeler.execute_autoagefree()

class ConfidenceIntervalAction(Action):
    '''
    '''
    def perform(self, event):
        '''
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.modeler.execute_confidence_interval()


class CorrelationAction(Action):
    '''
    '''
    def perform(self, event):
        '''
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.modeler.execute_correlation()


class ArrmeAction(Action):
    '''
    '''
    def perform(self, event):
        '''
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.modeler.execute_arrme()


class AgesmeAction(Action):
    '''
    '''
    def perform(self, event):
        '''
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.modeler.execute_agesme()



class ParseAutoupdateAction(Action):
    '''
    '''
    description = 'Parse an autoupdate file'
    name = 'Parse Autoupdate'
    def perform(self, event):
        '''

        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.window = event.window
        manager.parse_autoupdate()

# class AddModelerAction(Action):
#    '''
#    '''
#    description = 'Add another modeler tab'
#    name = 'Add Modeler'
#    def perform(self, event):
#        '''
#        '''
#        app = event.window.application
#        manager = app.get_service(MDD_PROTOCOL)
#        manager.window = event.window
#        manager.add_modeler()

class NewModelAction(Action):
    '''
    '''

    def perform(self, event):
        '''
   
        '''
        app = event.window.application
        manager = app.get_service(MDD_PROTOCOL)
        manager.window = event.window
        manager.new_modeler()




#============= EOF ====================================
