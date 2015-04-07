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
from pyface.tasks.action.task_action import TaskAction

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon


class ResetEditorsAction(TaskAction):
    method = 'reset_editors'
    name = 'Reset Editors'
    image = icon('arrow_refresh')


class ClearFigureAction(TaskAction):
    name = 'Clear Figure'
    method = 'clear_figure'
    image = icon('clear')


class AddSystemMonitorAction(TaskAction):
    name = 'New Monitor'
    method = 'add_system_monitor'
    image = icon('add')


class PauseAction(TaskAction):
    name = 'Pause'
    method = 'toggle_pause'
    image = icon('control_pause_blue')
    visible_name = 'pause_visible'


class PlayAction(TaskAction):
    name = 'Play'
    method = 'toggle_pause'
    image = icon('control_play_blue')
    visible_name = 'play_visible'

# ============= EOF =============================================
