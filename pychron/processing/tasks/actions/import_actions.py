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


class EasyImportAction(Action):
    name = 'Easy Import'

    def perform(self, event):
        from pychron.experiment.importer.easy_import import EasyImporter

        em = EasyImporter()
        em.do_import()


#============= EOF ====================================
