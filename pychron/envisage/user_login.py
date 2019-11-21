# ===============================================================================
# Copyright 2014 Jake Ross
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

import os
import pickle

from pyface.constant import OK
from pyface.directory_dialog import DirectoryDialog
from traits.api import HasTraits, List, Str, Bool, Button
from traitsui.api import HGroup, UItem, Label, Handler, EnumEditor

from pychron.core.helpers.strtools import to_bool
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths, users_file, environments_file


class LoginHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            info.object.dump()
        return True


def load_user_file():
    users = []
    last_login = ''
    path = users_file
    isfile = False
    if os.path.isfile(path):
        isfile = True
        with open(path, 'rb') as rfile:
            try:
                users, last_login = pickle.load(rfile)
            except (UnicodeDecodeError, EOFError, ValueError):
                pass

    # return users, last_login, isfile
    return last_login, users, isfile


def load_environments_file():
    path = environments_file
    envs = []
    last_env = ''
    if os.path.isfile(path):
        with open(path, 'rb') as rfile:
            try:
                last_env, envs = pickle.load(rfile)
            except (UnicodeDecodeError, EOFError, ValueError):
                pass
    return last_env, envs


def dump_environments_file(env, envs):
    path = environments_file
    with open(path, 'wb') as wfile:
        pickle.dump((env, envs), wfile)


def dump_user_file(names, last_login=None):
    if last_login is None:
        from pychron.globals import globalv
        last_login = globalv.username

    if names is None:
        _, names, _ = load_user_file()

    if not isinstance(names, list):
        names = [names, ]

    names = [ni for ni in names if ni and ni.strip()]

    with open(users_file, 'wb') as wfile:
        pickle.dump((names, last_login), wfile)


class Login(HasTraits):
    users = List
    user = Str
    user_enabled = Bool(True)

    environment = Str
    environments = List
    directory_select_button = Button
    message = Str
    user_help = 'Select your username or enter a new one'

    def __init__(self, *args, **kw):
        super(Login, self).__init__(*args, **kw)
        self.environment, self.environments = load_environments_file()
        self.user, self.users, isfile = load_user_file()
        if not isfile or not self.users:
            self.user = 'root'
            self.user_enabled = False
            if os.environ.get('PYCHRON_APPNAME') in ('pyexperiment', 'pyview'):
                self.message = 'Auto Login as "root". Quit Pychron to populate users from database'

    def dump(self):
        dump_user_file(self.users, self.user)
        dump_environments_file(self.environment, self.environments)

    def _directory_select_button_fired(self):
        dlg = DirectoryDialog(default_path=paths.home)
        if dlg.open() == OK and dlg.path:
            self.environments.append(dlg.path)
            self.environment = dlg.path

    def traits_view(self):
        v = okcancel_view(
            CustomLabel('message', color='red', size=14, defined_when='message'),
            CustomLabel('user_help', defined_when='not message'),

            HGroup(UItem('user', width=225,
                         enabled_when='user_enabled',
                         editor=ComboboxEditor(name='users'))),
            Label('Select your work environment'),
            HGroup(UItem('environment', width=225,
                         editor=EnumEditor(name='environments')),
                   icon_button_editor('directory_select_button',
                                      'configure-2')),
            handler=LoginHandler(),
            title='Login')
        return v


# class SrcDestUsers(HasTraits):
#     users = List
#     src_user = Str
#     dest_user = Str
#     copy_all = Bool
#
#     def get_dest_user(self):
#         us = self.users
#         us.remove(self.src_user)
#         return us if self.copy_all else (self.dest_user,)
#
#     def traits_view(self):
#         v = View(Label('Copy "Source" preferences to "Destination"'),
#                  VGroup(UItem('src_user', width=225, editor=ComboboxEditor(name='users')),
#                         label='Source', show_border=True),
#                  VGroup(
#                      Item('copy_all', label='Copy All', tooltip='Copy "Source" to all destinations'),
#                      UItem('dest_user', editor=ComboboxEditor(name='users'),
#                            enabled_when='not copy_all',
#                            width=225),
#                      label='Destination', show_border=True),
#                  buttons=['OK', 'Cancel'],
#                  title='Login',
#                  kind='livemodal')
#         return v


def get_last_login(last_login):
    try:
        with open(paths.last_login_file, 'r') as rfile:
            obj = pickle.load(rfile)
            return obj[last_login]
    except BaseException:
        return True, True


def get_usernames():
    _, users, _ = load_user_file()
    return users


def get_user():
    """
        current: str, current user. if supplied omit from available list
    """
    login = Login()
    if to_bool(os.getenv('PYCHRON_USE_LOGIN', True)) or not (login.user and login.environment):
        while 1:
            info = login.edit_traits()
            if info.result:
                if login.user and login.environment:
                    return login.user, login.environment
            else:
                break
    else:
        return login.user, login.environment


# ============= EOF =============================================
