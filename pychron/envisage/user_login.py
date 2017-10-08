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

import os
import pickle

from pyface.constant import OK
from pyface.directory_dialog import DirectoryDialog
from traits.api import HasTraits, List, Str, Bool, Button
from traitsui.api import View, Item, HGroup, UItem, Label, Handler, VGroup, EnumEditor

from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths, users_file, environments_file, HOME


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
        with open(path, 'r') as rfile:
            users, last_login = pickle.load(rfile)

    # return users, last_login, isfile
    return last_login, users, isfile


def load_environments_file():
    path = environments_file
    envs = []
    last_env = ''
    if os.path.isfile(path):
        with open(path, 'r') as rfile:
            last_env, envs = pickle.load(rfile)
    return last_env, envs


def dump_environments_file(env, envs):
    path = environments_file
    with open(path, 'w') as wfile:
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

    with open(users_file, 'w') as wfile:
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
            self.message = 'Auto Login as "root". Quit Pychron to populate users from database'

    def dump(self):
        dump_user_file(self.users, self.user)
        dump_environments_file(self.environment, self.environments)

    def _directory_select_button_fired(self):
        dlg = DirectoryDialog(default_path=HOME)
        if dlg.open() == OK and dlg.path:
            self.environments.append(dlg.path)
            self.environment = dlg.path

    def traits_view(self):
        v = View(
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
            buttons=['OK', 'Cancel'],
            title='Login',
            kind='livemodal')
        return v


class SrcDestUsers(HasTraits):
    users = List
    src_user = Str
    dest_user = Str
    copy_all = Bool

    def get_dest_user(self):
        us = self.users
        us.remove(self.src_user)
        return us if self.copy_all else (self.dest_user,)

    def traits_view(self):
        v = View(Label('Copy "Source" preferences to "Destination"'),
                 VGroup(UItem('src_user', width=225, editor=ComboboxEditor(name='users')),
                        label='Source', show_border=True),
                 VGroup(
                     Item('copy_all', label='Copy All', tooltip='Copy "Source" to all destinations'),
                     UItem('dest_user', editor=ComboboxEditor(name='users'),
                           enabled_when='not copy_all',
                           width=225),
                     label='Destination', show_border=True),
                 buttons=['OK', 'Cancel'],
                 title='Login',
                 kind='livemodal')
        return v


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
    while 1:
        login = Login()
        info = login.edit_traits()
        if info.result:
            if login.user and login.environment:
                return login.user, login.environment
        else:
            break

            # login_file = paths.login_file
            # if os.path.isfile(login_file):
            #     with open(login_file, 'r') as rfile:
            #         u = rfile.read()
            #     os.remove(login_file)
            #     return u
            #
            # users, last_login, isfile = load_user_file()
            # use_login, multi_user = get_last_login(last_login)
            # if use_login:
            #     # check to see if the login file is set
            #
            #     # read the existing user file
            #     if not isfile and multi_user:
            #         information(None, 'Auto login as root. Quit to populate the user list')
            #         dump_user_file(['root'], 'root')
            #         return 'root'
            #
            #     if current:
            #         users = [u for u in users if u != current]
            #     login = Login(users=users)
            #     if users:
            #         login.user = last_login if last_login in users else users[0]
            #
            #     while 1:
            #         info = login.edit_traits()
            #         if info.result:
            #             if login.user:
            #                 # add the manually entered user name to the users file
            #                 if not current and not multi_user:
            #                     if login.user not in users:
            #                         users.append(login.user)
            #                     dump_user_file(users, login.user)
            #
            #                 return login.user
            #         else:
            #             break
            # else:
            #     return 'root'

# def get_src_dest_user(cuser):
#     users, _, _ = load_user_file()
#     login = SrcDestUsers(users=users)
#     login.src_user = cuser
#     s, d = None, None
#     while 1:
#         info = login.edit_traits()
#         if info.result:
#             dusers = login.get_dest_user()
#             if login.src_user and dusers:
#                 s, d = login.src_user, dusers
#                 break
#         else:
#             break
#
#     return s, d

# ============= EOF =============================================
