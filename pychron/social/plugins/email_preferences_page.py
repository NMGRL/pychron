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



# from __future__ import with_statement
#============= enthought library imports =======================
from traits.api import Str, Password
from traitsui.api import  View
from apptools.preferences.ui.api import PreferencesPage

#============= standard library imports ========================

#============= local library imports  ==========================

class EmailPreferencesPage(PreferencesPage):
    name = 'Email'
    preferences_path = 'pychron.email'
    smtp_host = Str
    username = Str
    password = Password
    def traits_view(self):
        return View('smtp_host',
                    'username',
                    'password'
                    )

#    def traits_view(self):
#        '''
#        '''
#        v = View(grp,
#                 hardware_grp
#                 )
#        return v
#============= views ===================================
#============= EOF ====================================
