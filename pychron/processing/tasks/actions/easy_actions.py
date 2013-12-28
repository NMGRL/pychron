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
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================

#============= local library imports  ==========================


#============= EOF ====================================
class EasyFitAction(TaskAction):
    method = 'do_easy_fit'
    name = 'Easy Fit'


class EasyBlanksAction(TaskAction):
    method = 'do_easy_blanks'
    name = 'Easy Blanks'


class EasyDiscriminationAction(TaskAction):
    method = 'do_easy_discrimination'
    name = 'Easy Disc.'


class EasyICAction(TaskAction):
    method = 'do_easy_ic'
    name = 'Easy Disc.'


class EasyFiguresAction(Action):
    name = 'Easy Figures'

    def perform(self, event):
        from pychron.processing.easy.figures import EasyFigures

        e = EasyFigures()
        e.make_figures()


class EasyTablesAction(Action):
    name = 'Easy Tables'

    def perform(self, event):
        from pychron.processing.easy.tables import EasyTables

        e = EasyTables()
        e.make_tables()

