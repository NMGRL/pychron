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

import re

import requests
from apptools.preferences.api import PreferencesHelper
from envisage.ui.tasks.preferences_pane import PreferencesPane
# ============= enthought library imports =======================
from traits.api import List, Button, Any, Str, Enum, Color, BaseStr
from traitsui.api import View, VGroup, UItem, HGroup, Item
from traitsui.list_str_adapter import ListStrAdapter

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor


class FavoritesAdapter(ListStrAdapter):
    columns = [('', 'name')]
    can_edit = False

    def get_text(self, obj, tr, ind):
        o = getattr(obj, tr)[ind]
        return o.split(',')[0]


class BasePreferencesHelper(PreferencesHelper):
    pass


REPO_REGEX = re.compile(r'^\w+[\w\-\_]*\/\w+$')


def test_connection_item():
    return icon_button_editor('test_connection', 'server-connect',
                              tooltip='Test connection to Github Repo')


def remote_status_item(label=None):
    grp = HGroup(Item('remote',
                      label='Name', springy=True),
                 test_connection_item(),
                 CustomLabel('_remote_status',
                             width=50,
                             color_name='_remote_status_color'))
    if label:
        grp.label = label
        grp.show_border = True
    return grp


class RepoString(BaseStr):

    def validate(self, obj, name, value):
        if REPO_REGEX.match(value):
            return value
        else:
            self.error(obj, name, value)


class GitRepoPreferencesHelper(BasePreferencesHelper):
    remote = RepoString
    test_connection = Button
    _remote_status = Str
    _remote_status_color = Color

    def _test_connection_fired(self):

        print('fffff', self.remote)
        if self.remote.strip():
            try:
                cmd = 'https://github.com/{}.git'.format(self.remote)
                requests.get(cmd)
                self._remote_status = 'Valid'
                self._remote_status_color = 'green'
                self._connection_hook()
                return
            except BaseException as e:
                print('exception', e, cmd)

        self._remote_status_color = 'red'
        self._remote_status = 'Invalid'

    def _connection_hook(self):
        pass


class FavoritesPreferencesHelper(BasePreferencesHelper):
    favorites = List
    _fav_items = List

    add_favorite = Button('+')
    delete_favorite = Button('-')

    _selected = Any

    def _initialize(self, *args, **kw):
        super(FavoritesPreferencesHelper, self)._initialize(*args, **kw)
        self._fav_items = [self._fav_factory(f) for f in self.favorites]

    def _is_preference_trait(self, trait_name):
        if trait_name in ('favorites_items', '_selected'):
            return False
        else:
            return super(FavoritesPreferencesHelper, self)._is_preference_trait(trait_name)

    def _delete_favorite_fired(self):
        if self._selected in self._fav_items:
            self._fav_items.remove(self._selected)
            self._set_favorites()

    def _fav_factory(self, *args, **kw):
        raise NotImplementedError

    def _add_favorite_fired(self):
        self._fav_items.append(self._fav_factory())
        self._set_favorites()

    def _set_favorites(self):
        self.favorites = [fav.to_string() for fav in self._fav_items]


class BaseConsolePreferences(BasePreferencesHelper):
    fontsize = Enum(6, 8, 10, 11, 12, 14, 16, 18, 22, 24, 36)

    textcolor = Color('green')
    bgcolor = Color('black')

    preview = Str('Pychron is python + geochronology')


class BaseConsolePreferencesPane(PreferencesPane):
    category = 'Console'
    label = ''

    def traits_view(self):
        preview = CustomLabel('preview',
                              size_name='fontsize',
                              color_name='textcolor',
                              bgcolor_name='bgcolor')

        v = View(VGroup(HGroup(UItem('fontsize'),
                               UItem('textcolor'),
                               UItem('bgcolor')),
                        preview,
                        show_border=True,
                        label=self.label))
        return v
# ============= EOF =============================================
