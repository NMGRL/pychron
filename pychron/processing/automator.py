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
from traits.api import HasTraits
from traitsui.api import View, Item
from pychron.loggable import Loggable
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
#============= standard library imports ========================
#============= local library imports  ==========================

class Automator(IsotopeDatabaseManager):

    def _import_analyses(self):
        self.debug('importing analyses')

    def _fit_isotopes(self):
        self.debug('fitting isotopes')

    def _blank_fit(self):
        self.debug('blank fitting')

    def _make_tables(self):
        self.debug('make tables')


    def run(self):

        '''
            1. import analyses
                a. by irradiation [, levels]
            2. fit isotope regressions
            
            3. blank fit
            
            4. intercalibration fit
            
            5. make tables
        '''
        self._import_analyses()
        self._fit_isotopes()
        self._blank_fit()
        self._make_tables()

#============= EOF =============================================
