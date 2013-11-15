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
from traits.api import Str, Int
from traitsui.api import View, Item, Group
# from traitsui.list_str_adapter import ListStrAdapter
from envisage.ui.tasks.preferences_pane import PreferencesPane

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class AutoFigurePreferences(BasePreferencesHelper):
    #name = 'AutoFigure Client'
    preferences_path = 'pychron.auto_figure'
    id = 'pychron.auto_figure.preferences_page'
    #    username = Str

    host = Str
    port = Int


class AutoFigurePreferencesPane(PreferencesPane):
    model_factory = AutoFigurePreferences
    category = 'Processing'

    def traits_view(self):
        server_grp = Group(
            Item('host', width=125, label='Host'),
            Item('port', ),
            show_border=True,
            label='AutoFigure Server'
        )

        return View(server_grp,
        )

#============= EOF =============================================
