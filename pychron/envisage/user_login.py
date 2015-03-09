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

from pyface.message_dialog import information
from traits.api import HasTraits, List, Str, Bool
from traitsui.api import View, Item, HGroup, UItem, Label, Handler, VGroup
# ============= standard library imports ========================
import os
import pickle
# ============= local library imports  ==========================
from pychron.core.ui.combobox_editor import ComboboxEditor
# from pychron.paths import paths

enthought = os.path.join(os.path.expanduser('~'), '.enthought')
users_file = os.path.join(enthought, 'users')
login_file = os.path.join(enthought, 'login')


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
        with open(path, 'r') as fp:
            users, last_login = pickle.load(fp)

    return users, last_login, isfile


def dump_user_file(names, last_login_name):
    if names is None:
        names, _, _ = load_user_file()

    if not isinstance(names, list):
        names = [names, ]

    # for name in names:
    # if name not in users:
    #         users.append(name)
    with open(users_file, 'w') as fp:
        pickle.dump((names, last_login_name), fp)


class Login(HasTraits):
    users = List
    user = Str

    def dump(self):
        dump_user_file(self.users, self.user)

    def traits_view(self):
        v = View(Label('Select your username or enter a new one'),
                 HGroup(UItem('user', width=225, editor=ComboboxEditor(name='users'))),
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
        with open(os.path.join(enthought, 'last_login'), 'r') as fp:
            obj = pickle.load(fp)
            return obj[last_login]
    except BaseException:
        return True, True


def set_last_login(name, use_login, multi_user):
    try:
        with open(os.path.join(enthought, 'last_login'), 'r') as fp:
            obj = pickle.load(fp)
    except BaseException:
        obj = {}

    obj[name] = (use_login, multi_user)
    # print 'set last login', obj
    with open(os.path.join(enthought, 'last_login'), 'w') as fp:
        pickle.dump(obj, fp)

    dump_user_file(names=None, last_login_name=name)


def get_user(current=None):
    """
        current: str, current user. if supplied omit from available list
    """
    if os.path.isfile(login_file):
        with open(login_file, 'r') as fp:
            u = fp.read()
        os.remove(login_file)
        return u

    users, last_login, isfile = load_user_file()
    use_login, multi_user = get_last_login(last_login)
    if use_login:
        # check to see if the login file is set

        # read the existing user file
        if not isfile and multi_user:
            information(None, 'Auto login as root. Quit to populate the user list')
            dump_user_file(['root'], 'root')
            return 'root'

        if current:
            users = [u for u in users if u != current]
        login = Login(users=users)
        if users:
            login.user = last_login if last_login in users else users[0]

        while 1:
            info = login.edit_traits()
            if info.result:
                if login.user:
                    # add the manually entered user name to the users file
                    if not current and not multi_user:
                        if login.user not in users:
                            users.append(login.user)
                        dump_user_file(users, login.user)

                    return login.user
            else:
                break
    else:
        return 'root'


def get_src_dest_user(cuser):
    users, _, _ = load_user_file()
    login = SrcDestUsers(users=users)
    login.src_user = cuser
    s, d = None, None
    while 1:
        info = login.edit_traits()
        if info.result:
            dusers = login.get_dest_user()
            if login.src_user and dusers:
                s, d = login.src_user, dusers
                break
        else:
            break

    return s, d

# ============= EOF =============================================



