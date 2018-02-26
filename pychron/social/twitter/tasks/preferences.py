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
from __future__ import absolute_import
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Int, Bool, File, List
from traitsui.api import View, Item, VGroup, EnumEditor

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.social.google_calendar.client import GoogleCalendarClient


class TwitterPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.twitter'
    consumer_key = Str
    consumer_secret = Str
    access_token_key = Str
    access_token_secret = Str

    def __init__(self, *args, **kw):
        super(TwitterPreferences, self).__init__(*args, **kw)
    #
    # def _update_names(self):
    #     c = TwitterClient()


class TwitterPreferencesPane(PreferencesPane):
    category = 'Twitter'
    model_factory = TwitterPreferences

    def traits_view(self):
        v = View(VGroup(Item('consumer_key'),
                        Item('consumer_secret'),
                        Item('access_token_key'),
                        Item('access_token_secret')))
        return v


class TwitterExperimentPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.twitter.experiment'
    enabled = Bool


class TwitterExperimentPreferencesPane(PreferencesPane):
    category = 'Experiment'
    model_factory = TwitterExperimentPreferences

    def traits_view(self):
        v = View(VGroup(Item('enabled', label='Enabled', tooltip='Post experiment events to Twitter')))
        return v

# ============= EOF =============================================
