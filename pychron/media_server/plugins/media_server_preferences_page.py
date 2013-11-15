#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Bool, Str, Int, Directory
from traitsui.api import View, Item, VGroup
from apptools.preferences.ui.preferences_page import PreferencesPage
#============= standard library imports ========================
#============= local library imports  ==========================

class MediaServerPreferencesPage(PreferencesPage):
    use_media_server = Bool
    host = Str
    port = Int

    auto_upload = Bool
    use_cache = Bool
    cache_dir = Directory
#    category = 'Data'
    name = 'Media Server'
    id = 'pychron.media_server.preferences'
    preferences_path = 'pychron.media_server'


    def traits_view(self):
        config_group = VGroup(Item('host'),
                              Item('port'),
                              enabled_when='use_media_server',
                              show_border=True,
                              label='Connection'
                            )
        cache_grp = VGroup(Item('cache_dir',
                                label='Directory'),
                           label='Cache',
                           show_border=True
                           )
        v = View(Item('use_media_server'),
                 config_group,
                 Item('use_cache'),
                 cache_grp,
                 Item('auto_upload',
                      tooltip='Should snapshots and videos be automatically uploaded to the media server?'
                      )

                 )
        return v
#============= EOF =============================================
